---
name: "discord-communicate"
description: "Send messages and interact in Discord servers via bot account. Reply to conversations, react to messages, and participate in channels."
version: "1.0.0"
author: "AgentZero Discord Plugin"
license: "MIT"
tags: ["discord", "communication", "messaging"]
triggers:
  - "discord send"
  - "send discord message"
  - "reply on discord"
  - "post to discord"
allowed_tools:
  - discord_send
  - discord_read
  - discord_members
metadata:
  complexity: "beginner"
  category: "communication"
---

# Discord Communication Skill

Send messages and interact in Discord channels via the bot account.

## Important
- Messages are sent via the **bot account** only
- Always read recent conversation before responding

## Workflow

1. **Read context first**:
   `discord_read` with `action: messages`, `channel_id: ID`, `limit: 20`

2. **Send a message**:
   `discord_send` with `action: send`, `channel_id: ID`, `content: text`

3. **Reply to someone**:
   `discord_send` with `action: send`, `channel_id: ID`, `content: text`, `reply_to: MSG_ID`

4. **React to a message**:
   `discord_send` with `action: react`, `channel_id: ID`, `message_id: MSG_ID`, `emoji: thumbsup`

5. **Check who you're talking to**:
   `discord_members` with `action: info`, `guild_id: ID`, `user_id: UID`
