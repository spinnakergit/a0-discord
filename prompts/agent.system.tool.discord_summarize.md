## discord_summarize
Summarize a Discord channel or thread conversation. Produces structured summary with key topics, decisions, action items, and participants. Auto-saves to memory.

**Arguments:**
- **channel_id** (string): Channel to summarize
- **thread_id** (string): Thread to summarize (instead of channel)
- **guild_id** (string): Server ID for labeling
- **limit** (number): Messages to analyze (default: 100)
- **save_to_memory** (string): "true" or "false" (default: "true")
- **mode** (string, optional): `bot` or `user` — forces a specific auth mode. If omitted, tries bot first and falls back to user token on access errors.

~~~json
{"channel_id": "987654321", "guild_id": "123456789"}
~~~
~~~json
{"thread_id": "111222333", "limit": "200"}
~~~
