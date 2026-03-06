## discord_send
Send a message or reaction to a Discord channel. Requires bot account.

**Arguments:**
- **action** (string): `send` or `react`
- **channel_id** (string): Target channel ID
- **content** (string): Message text (for `send`)
- **reply_to** (string): Message ID to reply to (for `send`)
- **message_id** (string): Target message (for `react`)
- **emoji** (string): Emoji to react with (for `react`)

~~~json
{"action": "send", "channel_id": "987654321", "content": "Hello!"}
~~~
~~~json
{"action": "send", "channel_id": "987654321", "content": "Great point.", "reply_to": "444555666"}
~~~
~~~json
{"action": "react", "channel_id": "987654321", "message_id": "444555666", "emoji": "👍"}
~~~
