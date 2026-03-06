"""API endpoint: Get/set Discord plugin configuration.
URL: POST /api/plugins/discord/discord_config_api
"""
import json
import yaml
from pathlib import Path
from helpers.api import ApiHandler, Request, Response


def _get_config_path() -> Path:
    """Find the writable config path for the discord plugin."""
    candidates = [
        Path(__file__).parent.parent / "config.json",
        Path("/a0/usr/plugins/discord/config.json"),
        Path("/a0/plugins/discord/config.json"),
        Path("/git/agent-zero/usr/plugins/discord/config.json"),
    ]
    for p in candidates:
        if p.parent.exists():
            return p
    return candidates[-1]


class DiscordConfigApi(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "get")
        if request.method == "GET" or action == "get":
            return self._get_config()
        else:
            return self._set_config(input)

    def _get_config(self) -> dict:
        try:
            config_path = _get_config_path()
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                default_path = config_path.parent / "default_config.yaml"
                if default_path.exists():
                    with open(default_path, "r") as f:
                        config = yaml.safe_load(f) or {}
                else:
                    config = {}

            # Mask tokens for security
            masked = json.loads(json.dumps(config))
            for key in ("bot", "user"):
                if key in masked and masked[key].get("token"):
                    token = masked[key]["token"]
                    if len(token) > 8:
                        masked[key]["token"] = token[:4] + "..." + token[-4:]
            return masked
        except Exception as e:
            return {"error": str(e)}

    def _set_config(self, input: dict) -> dict:
        try:
            config = input.get("config", input)
            if not config or config == {"action": "set"}:
                return {"error": "No config provided"}

            # Remove the action key if present
            config.pop("action", None)

            config_path = _get_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Merge with existing config (preserve tokens if masked)
            existing = {}
            if config_path.exists():
                with open(config_path, "r") as f:
                    existing = json.load(f)

            for key in ("bot", "user"):
                new_token = config.get(key, {}).get("token", "")
                if new_token and "..." in new_token:
                    config.setdefault(key, {})["token"] = existing.get(key, {}).get("token", "")

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}
