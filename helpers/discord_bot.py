"""Persistent Discord Gateway bot for the chat bridge.
Listens for messages in designated channels and routes them through Agent Zero's LLM."""

import asyncio
import collections
import json
import logging
import time
from pathlib import Path
from typing import Optional

import discord

logger = logging.getLogger("discord_chat_bridge")

# Singleton bot instance
_bot_instance: Optional["ChatBridgeBot"] = None
_bot_task: Optional[asyncio.Task] = None

CHAT_STATE_FILE = "chat_bridge_state.json"


def _get_state_path() -> Path:
    candidates = [
        Path(__file__).parent.parent / "data" / CHAT_STATE_FILE,
        Path("/a0/usr/plugins/discord/data") / CHAT_STATE_FILE,
        Path("/a0/plugins/discord/data") / CHAT_STATE_FILE,
        Path("/git/agent-zero/usr/plugins/discord/data") / CHAT_STATE_FILE,
    ]
    for p in candidates:
        if p.exists():
            return p
    path = candidates[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_chat_state() -> dict:
    path = _get_state_path()
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {"channels": {}, "contexts": {}}


def save_chat_state(state: dict):
    from plugins.discord.helpers.sanitize import secure_write_json
    secure_write_json(_get_state_path(), state)


def add_chat_channel(channel_id: str, guild_id: str = "", label: str = ""):
    state = load_chat_state()
    state.setdefault("channels", {})[channel_id] = {
        "guild_id": guild_id,
        "label": label or channel_id,
        "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save_chat_state(state)


def remove_chat_channel(channel_id: str):
    state = load_chat_state()
    state.get("channels", {}).pop(channel_id, None)
    state.get("contexts", {}).pop(channel_id, None)
    save_chat_state(state)


def get_chat_channels() -> dict:
    return load_chat_state().get("channels", {})


def get_context_id(channel_id: str) -> Optional[str]:
    return load_chat_state().get("contexts", {}).get(channel_id)


def set_context_id(channel_id: str, context_id: str):
    state = load_chat_state()
    state.setdefault("contexts", {})[channel_id] = context_id
    save_chat_state(state)


class ChatBridgeBot(discord.Client):
    """Discord bot that bridges messages to Agent Zero's LLM.

    SECURITY: Uses direct LLM calls (call_utility_model) instead of the full
    agent loop. This means the LLM has NO access to tools, code execution,
    file operations, or any system resources. This is intentional — chat bridge
    users are untrusted external Discord users.
    """

    MAX_CHAT_MESSAGE_LENGTH = 4000
    MAX_HISTORY_MESSAGES = 20
    # Rate limit: max messages per user within the window
    RATE_LIMIT_MAX = 10
    RATE_LIMIT_WINDOW = 60  # seconds

    CHAT_SYSTEM_PROMPT = (
        "You are a friendly, helpful AI assistant chatting with users on Discord.\n\n"
        "IMPORTANT CONSTRAINTS:\n"
        "- You are a conversational chat bot ONLY. You have NO access to tools, files, "
        "commands, terminals, or any system resources.\n"
        "- If users ask you to run commands, access files, list directories, execute code, "
        "or perform any system operations, explain that you don't have those capabilities.\n"
        "- NEVER fabricate or make up file listings, directory contents, command outputs, "
        "or system information. You genuinely do not have access to any of these.\n"
        "- Be helpful, friendly, and conversational within these constraints.\n"
        "- You can help with general knowledge, answer questions, have discussions, "
        "write text, brainstorm ideas, and more — just not anything involving system access.\n"
        "- Each message shows the Discord username prefix. Respond naturally to the "
        "conversation.\n"
    )

    def __init__(self, bot_token: str):
        if not bot_token or not bot_token.strip():
            raise ValueError("Bot token must be provided to ChatBridgeBot.")
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.bot_token = bot_token
        # Per-user rate limiting: user_id -> deque of timestamps
        self._rate_limits: dict[str, collections.deque] = {}
        # Per-channel conversation history (in-memory, lost on restart)
        self._conversations: dict[str, list[dict]] = {}

    async def on_ready(self):
        logger.info(f"Chat bridge connected as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message):
        # Ignore own messages and other bots
        if message.author.bot:
            return

        channel_id = str(message.channel.id)
        chat_channels = get_chat_channels()

        # Only respond in designated chat channels
        if channel_id not in chat_channels:
            return

        user_text = message.content
        if not user_text.strip():
            return

        # Enforce content length limit before any processing
        if len(user_text) > self.MAX_CHAT_MESSAGE_LENGTH:
            await message.channel.send(
                f"Message too long ({len(user_text)} chars). "
                f"Max: {self.MAX_CHAT_MESSAGE_LENGTH}."
            )
            return

        # Per-user rate limiting
        user_key = str(message.author.id)
        now = time.monotonic()
        if user_key not in self._rate_limits:
            self._rate_limits[user_key] = collections.deque()
        timestamps = self._rate_limits[user_key]
        # Purge old entries outside the window
        while timestamps and now - timestamps[0] > self.RATE_LIMIT_WINDOW:
            timestamps.popleft()
        if len(timestamps) >= self.RATE_LIMIT_MAX:
            await message.channel.send(
                f"Rate limit: max {self.RATE_LIMIT_MAX} messages per {self.RATE_LIMIT_WINDOW}s. Please wait."
            )
            return
        timestamps.append(now)

        # Show typing while processing
        async with message.channel.typing():
            try:
                response_text = await self._get_agent_response(channel_id, user_text, message)
            except Exception as e:
                logger.error(f"Agent error: {type(e).__name__}")
                response_text = "An error occurred while processing your message."

        # Send response, splitting if needed
        await self._send_response(message.channel, response_text, reference=message)

    async def _get_agent_response(self, channel_id: str, text: str, message: discord.Message) -> str:
        """Get LLM response via direct model call (no agent loop, no tools).

        SECURITY: This intentionally bypasses the full agent loop. The LLM is
        called directly via call_utility_model(), which provides NO tool access.
        This prevents privilege escalation from untrusted Discord users.
        """
        try:
            from agent import AgentContext, AgentContextType
            from initialize import initialize_agent

            # Get or create a context (only for model access, NOT for tool execution)
            context_id = get_context_id(channel_id)
            context = None

            if context_id:
                context = AgentContext.get(context_id)

            if context is None:
                config = initialize_agent()
                context = AgentContext(config=config, type=AgentContextType.USER)
                set_context_id(channel_id, context.id)
                logger.info(f"Created new context {context.id} for channel {channel_id}")

            agent = context.agent0

            # Sanitize external content
            from plugins.discord.helpers.sanitize import sanitize_content, sanitize_username
            author_name = sanitize_username(
                message.author.display_name or message.author.name
            )
            safe_text = sanitize_content(text)

            # Maintain per-channel conversation history
            if channel_id not in self._conversations:
                self._conversations[channel_id] = []
            history = self._conversations[channel_id]
            history.append({"role": "user", "name": author_name, "content": safe_text})

            # Trim to max history length
            if len(history) > self.MAX_HISTORY_MESSAGES:
                self._conversations[channel_id] = history[-self.MAX_HISTORY_MESSAGES:]
                history = self._conversations[channel_id]

            # Format conversation history for the model
            formatted = []
            for msg in history:
                if msg["role"] == "user":
                    formatted.append(f"{msg['name']}: {msg['content']}")
                else:
                    formatted.append(f"Assistant: {msg['content']}")
            conversation_text = "\n".join(formatted)

            # Direct LLM call — NO tools, NO agent loop, NO code execution
            response = await agent.call_utility_model(
                system=self.CHAT_SYSTEM_PROMPT,
                message=conversation_text,
            )

            # Store response in history
            history.append({"role": "assistant", "content": response})

            return response if isinstance(response, str) else str(response)

        except ImportError:
            # Fallback: use HTTP API if in-process imports aren't available
            # WARNING: HTTP fallback routes through the full agent loop and is
            # less secure. It should only be used when A0 imports are unavailable.
            return await self._get_agent_response_http(channel_id, text)

    async def _get_agent_response_http(self, channel_id: str, text: str) -> str:
        """Fallback: route through Agent Zero's HTTP API."""
        import aiohttp
        from plugins.discord.helpers.discord_client import get_discord_config

        config = get_discord_config()
        api_port = config.get("chat_bridge", {}).get("api_port", 80)
        api_key = config.get("chat_bridge", {}).get("api_key", "")

        context_id = get_context_id(channel_id) or ""

        async with aiohttp.ClientSession() as session:
            payload = {
                "message": text,
                "context_id": context_id,
            }
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["X-API-KEY"] = api_key

            async with session.post(
                f"http://localhost:{api_port}/api/api_message",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    return f"Agent API error ({resp.status}): {body}"
                data = await resp.json()

                # Store context ID for conversation continuity
                if data.get("context_id"):
                    set_context_id(channel_id, data["context_id"])

                return data.get("response", "No response from agent.")

    async def _send_response(self, channel: discord.TextChannel, text: str, reference=None):
        """Send a response to Discord, splitting long messages."""
        if not text:
            text = "(No response)"

        chunks = _split_message(text)
        for i, chunk in enumerate(chunks):
            ref = reference if i == 0 else None
            await channel.send(chunk, reference=ref)

    async def start_bot(self):
        """Start the bot (non-blocking within an existing event loop)."""
        await self.start(self.bot_token)

    async def wait_until_ready_timeout(self, timeout: float = 30.0):
        """Wait for the bot to be ready, with timeout."""
        try:
            await asyncio.wait_for(self.wait_until_ready(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError("Bot failed to connect within timeout")


def _split_message(content: str, max_length: int = 2000) -> list[str]:
    if len(content) <= max_length:
        return [content]
    chunks = []
    while content:
        if len(content) <= max_length:
            chunks.append(content)
            break
        split_at = content.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = content.rfind(" ", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(content[:split_at])
        content = content[split_at:].lstrip("\n")
    return chunks


async def start_chat_bridge(bot_token: str) -> ChatBridgeBot:
    """Start the chat bridge bot as a background task."""
    global _bot_instance, _bot_task

    if not bot_token or not bot_token.strip():
        raise ValueError("Cannot start chat bridge: bot token is empty or not configured.")

    if _bot_instance and not _bot_instance.is_closed():
        return _bot_instance

    bot = ChatBridgeBot(bot_token)
    _bot_instance = bot
    _bot_task = asyncio.create_task(bot.start_bot())

    await bot.wait_until_ready_timeout(30)
    return bot


async def stop_chat_bridge():
    """Stop the chat bridge bot."""
    global _bot_instance, _bot_task

    if _bot_instance and not _bot_instance.is_closed():
        await _bot_instance.close()

    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except (asyncio.CancelledError, Exception):
            pass

    _bot_instance = None
    _bot_task = None


def get_bot_status() -> dict:
    """Get current bot status."""
    if _bot_instance is None:
        return {"running": False, "status": "stopped"}
    if _bot_instance.is_closed():
        return {"running": False, "status": "closed"}
    if _bot_instance.is_ready():
        user = _bot_instance.user
        return {
            "running": True,
            "status": "connected",
            "user": str(user),
            "user_id": str(user.id) if user else None,
            "guilds": len(_bot_instance.guilds),
        }
    return {"running": True, "status": "connecting"}
