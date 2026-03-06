## discord_read
Read messages, list channels, or list threads from a Discord server.

**Arguments:**
- **action** (string): `messages`, `channels`, or `threads`
- **channel_id** (string): Channel ID (required for `messages`)
- **thread_id** (string): Thread ID (use instead of channel_id for threads)
- **guild_id** (string): Server ID (required for `channels` and `threads`)
- **limit** (number): Messages to fetch (default: 50, max: 200)
- **after** (string): Only fetch messages after this message ID
- **mode** (string, optional): `bot` or `user` — forces a specific auth mode. If omitted, tries bot first and falls back to user token on access errors.

~~~json
{"action": "channels", "guild_id": "123456789"}
~~~
~~~json
{"action": "messages", "channel_id": "987654321", "limit": "100"}
~~~
~~~json
{"action": "threads", "guild_id": "123456789"}
~~~
