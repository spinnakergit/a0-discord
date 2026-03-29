"""API endpoint: Test Discord connection.
URL: POST /api/plugins/discord/discord_test
"""
from helpers.api import ApiHandler, Request, Response


class DiscordTest(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Self-heal: ensure symlink exists for plugin namespace imports
            from pathlib import Path
            plugin_dir = Path(__file__).resolve().parent.parent
            for root in [Path("/a0"), Path("/git/agent-zero")]:
                plugins_dir = root / "plugins"
                if plugins_dir.is_dir():
                    symlink = plugins_dir / "discord"
                    if not symlink.exists():
                        symlink.symlink_to(plugin_dir)
                    break

            from plugins.discord.helpers.discord_client import DiscordClient, get_discord_config

            config = get_discord_config()
            mode = "bot" if config.get("bot", {}).get("token") else "user"

            if mode == "bot" and not config.get("bot", {}).get("token"):
                if not config.get("user", {}).get("token"):
                    return {"ok": False, "error": "No token configured"}

            client = DiscordClient.from_config(mode=mode)
            user = await client.get_current_user()
            await client.close()

            return {
                "ok": True,
                "user": user.get("username", "Unknown"),
                "mode": mode,
                "id": user.get("id"),
            }
        except Exception as e:
            return {"ok": False, "error": f"Connection failed: {type(e).__name__}"}
