from helpers.tool import Tool, Response
from plugins.discord.helpers.discord_client import (
    DiscordClient, DiscordAPIError, get_discord_config,
)


class DiscordSend(Tool):
    """Send a message or reaction to a Discord channel via bot account."""

    async def execute(self, **kwargs) -> Response:
        channel_id = self.args.get("channel_id", "")
        content = self.args.get("content", "")
        reply_to = self.args.get("reply_to", "")
        action = self.args.get("action", "send")

        if not channel_id:
            return Response(message="Error: channel_id is required.", break_loop=False)

        config = get_discord_config(self.agent)
        if not config.get("bot", {}).get("token"):
            return Response(
                message="Error: Bot token not configured. Sending requires a bot account.",
                break_loop=False,
            )

        try:
            client = DiscordClient.from_config(agent=self.agent, mode="bot")

            if action == "send":
                if not content:
                    return Response(message="Error: content is required for sending.", break_loop=False)

                chunks = _split_message(content)
                sent_ids = []
                for i, chunk in enumerate(chunks):
                    ref = reply_to if i == 0 and reply_to else None
                    result = await client.send_message(channel_id=channel_id, content=chunk, reply_to=ref)
                    sent_ids.append(result["id"])

                await client.close()
                if len(sent_ids) == 1:
                    return Response(message=f"Message sent (ID: {sent_ids[0]}).", break_loop=False)
                return Response(message=f"Message sent in {len(sent_ids)} parts (IDs: {', '.join(sent_ids)}).", break_loop=False)

            elif action == "react":
                emoji = self.args.get("emoji", "")
                message_id = self.args.get("message_id", "")
                if not emoji or not message_id:
                    return Response(message="Error: emoji and message_id required for reactions.", break_loop=False)
                await client.add_reaction(channel_id, message_id, emoji)
                await client.close()
                return Response(message=f"Reaction {emoji} added to message {message_id}.", break_loop=False)

            else:
                return Response(message=f"Unknown action '{action}'. Use 'send' or 'react'.", break_loop=False)

        except PermissionError as e:
            return Response(message=str(e), break_loop=False)
        except DiscordAPIError as e:
            return Response(message=f"Discord API error: {e}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error sending to Discord: {e}", break_loop=False)


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
