# Development Guide

How to extend, modify, and contribute to the Discord plugin.

---

## Plugin Framework Basics

This plugin follows Agent Zero's plugin framework conventions. Key rules:

- **`plugin.yaml`** in the root directory is required — it's how the framework discovers the plugin
- **Tools** go in `tools/` — one file per tool, one `Tool` subclass per file
- **Tool prompts** go in `prompts/agent.system.tool.<tool_name>.md` — this is what the LLM reads
- **Extensions** go in `extensions/python/<extension_point>/`
- **Helpers** go in `helpers/` — imported as `from plugins.discord.helpers.<module> import ...`
- **API endpoints** go in `api/` — Flask route handlers
- **WebUI** goes in `webui/` — `main.html` (dashboard) and `config.html` (settings)
- **Config** is accessed via `plugins.get_plugin_config("discord", agent=self.agent)`

---

## Adding a New Tool

### Step 1: Create the tool file

Create `tools/discord_search.py`:

```python
from helpers.tool import Tool, Response
from plugins.discord.helpers.discord_client import (
    DiscordClient, DiscordAPIError, get_discord_config,
)


class DiscordSearch(Tool):
    """Search messages in a Discord server."""

    async def execute(self, **kwargs) -> Response:
        guild_id = self.args.get("guild_id", "")
        query = self.args.get("query", "")

        if not guild_id or not query:
            return Response(
                message="Error: guild_id and query are required.",
                break_loop=False,
            )

        config = get_discord_config(self.agent)
        mode = "bot" if config.get("bot", {}).get("token") else "user"

        try:
            client = DiscordClient.from_config(agent=self.agent, mode=mode)
            self.set_progress("Searching...")

            results = await client.search_messages(guild_id=guild_id, query=query)
            await client.close()

            messages = results.get("messages", [])
            if not messages:
                return Response(
                    message=f"No messages found matching '{query}'.",
                    break_loop=False,
                )

            # Format results
            lines = [f"Found {len(messages)} results for '{query}':"]
            for group in messages:
                for msg in group:
                    author = msg.get("author", {}).get("username", "?")
                    content = msg.get("content", "")[:200]
                    lines.append(f"  - @{author}: {content}")

            return Response(message="\n".join(lines), break_loop=False)

        except DiscordAPIError as e:
            return Response(message=f"Discord API error: {e}", break_loop=False)
        except Exception as e:
            return Response(message=f"Error: {e}", break_loop=False)
```

### Step 2: Create the tool prompt

Create `prompts/agent.system.tool.discord_search.md`:

```markdown
## discord_search
Search messages in a Discord server by keyword.

**Arguments:**
- **guild_id** (string): Server ID to search in
- **query** (string): Search term

~~~json
{"guild_id": "123456789", "query": "migration plan"}
~~~
```

### Step 3: Restart Agent Zero

The plugin framework auto-discovers tools by filename. No registration needed.

---

## Adding a New Extension

Extensions hook into Agent Zero's lifecycle. Example: log every Discord tool call.

Create `extensions/python/tool_execute_after/_50_discord_log.py`:

```python
from helpers.extension import Extension


class DiscordToolLogger(Extension):
    async def execute(self, tool=None, response=None, **kwargs):
        if tool and tool.name.startswith("discord_"):
            print(f"[Discord] Tool {tool.name} completed: {response.message[:100]}")
```

The `_50_` prefix controls execution order (lower = earlier). The directory name (`tool_execute_after`) must match a valid extension point.

---

## Adding a Discord API Method

To add a new Discord API call, edit `helpers/discord_client.py`:

```python
# In the DiscordClient class:

async def get_guild_roles(self, guild_id: str) -> list:
    return await self._request("GET", f"/guilds/{guild_id}/roles")
```

The `_request` method handles:
- Authentication (bot or user token)
- Rate limiting
- 429 retry
- Error handling

For bot-only operations, add the guard:

```python
async def ban_member(self, guild_id: str, user_id: str) -> None:
    self._assert_bot_only("ban_member")
    await self._request("PUT", f"/guilds/{guild_id}/bans/{user_id}")
```

---

## Testing Locally

Since the plugin depends on Agent Zero's framework (helpers.tool, plugins.memory, etc.), full testing requires a running Agent Zero instance.

**Quick validation:**

```python
# Test the Discord client standalone
import asyncio
from helpers.discord_client import DiscordClient

async def test():
    client = DiscordClient(token="your_bot_token", is_bot=True)
    user = await client.get_current_user()
    print(f"Connected as: {user['username']}")

    channels = await client.get_guild_channels("your_guild_id")
    for ch in channels:
        print(f"  #{ch['name']} ({ch['id']})")

    await client.close()

asyncio.run(test())
```

**Integration testing:**

1. Install the plugin into a running Agent Zero instance
2. Open the WebUI and test the connection via the dashboard
3. Ask the agent to list channels, read messages, etc.
4. Check Agent Zero logs for errors

---

## Known Limitations

### WebUI Config Uses Custom API Instead of Framework Settings Store

The `webui/config.html` settings panel uses a custom API endpoint (`discord_config_api`) with raw `fetch()` calls instead of the framework's standard `$store.pluginSettings` Alpine.js store used by core plugins (e.g., the Memory plugin).

**Why:** Discord tokens are sensitive credentials. Our custom API masks tokens in GET responses (showing only first 4 + last 4 characters) and preserves existing tokens when a masked value is submitted back. The framework's generic `get_config`/`save_config` API does not provide this masking behavior, which would expose full tokens in the browser.

**Impact:** Per-project and per-agent config scoping through the WebUI settings modal will not work -- changes made in the config UI always write to the global plugin config at `usr/plugins/discord/config.json`. However, file-based scoping still works: you can manually create scoped config files at the paths defined in the [Settings Resolution](https://www.agent-zero.ai/p/docs/plugins/#settings-resolution) hierarchy (e.g., `usr/agents/<profile>/plugins/discord/config.json`).

**Future fix:** If the framework adds a hook for custom serialization or field-level masking in the settings store, the config UI should be migrated to use `$store.pluginSettings` for full scope support.

---

## Project Structure Reference

```
discord-plugin/
+-- README.md                # Top-level overview with quick start
+-- plugin.yaml              # Manifest -- do not rename
+-- default_config.yaml      # Defaults -- values used when no config.json exists
+-- initialize.py            # Run once to install deps (aiohttp, pyyaml, discord.py)
+-- install.sh               # Automated installer (auto-detects /a0/ vs /git/agent-zero/)
+-- helpers/
|   +-- __init__.py
|   +-- discord_client.py    # REST API wrapper with rate limiting
|   +-- discord_bot.py       # Chat bridge bot (discord.py Gateway + AgentContext)
|   +-- persona_registry.py  # JSON-based user tracking
|   +-- poll_state.py        # Polling state tracker (last seen IDs, alert history)
+-- tools/
|   +-- discord_read.py      # Read channels/threads/messages
|   +-- discord_send.py      # Send messages/reactions (bot only)
|   +-- discord_summarize.py # Summarize -> LLM -> memory
|   +-- discord_insights.py  # Insights -> LLM -> memory
|   +-- discord_members.py   # Member queries + persona registry
|   +-- discord_poll.py      # Channel monitoring with image analysis
|   +-- discord_chat.py      # Chat bridge management (start/stop/add/remove)
+-- prompts/
|   +-- agent.system.tool.discord_read.md
|   +-- agent.system.tool.discord_send.md
|   +-- agent.system.tool.discord_summarize.md
|   +-- agent.system.tool.discord_insights.md
|   +-- agent.system.tool.discord_members.md
|   +-- agent.system.tool.discord_poll.md
|   +-- agent.system.tool.discord_chat.md
+-- api/
|   +-- discord_test.py          # POST /api/plugins/discord/discord_test
|   +-- discord_config_api.py    # GET/POST /api/plugins/discord/discord_config_api
+-- webui/
|   +-- main.html            # Dashboard
|   +-- config.html          # Settings
+-- extensions/python/
|   +-- agent_init/
|       +-- _10_discord_chat.py  # Auto-start chat bridge on agent init
+-- skills/
|   +-- discord-research/SKILL.md
|   +-- discord-communicate/SKILL.md
|   +-- discord-persona-mapping/SKILL.md
|   +-- discord-alerts/SKILL.md
|   +-- discord-chat/SKILL.md
+-- data/                    # Runtime data (auto-created)
|   +-- persona_registry.json
|   +-- poll_state.json
|   +-- chat_bridge_state.json
+-- docs/
    +-- README.md            # Full documentation
    +-- QUICKSTART.md        # 5-minute setup guide
    +-- CHAT_BRIDGE.md       # Chat bridge setup and config
    +-- API_REFERENCE.md     # API endpoints and data format docs
    +-- DEVELOPMENT.md       # This file
```

### Important: Plugin Installation Path

Agent Zero uses a dual-path architecture:
- `/git/agent-zero/` -- source code (persists across rebuilds)
- `/a0/` -- runtime copy (where the server runs from)

User plugins go in `usr/plugins/<name>/` but need a symlink at `plugins/<name>/` for Python imports:
```bash
ln -sf /a0/usr/plugins/discord /a0/plugins/discord
```

Without this symlink, `from plugins.discord.helpers...` imports will fail with `ModuleNotFoundError`. The `install.sh` script creates this automatically.

When developing, always copy changes to `/a0/usr/plugins/discord/`, clear `__pycache__`, and restart:
```bash
docker cp your-file.py <container>:/a0/usr/plugins/discord/path/to/file.py
docker exec <container> find /a0 -path '*/discord*/__pycache__' -type d -exec rm -rf {} +
docker exec <container> supervisorctl restart run_ui
```
