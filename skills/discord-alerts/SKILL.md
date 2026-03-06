---
name: "discord-alerts"
description: "Monitor Discord channels for new alerts and messages. Automatically polls at configurable intervals, extracts images for analysis, and saves alerts to memory."
version: "1.0.0"
author: "AgentZero Discord Plugin"
license: "MIT"
tags: ["discord", "alerts", "monitoring", "research"]
triggers:
  - "discord alerts"
  - "monitor discord"
  - "discord poll"
  - "watch discord channel"
  - "check discord alerts"
allowed_tools:
  - discord_poll
  - discord_read
  - discord_members
metadata:
  complexity: "intermediate"
  category: "monitoring"
---

# Discord Alerts Monitoring Skill

Monitor specific Discord channels for new messages, especially alerts with images.

## Setup Workflow

### Step 1: Identify the Channel and Owner
Get the channel ID and the server owner's user ID:
```json
{"tool": "discord_read", "args": {"action": "channels", "guild_id": "SERVER_ID"}}
```
```json
{"tool": "discord_members", "args": {"action": "list", "guild_id": "SERVER_ID"}}
```

### Step 2: Watch the Channel
Start monitoring, optionally filter to a specific user:
```json
{"tool": "discord_poll", "args": {"action": "watch", "channel_id": "CHANNEL_ID", "guild_id": "SERVER_ID", "label": "alerts", "owner_id": "OWNER_USER_ID"}}
```

### Step 3: Set Up Automatic Polling
Schedule checks every 15 minutes (configurable):
```json
{"tool": "discord_poll", "args": {"action": "setup_scheduler", "interval": "15"}}
```

### Step 4: Manual Check (anytime)
```json
{"tool": "discord_poll", "args": {"action": "check"}}
```

## How It Works
- Each poll only fetches **new messages** since the last check
- If `owner_id` is set, only that user's messages trigger alerts
- **Images** (charts, targets) are automatically downloaded and loaded into context
- The agent analyzes images for price targets, support/resistance levels, and patterns
- All alerts are saved to memory automatically
- Alert history is tracked in the plugin's data directory

## Tips
- Use `owner_id` to filter out noise — only get alerts from the channel owner
- Images are analyzed by the main LLM model (must support vision)
- Check `list` to see all watched channels and their last poll times
- Use `unwatch` to stop monitoring a channel
