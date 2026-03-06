import time
from pathlib import Path
from helpers.tool import Tool, Response
from plugins.discord.helpers.discord_client import (
    DiscordClient, DiscordAPIError, format_messages, get_discord_config,
    get_modes_to_try,
)

SUMMARIZE_PROMPT = """You are summarizing a Discord conversation. Analyze the following messages and produce a structured summary.

## Instructions
- Identify the main topics discussed
- Note key decisions or conclusions reached
- Highlight important links, resources, or references shared
- List action items if any were mentioned
- Note the most active participants and their primary contributions
- Keep the summary concise but comprehensive

## Messages
{messages}

## Output Format
### Summary
[2-4 sentence overview]

### Key Topics
- [topic 1]: [brief description]
- [topic 2]: [brief description]

### Key Decisions / Conclusions
- [decision or conclusion, if any]

### Notable References
- [links, resources, or references mentioned]

### Action Items
- [action items, if any]

### Active Participants
- [username]: [primary contribution/role in discussion]
"""


class DiscordSummarize(Tool):
    """Summarize messages from a Discord channel or thread."""

    async def execute(self, **kwargs) -> Response:
        channel_id = self.args.get("channel_id", "")
        thread_id = self.args.get("thread_id", "")
        guild_id = self.args.get("guild_id", "")
        limit = int(self.args.get("limit", "100"))
        save_to_memory = self.args.get("save_to_memory", "true").lower() == "true"

        target_id = thread_id or channel_id
        if not target_id:
            return Response(message="Error: channel_id or thread_id is required.", break_loop=False)

        config = get_discord_config(self.agent)
        explicit_mode = self.args.get("mode", "")
        modes = get_modes_to_try(config, explicit_mode or None)

        last_error = None
        for mode in modes:
            try:
                client = DiscordClient.from_config(agent=self.agent, mode=mode)

                channel_info = await client.get_channel(target_id)
                channel_name = channel_info.get("name", target_id)

                self.set_progress("Fetching messages...")
                messages = await client.get_all_channel_messages(channel_id=target_id, limit=limit)
                await client.close()

                if not messages:
                    return Response(message=f"No messages found in #{channel_name}.", break_loop=False)

                self.set_progress("Generating summary...")
                formatted = format_messages(messages)
                prompt = SUMMARIZE_PROMPT.format(messages=formatted)

                summary = await self.agent.call_utility_model(
                    system="You are a precise summarizer of Discord conversations.",
                    message=prompt,
                )

                if save_to_memory:
                    self.set_progress("Saving to memory...")
                    timestamp = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
                    guild_label = f" (guild: {guild_id})" if guild_id else ""
                    memory_text = (
                        f"Discord Summary - #{channel_name}{guild_label} "
                        f"[{timestamp}, {len(messages)} messages]\n\n{summary}"
                    )
                    await _save_to_memory(self.agent, memory_text)

                header = f"Summary of #{channel_name} ({len(messages)} messages):"
                suffix = "\n\n[Saved to memory]" if save_to_memory else ""
                return Response(message=f"{header}\n\n{summary}{suffix}", break_loop=False)

            except DiscordAPIError as e:
                try:
                    await client.close()
                except Exception:
                    pass
                last_error = e
                if e.status == 403 and mode != modes[-1]:
                    continue
                return Response(message=f"Discord API error: {e}", break_loop=False)
            except Exception as e:
                return Response(message=f"Error summarizing: {e}", break_loop=False)

        return Response(message=f"Discord API error: {last_error}", break_loop=False)


async def _save_to_memory(agent, text: str):
    try:
        from plugins.memory.helpers.memory import Memory
        db = await Memory.get(agent)
        metadata = {"area": "main", "source": "discord_summarize"}
        await db.insert_text(text, metadata)
    except Exception:
        fallback_dir = Path("/a0/memory/discord_summaries") if Path("/a0").exists() else Path("/git/agent-zero/memory/discord_summaries")
        fallback_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        with open(fallback_dir / f"summary_{ts}.md", "w") as f:
            f.write(text)
