"""Auto-start the Discord chat bridge on agent initialization.

Only starts if:
  - A bot token is configured
  - chat_bridge.auto_start is true in config
  - At least one chat channel is registered
"""

import asyncio
import logging

logger = logging.getLogger("discord_chat_bridge")


async def execute(agent, **kwargs):
    try:
        from helpers import plugins

        config = plugins.get_plugin_config("discord", agent=agent)
        bot_token = config.get("bot", {}).get("token", "")

        if not bot_token:
            return  # No token, skip

        bridge_config = config.get("chat_bridge", {})
        if not bridge_config.get("auto_start", False):
            return  # Auto-start disabled

        from usr.plugins.discord.helpers.discord_bot import get_chat_channels, start_chat_bridge

        channels = get_chat_channels()
        if not channels:
            return  # No channels configured

        logger.info(f"Auto-starting Discord chat bridge ({len(channels)} channel(s))...")
        await start_chat_bridge(bot_token)
        logger.info("Discord chat bridge auto-started successfully.")

    except Exception as e:
        logger.warning(f"Discord chat bridge auto-start failed: {e}")
