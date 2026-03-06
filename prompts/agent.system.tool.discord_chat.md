## discord_chat
Manage the Discord chat bridge — a persistent bot that routes Discord messages through Agent Zero's LLM. Users can chat with the agent directly from Discord channels.

**Arguments:**
- **action** (string): `start`, `stop`, `add_channel`, `remove_channel`, `list`, or `status`
- **channel_id** (string): Discord channel ID (for add_channel / remove_channel)
- **guild_id** (string): Server ID (for add_channel)
- **label** (string): Friendly name for the channel (for add_channel)

**start** — Launch the chat bridge bot:
~~~json
{"action": "start"}
~~~

**stop** — Shut down the chat bridge bot:
~~~json
{"action": "stop"}
~~~

**add_channel** — Designate a Discord channel for LLM chat:
~~~json
{"action": "add_channel", "channel_id": "1234567890123456789", "guild_id": "9876543210123456789", "label": "llm-chat"}
~~~

**remove_channel** — Stop listening in a channel:
~~~json
{"action": "remove_channel", "channel_id": "1234567890123456789"}
~~~

**list** — Show all chat bridge channels:
~~~json
{"action": "list"}
~~~

**status** — Check if the bot is running:
~~~json
{"action": "status"}
~~~

The bot maintains separate conversation contexts per channel. Messages from Discord users are prefixed with their display name. The bot shows a typing indicator while processing. Image attachments are forwarded to the LLM for analysis.
