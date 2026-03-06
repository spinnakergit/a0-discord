---
name: "discord-chat"
description: "Use Discord as a chat interface to Agent Zero's LLM. Set up a persistent bot that listens in designated channels and routes messages through the agent."
version: "1.0.0"
author: "AgentZero Discord Plugin"
license: "MIT"
tags: ["discord", "chat", "bridge", "llm"]
triggers:
  - "discord chat bridge"
  - "chat through discord"
  - "discord llm chat"
  - "talk to agent on discord"
allowed_tools:
  - discord_chat
  - discord_read
metadata:
  complexity: "intermediate"
  category: "communication"
---

# Discord Chat Bridge Skill

Set up Discord as a chat frontend to Agent Zero's LLM.

## Setup Workflow

### Step 1: Find the Channel
List available channels to identify where to set up the chat:
```json
{"tool": "discord_read", "args": {"action": "channels", "guild_id": "SERVER_ID"}}
```

### Step 2: Add the Channel
Designate the channel for LLM chat:
```json
{"tool": "discord_chat", "args": {"action": "add_channel", "channel_id": "CHANNEL_ID", "guild_id": "SERVER_ID", "label": "llm-chat"}}
```

### Step 3: Start the Bot
Launch the chat bridge:
```json
{"tool": "discord_chat", "args": {"action": "start"}}
```

### Step 4: Verify
Check that the bot is connected:
```json
{"tool": "discord_chat", "args": {"action": "status"}}
```

## How It Works
- The bot connects via Discord Gateway (WebSocket) for real-time message delivery
- Each designated channel gets its own conversation context
- Messages are prefixed with the sender's Discord display name
- The bot shows a typing indicator while the LLM processes the response
- Long responses are automatically split into 2000-char chunks
- Image attachments are forwarded to the LLM for visual analysis
- Conversation history is maintained per channel across messages

## Tips
- Create a dedicated `#llm-chat` channel to keep things organized
- The bot only responds in channels you explicitly add — it won't interfere with other channels
- Use `stop` and `start` to restart the bot if issues arise
- Enable `auto_start` in config to launch the bot automatically on agent startup
