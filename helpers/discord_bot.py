"""Persistent Discord Gateway bot for the chat bridge.
Listens for messages in designated channels and routes them through Agent Zero's LLM."""

import asyncio
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
    path = _get_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


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
    """Discord bot that bridges messages to Agent Zero's LLM."""

    def __init__(self, bot_token: str):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.bot_token = bot_token

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

        # Show typing while processing
        async with message.channel.typing():
            try:
                response_text = await self._get_agent_response(channel_id, user_text, message)
            except Exception as e:
                logger.error(f"Agent error: {e}")
                response_text = f"Error processing message: {e}"

        # Send response, splitting if needed
        await self._send_response(message.channel, response_text, reference=message)

    async def _get_agent_response(self, channel_id: str, text: str, message: discord.Message) -> str:
        """Route the message through Agent Zero's agent loop."""
        try:
            from agent import AgentContext, AgentContextType, UserMessage
            from initialize import initialize_agent

            # Get or create a context for this channel
            context_id = get_context_id(channel_id)
            context = None

            if context_id:
                context = AgentContext.get(context_id)

            if context is None:
                # Create new context matching how A0's api_message.py does it
                config = initialize_agent()
                context = AgentContext(config=config, type=AgentContextType.USER)
                set_context_id(channel_id, context.id)
                logger.info(f"Created new context {context.id} for channel {channel_id}")

            # Build user message with Discord metadata
            author_name = message.author.display_name or message.author.name
            prefixed_text = f"[Discord - {author_name}]: {text}"

            # Handle image attachments — save to temp files (UserMessage expects file paths)
            attachment_paths = []
            for att in message.attachments:
                if att.content_type and att.content_type.startswith("image/"):
                    try:
                        import tempfile
                        img_bytes = await att.read()
                        suffix = Path(att.filename).suffix or ".png"
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                        tmp.write(img_bytes)
                        tmp.close()
                        attachment_paths.append(tmp.name)
                    except Exception:
                        pass

            user_msg = UserMessage(message=prefixed_text, attachments=attachment_paths)
            task = context.communicate(user_msg)
            result = await task.result()

            return result if isinstance(result, str) else str(result)

        except ImportError:
            # Fallback: use HTTP API if in-process imports aren't available
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
