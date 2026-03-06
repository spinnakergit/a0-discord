## discord_insights
Extract high-level ideas, concepts, and research-worthy knowledge from Discord discussions. Deeper than summarization — identifies themes, patterns, contested points, and research directions. Auto-saves to memory.

**Arguments:**
- **channel_id** (string): Channel to analyze
- **thread_id** (string): Thread to analyze (instead of channel)
- **guild_id** (string): Server ID for labeling
- **limit** (number): Messages to analyze (default: 200)
- **focus** (string): Optional topic to focus analysis on
- **save_to_memory** (string): "true" or "false" (default: "true")
- **mode** (string, optional): `bot` or `user` — forces a specific auth mode. If omitted, tries bot first and falls back to user token on access errors.

~~~json
{"channel_id": "987654321", "guild_id": "123456789"}
~~~
~~~json
{"channel_id": "987654321", "focus": "tokenomics and governance", "limit": "300"}
~~~
~~~json
{"thread_id": "111222333", "focus": "technical architecture"}
~~~
