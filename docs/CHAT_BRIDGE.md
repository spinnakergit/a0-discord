# Chat Bridge Configuration Guide

Use Discord as a real-time chat frontend to Agent Zero's LLM. Users message in a designated Discord channel and receive LLM-generated responses.

---

## How the Chat Bridge Works

```
Discord User sends message in #llm-chat
    |
    v
Discord Gateway (WebSocket) ---> ChatBridgeBot (discord.py)
    |
    v
on_message() handler checks:
  1. Is this channel in our designated list? (skip if not)
  2. Is the author a bot? (skip bots)
  3. Is the message empty? (skip empty)
    |
    v
Show typing indicator in Discord
    |
    v
Create/retrieve AgentContext for this channel (via initialize_agent() + AgentContext())
Route through AgentContext.communicate(UserMessage(...))
  - Message prefixed: "[Discord - DisplayName]: message text"
  - Image attachments: saved to temp files and forwarded as file paths
  - Each channel has its own conversation context (independent history)
    |
    v
LLM generates response
    |
    v
Send response back to Discord channel
  - Replies to the original message
  - Splits into 2000-char chunks if needed
```

---

## Configuration

The chat bridge has two configuration layers:

### 1. Plugin Config (persistent settings)

Stored in `config.json` (via WebUI or API). Controls whether the bot auto-starts.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `chat_bridge.auto_start` | bool | `false` | Start the bot automatically when Agent Zero initializes |

**Set via WebUI:**
Go to Discord plugin settings page > Chat Bridge section > check "Auto-start chat bridge on agent startup" > Save.

**Set via config file** (`usr/plugins/discord/config.json`):
```json
{
  "bot": {
    "token": "YOUR_BOT_TOKEN"
  },
  "chat_bridge": {
    "auto_start": true
  }
}
```

**Set via API:**
```bash
curl -X POST http://localhost/api/plugins/discord/discord_config_api \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "set",
    "config": {
      "bot": {"token": "YOUR_BOT_TOKEN"},
      "chat_bridge": {"auto_start": true}
    }
  }'
```

### 2. Channel Assignments (runtime state)

Channels are NOT configured in `config.json`. They are managed at runtime through the `discord_chat` tool and stored in `data/chat_bridge_state.json`.

This separation exists because channels are managed interactively — you add and remove them by talking to the agent, not by editing config files.

**Add a channel (tell Agent Zero):**
> Add Discord channel YOUR_CHANNEL_ID to the chat bridge, label it "llm-chat", server YOUR_SERVER_ID

Replace `YOUR_CHANNEL_ID` and `YOUR_SERVER_ID` with your actual Discord IDs (see [Getting Discord IDs](#step-1-identify-your-channel) below).

**Or call the tool directly:**
```json
{
  "tool": "discord_chat",
  "args": {
    "action": "add_channel",
    "channel_id": "YOUR_CHANNEL_ID",
    "guild_id": "YOUR_SERVER_ID",
    "label": "llm-chat"
  }
}
```

**The state file** (`data/chat_bridge_state.json`) looks like:
```json
{
  "channels": {
    "YOUR_CHANNEL_ID": {
      "guild_id": "YOUR_SERVER_ID",
      "label": "llm-chat",
      "added_at": "2026-03-05T14:30:00Z"
    }
  },
  "contexts": {
    "YOUR_CHANNEL_ID": "a1b2c3d4-uuid-of-agent-context"
  }
}
```

You can also edit this file directly if needed, but the tool is the recommended approach.

---

## Prerequisites

### 1. Bot Token
A Discord bot token is required. The chat bridge uses the Gateway (WebSocket) connection via `discord.py`, which only works with bot tokens (not user tokens).

Set it via any of:
- Config file: `config.json` -> `bot.token` (most reliable)
- Environment variable: `DISCORD_BOT_TOKEN=...`
- WebUI: Discord plugin settings > Bot Account > Bot Token

### 2. Gateway Intents
In the [Discord Developer Portal](https://discord.com/developers/applications), your bot application must have these Privileged Gateway Intents enabled:

| Intent | Required | Why |
|--------|----------|-----|
| **Message Content** | Yes | Read message text from users |
| **Server Members** | Recommended | Resolve display names |

Without Message Content intent, the bot will connect but `message.content` will be empty for all messages.

### 3. Bot Permissions
The bot needs these permissions in the channel(s) you designate:

| Permission | Why |
|------------|-----|
| View Channel | See the channel |
| Read Message History | Access messages |
| Send Messages | Reply with LLM responses |

### 4. Bot Invited to Server
The bot must be a member of the server containing the channel. Use the OAuth2 URL Generator in the Developer Portal to create an invite link.

---

## Step-by-Step Setup

### Quick Setup (3 commands)

```
You: List channels in Discord server YOUR_SERVER_ID
Agent: [shows channels with IDs]

You: Add channel YOUR_CHANNEL_ID to the Discord chat bridge, call it "llm-chat"
Agent: Channel YOUR_CHANNEL_ID added to chat bridge (#llm-chat).

You: Start the Discord chat bridge
Agent: Chat bridge started as MyBot#1234. Listening in 1 channel(s).
```

Done. Go to `#llm-chat` in Discord and start chatting.

### Detailed Setup

#### Step 1: Identify Your Channel

If you don't know the channel ID:

**Option A — Ask Agent Zero:**
> Show me channels in Discord server YOUR_SERVER_ID

**Option B — Discord Developer Mode:**
Enable Developer Mode (User Settings > Advanced > Developer Mode), then right-click the channel > Copy Channel ID.

**Option C — From URL:**
```
https://discord.com/channels/SERVER_ID/CHANNEL_ID
```

#### Step 2: Register the Channel

Tell Agent Zero:
> Add Discord channel CHANNEL_ID to the chat bridge, label it "llm-chat"

The label is optional but makes status output more readable.

You can register multiple channels:
> Add channel CHANNEL_ID_1 to the chat bridge as "general-ai"
> Add channel CHANNEL_ID_2 to the chat bridge as "dev-help"

Each channel gets its own independent conversation context.

#### Step 3: Start the Bot

> Start the Discord chat bridge

The bot connects via WebSocket and begins listening. You'll see:
```
Chat bridge started as MyBot#1234.
Listening in 2 channel(s).
```

#### Step 4: Verify

> Show Discord chat bridge status

```
Chat bridge is connected as MyBot#1234
  User ID: <bot_user_id>
  Guilds: 1
  Chat channels: 2
    - #general-ai (ID: <channel_id_1>)
    - #dev-help (ID: <channel_id_2>)
```

#### Step 5: Enable Auto-Start (Optional)

So the bridge starts automatically after an Agent Zero restart:

> Enable auto-start for the Discord chat bridge

Or set it in config:
```json
{
  "chat_bridge": {
    "auto_start": true
  }
}
```

Auto-start only activates when all three conditions are met:
1. A bot token is configured
2. `chat_bridge.auto_start` is `true`
3. At least one channel is registered

---

## Managing the Chat Bridge

### Check Status
```
You: What's the Discord chat bridge status?
```

### Stop the Bot
```
You: Stop the Discord chat bridge
```

### Add a Channel
```
You: Add channel YOUR_CHANNEL_ID to the chat bridge as "research"
```

### Remove a Channel
```
You: Remove channel YOUR_CHANNEL_ID from the chat bridge
```

### List Channels
```
You: List Discord chat bridge channels
```

### Reset a Conversation
To start fresh in a channel (clear conversation history), remove its context from `data/chat_bridge_state.json`:

```json
{
  "channels": { ... },
  "contexts": {
    "YOUR_CHANNEL_ID": "DELETE_THIS_ENTRY"
  }
}
```

The next message in that channel will create a new conversation context.

---

## Behavior Details

### Message Routing
- Only messages in explicitly registered channels are processed
- Bot messages are ignored (prevents loops)
- Empty messages are ignored
- Messages are prefixed with `[Discord - DisplayName]:` for LLM context

### Image Handling
When a user sends an image attachment in a chat bridge channel:
1. The image is downloaded from Discord's CDN
2. Saved to a temporary file on disk
3. The file path is passed to `UserMessage(attachments=[...])` for the LLM
4. The LLM can analyze/describe the image if it supports vision

### Response Splitting
Discord has a 2000-character message limit. Long LLM responses are automatically split:
1. Try to split at the last newline before 2000 chars
2. If no newline, split at the last space
3. If no space, hard-split at 2000 chars
4. The first chunk replies to the original message; subsequent chunks are standalone

### Conversation Contexts
- Each channel has its own Agent Zero `AgentContext`
- Context IDs persist in `data/chat_bridge_state.json`
- If Agent Zero's in-memory context expires (e.g., after restart), a new one is created automatically
- Multiple users in the same channel share the same context (the LLM sees all messages)

### Typing Indicator
The bot shows Discord's typing indicator (`... is typing`) while the LLM processes the response. This gives users visual feedback that the bot received their message.

### Concurrent Messages
If multiple messages arrive while one is being processed, they queue up and are handled sequentially (one at a time per channel, due to the typing indicator lock).

---

## Architecture

### Files

| File | Purpose |
|------|---------|
| `helpers/discord_bot.py` | `ChatBridgeBot` class (discord.py Client), lifecycle management, channel state persistence |
| `tools/discord_chat.py` | `DiscordChat` Tool — management actions (start/stop/add/remove/list/status) |
| `extensions/python/agent_init/_10_discord_chat.py` | Auto-start extension hook |
| `data/chat_bridge_state.json` | Persisted channel assignments and context IDs |

### Key Classes and Functions

**`ChatBridgeBot(discord.Client)`** -- The bot itself:
- `on_ready()` -- Logs when connected (uses discord.py's built-in ready state)
- `on_message()` -- Routes messages from designated channels to Agent Zero
- `_get_agent_response()` -- In-process routing via `initialize_agent()` + `AgentContext.communicate()`
- `_get_agent_response_http()` -- HTTP fallback via `POST /api/api_message`
- `_send_response()` -- Sends (potentially split) responses back to Discord
- `wait_until_ready_timeout()` -- Waits for Gateway connection with timeout (uses discord.py's built-in `wait_until_ready()`)

**Module-level functions:**
- `start_chat_bridge(token)` — Start the singleton bot as a background task
- `stop_chat_bridge()` — Gracefully shut down the bot
- `get_bot_status()` — Returns running/status/user/guilds info
- `add_chat_channel(channel_id, guild_id, label)` — Register a channel
- `remove_chat_channel(channel_id)` — Unregister a channel
- `get_chat_channels()` — List registered channels
- `get_context_id(channel_id)` / `set_context_id(channel_id, context_id)` — Context persistence

### Singleton Pattern
Only one bot instance runs at a time. `start_chat_bridge()` checks if a bot is already running and returns the existing instance if so. This prevents duplicate Gateway connections.

---

## Troubleshooting

### Bot connects but doesn't respond to messages

1. **Channel not registered** — The bot only responds in channels added via `discord_chat add_channel`. Check with `discord_chat list`.
2. **Missing Message Content intent** — Enable it in Developer Portal > Bot > Privileged Gateway Intents.
3. **Bot doesn't have channel access** — Ensure the bot role has View Channel + Read Message History + Send Messages in the target channel.

### "Bot failed to connect within timeout"

- Invalid bot token -- verify with: `curl -H "Authorization: Bot YOUR_TOKEN" https://discord.com/api/v10/users/@me`
- Network issue -- check that the Agent Zero container can reach `gateway.discord.gg`
- Discord outage -- check [Discord Status](https://discordstatus.com)

### Bot responds to itself / loops

This shouldn't happen — `on_message()` skips all bot messages (`message.author.bot`). If you see loops, check if another bot is relaying messages.

### Responses are cut off

Discord's 2000-char limit applies. The bot splits long messages automatically, but check that it has Send Messages permission (needed for each chunk).

### Context doesn't persist after restart

The channel-to-context mapping is saved in `data/chat_bridge_state.json`. However, the Agent Zero context itself is in-memory. After a full Agent Zero restart, the context UUID may point to a context that no longer exists, and a new one will be created. This means conversation history resets on restart.

### Multiple users in same channel — who's talking?

Each message is prefixed with `[Discord - DisplayName]:` so the LLM knows who said what. All users in a channel share the same conversation context.
