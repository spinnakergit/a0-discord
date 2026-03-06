## discord_poll
Monitor Discord channels for new messages (alerts). Tracks last-seen message per channel so each poll only returns new content. Supports image extraction and analysis. Can set up automatic scheduled polling.

**Arguments:**
- **action** (string): `check`, `watch`, `unwatch`, `list`, or `setup_scheduler`
- **channel_id** (string): Channel to watch or check
- **guild_id** (string): Server ID (for watch)
- **label** (string): Friendly name for the channel (for watch)
- **owner_id** (string): Only alert on messages from this user ID (for watch)
- **interval** (string): Minutes between polls (for setup_scheduler, default: "15")
- **mode** (string, optional): `bot` or `user` — forces a specific auth mode. If omitted, tries bot first and falls back to user token on access errors.

**watch** — Start monitoring a channel:
~~~json
{"action": "watch", "channel_id": "CHANNEL_ID", "guild_id": "SERVER_ID", "label": "alerts", "owner_id": "USER_ID_OF_OWNER"}
~~~

**check** — Poll for new messages now:
~~~json
{"action": "check"}
~~~

Check a specific channel only:
~~~json
{"action": "check", "channel_id": "CHANNEL_ID"}
~~~

**setup_scheduler** — Auto-poll every N minutes:
~~~json
{"action": "setup_scheduler", "interval": "15"}
~~~

**list** — Show all watched channels:
~~~json
{"action": "list"}
~~~

**unwatch** — Stop monitoring a channel:
~~~json
{"action": "unwatch", "channel_id": "CHANNEL_ID"}
~~~

When images are found in alerts, they are automatically loaded into context for visual analysis.
