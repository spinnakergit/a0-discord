---
name: "discord-persona-mapping"
description: "Build and maintain a knowledge base of Discord server members. Track roles, contributions, expertise, and relationships."
version: "1.0.0"
author: "AgentZero Discord Plugin"
license: "MIT"
tags: ["discord", "personas", "community", "knowledge"]
triggers:
  - "discord personas"
  - "discord members"
  - "who is on discord"
  - "map discord users"
allowed_tools:
  - discord_members
  - discord_read
  - discord_insights
metadata:
  complexity: "intermediate"
  category: "research"
---

# Discord Persona Mapping Skill

Build a comprehensive understanding of who's who in a Discord server.

## Workflow

1. **Sync members** into persona registry:
   `discord_members` with `action: sync`, `guild_id: SERVER_ID`

2. **Read channels** to identify active contributors:
   `discord_read` with `action: messages`, `channel_id: ID`, `limit: 200`

3. **Get user details**:
   `discord_members` with `action: info`, `guild_id: ID`, `user_id: UID`

4. **Add contextual notes**:
   `discord_members` with `action: note`, `user_id: UID`, `notes: "Core dev, Solidity expert"`

5. **Search the registry**:
   `discord_members` with `action: search`, `query: developer`

6. **Review all tracked users**:
   `discord_members` with `action: registry`, `guild_id: SERVER_ID`

## Tips
- Sync first, then enrich with notes over time
- Notes accumulate across sessions
- The registry persists between conversations
