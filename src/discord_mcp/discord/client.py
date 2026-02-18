import asyncio
from collections.abc import Callable
from typing import Any, Optional

import discord
from discord.ext import commands

from discord_mcp.config import settings
from discord_mcp.discord.exceptions import DiscordAPIException
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class DiscordBotClient(commands.Bot):
    def __init__(
        self,
        token: str,
        session_id: str,
        max_shards: int = 1,
        intents: Optional[discord.Intents] = None,
        event_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.token = token
        self.session_id = session_id
        self.event_callback = event_callback

        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True
            intents.members = True
            intents.guild_messages = True
            intents.guild_reactions = True
            intents.voice_states = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            max_shards=max_shards,
            help_command=None,
        )

        self._ready_event = asyncio.Event()
        self._ready = False
        self._current_activity = None

    async def set_activity(
        self, activity_type: str = "playing", name: str = None, status: str = "online"
    ) -> None:
        """Update the bot's activity and status."""
        if not self._ready or not self.user:
            return

        activity = None
        if name:
            if activity_type == "playing":
                activity = discord.Game(name=name)
            elif activity_type == "listening":
                activity = discord.Activity(type=discord.ActivityType.listen, name=name)
            elif activity_type == "watching":
                activity = discord.Activity(type=discord.ActivityType.watch, name=name)
            elif activity_type == "streaming":
                activity = discord.Streaming(name=name, url="https://discord.com")
            elif activity_type == "competing":
                activity = discord.Activity(type=discord.ActivityType.competing, name=name)

        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }

        await self.change_presence(
            activity=activity, status=status_map.get(status, discord.Status.online)
        )
        self._current_activity = name
        logger.info("bot_activity_updated", activity_type=activity_type, name=name, status=status)

    async def clear_activity(self) -> None:
        """Clear the bot's activity."""
        if not self._ready or not self.user:
            return
        await self.change_presence(activity=None, status=discord.Status.online)
        self._current_activity = None
        logger.info("bot_activity_cleared")

    async def on_ready(self):
        self._ready = True
        self._ready_event.set()
        logger.info("bot_ready", session_id=self.session_id, user=str(self.user))
        if self.event_callback:
            self.event_callback(
                {
                    "type": "ready",
                    "session_id": self.session_id,
                    "bot": {
                        "id": str(self.user.id),
                        "username": self.user.name,
                        "discriminator": self.user.discriminator,
                    },
                }
            )

    async def on_message(self, message: discord.Message):
        if self.event_callback and not message.author.bot:
            self.event_callback(
                {
                    "type": "message",
                    "session_id": self.session_id,
                    "message": {
                        "id": str(message.id),
                        "channel_id": str(message.channel.id),
                        "author": {
                            "id": str(message.author.id),
                            "username": message.author.name,
                            "discriminator": message.author.discriminator,
                        },
                        "content": message.content,
                        "timestamp": message.created_at.isoformat(),
                        "guild_id": str(message.guild.id) if message.guild else None,
                    },
                }
            )

    async def on_member_join(self, member: discord.Member):
        if self.event_callback:
            self.event_callback(
                {
                    "type": "member_join",
                    "session_id": self.session_id,
                    "member": {
                        "id": str(member.id),
                        "username": member.name,
                        "discriminator": member.discriminator,
                        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                        "guild_id": str(member.guild.id),
                    },
                }
            )

    async def on_member_remove(self, member: discord.Member):
        if self.event_callback:
            self.event_callback(
                {
                    "type": "member_leave",
                    "session_id": self.session_id,
                    "member": {
                        "id": str(member.id),
                        "username": member.name,
                        "discriminator": member.discriminator,
                        "guild_id": str(member.guild.id),
                    },
                }
            )

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if self.event_callback:
            changes = {}
            if before.display_name != after.display_name:
                changes["nickname"] = {"before": before.display_name, "after": after.display_name}
            if before.roles != after.roles:
                changes["roles"] = {
                    "before": [str(r.id) for r in before.roles],
                    "after": [str(r.id) for r in after.roles],
                }

            if changes:
                self.event_callback(
                    {
                        "type": "member_update",
                        "session_id": self.session_id,
                        "member_id": str(after.id),
                        "guild_id": str(after.guild.id),
                        "changes": changes,
                    }
                )

    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ):
        if self.event_callback:
            changes = {}
            if before.name != after.name:
                changes["name"] = {"before": before.name, "after": after.name}
            if hasattr(before, "position") and hasattr(after, "position"):
                if before.position != after.position:
                    changes["position"] = {"before": before.position, "after": after.position}
            if hasattr(before, "category") and hasattr(after, "category"):
                if before.category != after.category:
                    changes["category"] = {
                        "before": str(before.category.id) if before.category else None,
                        "after": str(after.category.id) if after.category else None,
                    }

            if changes:
                self.event_callback(
                    {
                        "type": "channel_update",
                        "session_id": self.session_id,
                        "channel_id": str(after.id),
                        "guild_id": str(after.guild.id),
                        "changes": changes,
                    }
                )

    async def on_role_update(self, before: discord.Role, after: discord.Role):
        if self.event_callback:
            changes = {}
            if before.name != after.name:
                changes["name"] = {"before": before.name, "after": after.name}
            if before.color != after.color:
                changes["color"] = {"before": str(before.color), "after": str(after.color)}
            if before.permissions != after.permissions:
                changes["permissions"] = {"before": True, "after": True}
            if before.position != after.position:
                changes["position"] = {"before": before.position, "after": after.position}

            if changes:
                self.event_callback(
                    {
                        "type": "role_update",
                        "session_id": self.session_id,
                        "role_id": str(after.id),
                        "guild_id": str(after.guild.id),
                        "changes": changes,
                    }
                )

    async def setup_hook(self):
        logger.info("setting_up_bot", session_id=self.session_id)

    async def wait_until_ready(self, timeout: float = 30.0) -> bool:
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.error("bot_ready_timeout", session_id=self.session_id, timeout=timeout)
            return False

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def start_session(self):
        logger.info(
            "starting_session", session_id=self.session_id, token_prefix=self.token[:8] + "..."
        )
        await self.start(self.token)

    async def close_session(self):
        logger.info("closing_session", session_id=self.session_id)
        if self.is_ready:
            await self.close()
