# Quick Start Guide

Get the Discord plugin running in under 5 minutes.

---

## 1. Create a Discord Bot (2 min)

1. Open [discord.com/developers/applications](https://discord.com/developers/applications)
2. **New Application** > name it > **Create**
3. **Bot** tab > **Reset Token** > copy the **entire** token
4. Enable **Message Content Intent** under Privileged Gateway Intents
5. Go to **Installation** tab (left sidebar):
   - Keep **Guild Install** checked (not User Install)
   - Under Default Install Settings for Guild Install, add scope `bot`
   - Add permissions: View Channels, Send Messages, Read Message History, Add Reactions, Manage Messages
6. Copy the install link > open in browser > invite the bot to your server

## 2. Install the Plugin (1 min)

```bash
# Copy plugin into the container
docker cp discord-plugin/ <container_name>:/tmp/discord-plugin

# Run the automated installer
docker exec <container_name> bash /tmp/discord-plugin/install.sh

# Restart Agent Zero
docker exec <container_name> supervisorctl restart run_ui
```

The installer handles everything: copying files, creating the required symlink, installing dependencies, and enabling the plugin.

**Alternative -- manual install:**

```bash
docker cp discord-plugin/ <container_name>:/a0/usr/plugins/discord
docker exec <container_name> ln -sf /a0/usr/plugins/discord /a0/plugins/discord
docker exec <container_name> python /a0/usr/plugins/discord/initialize.py
docker exec <container_name> touch /a0/usr/plugins/discord/.toggle-1
docker exec <container_name> supervisorctl restart run_ui
```

## 3. Set Your Token (30 sec)

```bash
docker exec <container_name> bash -c 'cat > /a0/usr/plugins/discord/config.json << EOF
{
  "bot": {
    "token": "YOUR_BOT_TOKEN_HERE"
  }
}
EOF'
```

Or set `DISCORD_BOT_TOKEN=...` as an environment variable, or use the WebUI settings page.

## 4. Get Your Server ID (30 sec)

1. In Discord: **User Settings > Advanced > Developer Mode** > enable
2. Right-click your server name > **Copy Server ID**

You can also get it from a channel URL: `https://discord.com/channels/SERVER_ID/CHANNEL_ID`

## 5. Verify It Works

```bash
# Test the Discord connection
docker exec <container_name> curl -s http://localhost/api/plugins/discord/discord_test | python3 -m json.tool
```

You should see `"ok": true` with your bot's username.

## 6. Start Using It

Open Agent Zero chat and try these:

### List channels
> Show me the channels in Discord server YOUR_SERVER_ID

### Read messages
> Read the last 20 messages in Discord channel YOUR_CHANNEL_ID

### Summarize a channel
> Summarize the last 100 messages in Discord channel YOUR_CHANNEL_ID

### Extract research insights
> Extract insights from Discord channel YOUR_CHANNEL_ID focused on [topic]

### Send a message
> Send "Hello from Agent Zero!" to Discord channel YOUR_CHANNEL_ID

### Track community members
> List members in Discord server YOUR_SERVER_ID

### Set up the chat bridge
> Add channel YOUR_CHANNEL_ID to the Discord chat bridge, label it "llm-chat"
> Start the Discord chat bridge

Then go to that channel in Discord and chat directly with Agent Zero.

**Secure your chat bridge** -- see [Securing the Chat Bridge](#securing-the-chat-bridge) below for essential access controls.

### Monitor for alerts
> Watch Discord channel YOUR_CHANNEL_ID in server YOUR_SERVER_ID, call it "alerts"
> Check for new Discord alerts

---

## Securing the Chat Bridge

The chat bridge runs in **restricted mode** by default -- Discord users can only chat conversationally with the LLM and have no access to Agent Zero's tools or system. No additional configuration is needed for safe restricted-mode usage.

However, if you plan to use the chat bridge regularly, these settings add important access control:

### User Allowlist (Recommended)

Restrict which Discord users can interact with the bot. Unlisted users are silently ignored.

**Via WebUI:** Settings > Chat Bridge > User Allowlist > enter Discord user IDs (one per line) > Save

**Via config file:**
```json
{
  "chat_bridge": {
    "allowed_users": ["YOUR_DISCORD_USER_ID"]
  }
}
```

Get user IDs by enabling Developer Mode in Discord (User Settings > Advanced), then right-click a user > Copy User ID. Changes take effect immediately -- no bridge restart needed.

### Elevated Mode (Advanced -- Read Before Enabling)

Elevated mode grants authenticated Discord users full access to Agent Zero, including tools, code execution, and file operations. **This is disabled by default for good reason.**

Before enabling, read the [full security documentation](../README.md#elevated-mode----important).

**Required steps for safe elevated mode:**
1. Use a **private Discord server** with only trusted members
2. Configure the **User Allowlist** (above) with explicit user IDs
3. Enable elevated mode in WebUI Settings > Chat Bridge > Elevated Mode
4. Share the auth key only through **secure, out-of-band channels**
5. Use the default **1-hour session timeout** or shorter

**Optimal configuration:** A dedicated server with a single user and the bot. If collaboration is needed, only add users you deeply trust.

Users authenticate in Discord by typing `!auth <key>` (auto-deleted for security -- requires **Manage Messages** bot permission) and deauthenticate with `!deauth`.

---

## What Happens Next

- **Summaries** and **insights** are automatically saved to Agent Zero's memory
- The **persona registry** tracks users across sessions
- You can reference past summaries in future conversations -- Agent Zero remembers
- The **chat bridge** lets Discord users chat with Agent Zero's LLM in real time
- **Alert monitoring** can run on a schedule, with automatic image analysis

## Common Patterns

| What you want | What to say |
|---------------|-------------|
| See server structure | "List channels in server X" |
| Quick overview | "Summarize channel X" |
| Deep research | "Extract insights from channel X focused on [topic]" |
| Who's who | "List members in server X, then tell me about user Y" |
| Participate | "Read the last 20 messages in channel X, then reply to [person]" |
| Track someone | "Add a note about user X: they are the lead developer" |
| Live chat | "Add channel X to the chat bridge, then start it" |
| Monitor alerts | "Watch channel X for new messages, then set up polling every 15 min" |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Plugin not loading | Check symlink: `ls -la /a0/plugins/discord` should point to `/a0/usr/plugins/discord` |
| "No module named 'plugins.discord'" | Create symlink: `ln -sf /a0/usr/plugins/discord /a0/plugins/discord` |
| API returns 404 | Files must be in `/a0/` (not just `/git/agent-zero/`). Re-run the installer or copy manually. |
| "Bot token not configured" | Write token to config.json or set DISCORD_BOT_TOKEN env var |
| "Discord API error 401" | Invalid token -- regenerate in Developer Portal > Bot > Reset Token |
| "Discord API error 403" | Bot lacks channel permissions (View Channels, Send Messages, Read Message History) |
| Chat bridge not responding | Check User Allowlist (if configured), ensure Message Content Intent is enabled in Developer Portal |
| Changes not taking effect | Clear cache and restart: `find /a0 -path '*/discord*/__pycache__' -exec rm -rf {} +` then `supervisorctl restart run_ui` |

For detailed troubleshooting, see [README.md](README.md#troubleshooting).
