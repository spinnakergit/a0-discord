---
name: "discord-research"
description: "Research and analyze Discord server conversations. Summarize channels, extract insights, and track community discussions for knowledge gathering."
version: "1.0.0"
author: "AgentZero Discord Plugin"
license: "MIT"
tags: ["discord", "research", "summarization", "knowledge"]
triggers:
  - "discord research"
  - "summarize discord"
  - "discord insights"
  - "analyze discord"
  - "discord channel summary"
allowed_tools:
  - discord_read
  - discord_summarize
  - discord_insights
  - discord_members
metadata:
  complexity: "intermediate"
  category: "research"
---

# Discord Research Skill

Use Discord tools to gather knowledge from Discord servers.

## Workflow

1. **List channels** to understand server structure:
   `discord_read` with `action: channels`, `guild_id: SERVER_ID`

2. **Check active threads**:
   `discord_read` with `action: threads`, `guild_id: SERVER_ID`

3. **Read messages** from a channel or thread:
   `discord_read` with `action: messages`, `channel_id: ID`, `limit: 100`

4. **Summarize** for a structured overview:
   `discord_summarize` with `channel_id: ID`, `guild_id: SERVER_ID`

5. **Extract insights** for deep analysis:
   `discord_insights` with `channel_id: ID`, `focus: OPTIONAL_TOPIC`

6. **Track people** — sync members and add notes:
   `discord_members` with `action: sync`, `guild_id: SERVER_ID`

## Tips
- Start by listing channels to understand the server
- Use `discord_summarize` for quick overviews, `discord_insights` for deep analysis
- Both auto-save to memory by default
- Use `focus` in insights to narrow the analysis
- Thread IDs work anywhere channel IDs do
