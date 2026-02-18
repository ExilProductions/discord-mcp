from typing import Any, Optional

import discord

from discord_mcp.discord.session import DiscordSession
from discord_mcp.mcp.context import get_current_session, update_bot_status, clear_bot_status
from discord_mcp.models.channel import (
    ChannelCreate,
    ChannelDelete,
    ChannelEdit,
    ChannelMove,
    ChannelResponse,
)
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    """Helper to update bot status."""
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    """Handle common Discord HTTP errors."""
    if isinstance(e, discord.Forbidden):
        error_code = getattr(e, "code", None)
        if error_code == 50013:
            from discord_mcp.discord.exceptions import ChannelException

            raise ChannelException(
                "Bot lacks required permissions. Please ensure the bot has the necessary permissions in Discord server settings.",
                details={"error_code": error_code, "original_error": str(e)},
            )
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Permission denied: {str(e)}",
            details={"error_code": error_code, "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            "Channel not found",
            details={"original_error": str(e)},
        )


CHANNEL_TYPE_MAP = {
    "text": discord.ChannelType.text,
    "voice": discord.ChannelType.voice,
    "category": discord.ChannelType.category,
    "news": discord.ChannelType.news,
    "stage": discord.ChannelType.stage_voice,
    "forum": discord.ChannelType.forum,
    "media": discord.ChannelType.media,
}


async def create_channel(
    name: str,
    guild_id: str,
    channel_type: str = "text",
    topic: Optional[str] = None,
    bitrate: Optional[int] = None,
    user_limit: Optional[int] = None,
    position: Optional[int] = None,
    nsfw: bool = False,
    rate_limit_per_user: Optional[int] = None,
    permission_overwrites: Optional[list[dict[str, str]]] = None,
    parent_id: Optional[str] = None,
    rtc_region: Optional[str] = None,
    video_quality_mode: Optional[str] = "auto",
    default_auto_archive_duration: Optional[int] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    channel_type_enum = CHANNEL_TYPE_MAP.get(channel_type, discord.ChannelType.text)

    overwrites = []
    if permission_overwrites:
        for overwrite in permission_overwrites:
            target_id = overwrite.get("id")
            target_type = overwrite.get("type", "role")
            allow = discord.Permissions(int(overwrite.get("allow", 0)))
            deny = discord.Permissions(int(overwrite.get("deny", 0)))

            if target_type == "role":
                target = guild.get_role(int(target_id)) if target_id else None
            else:
                target = guild.get_member(int(target_id)) if target_id else None

            if target:
                overwrites.append(discord.PermissionOverwrite.from_pair(allow, deny))

    category = None
    if parent_id:
        category = discord.utils.get(guild.categories, id=int(parent_id))

    video_quality = discord.VideoQualityMode.auto
    if video_quality_mode == "full":
        video_quality = discord.VideoQualityMode.full

    kwargs: dict[str, Any] = {
        "name": name,
        "topic": topic,
        "bitrate": bitrate,
        "user_limit": user_limit,
        "position": position,
        "nsfw": nsfw,
        "rate_limit_per_user": rate_limit_per_user,
        "permission_overwrites": overwrites,
        "rtc_region": rtc_region,
        "video_quality_mode": video_quality,
        "default_auto_archive_duration": default_auto_archive_duration,
    }

    if channel_type_enum in (
        discord.ChannelType.text,
        discord.ChannelType.news,
        discord.ChannelType.forum,
    ):
        kwargs["category"] = category

    if channel_type_enum == discord.ChannelType.voice:
        kwargs["category"] = category
        kwargs["bitrate"] = bitrate
        kwargs["user_limit"] = user_limit

    # Only add valid args for text/news/forum channels
    if channel_type_enum in (
        discord.ChannelType.text,
        discord.ChannelType.news,
        discord.ChannelType.forum,
    ):
        kwargs["category"] = category

    # Category doesn't have these args
    if channel_type_enum == discord.ChannelType.category:
        channel = await guild.create_category(
            **{
                k: v
                for k, v in kwargs.items()
                if k
                not in [
                    "topic",
                    "nsfw",
                    "rate_limit_per_user",
                    "rtc_region",
                    "video_quality_mode",
                    "default_auto_archive_duration",
                    "bitrate",
                    "user_limit",
                    "permission_overwrites",
                ]
            }
        )
    elif channel_type_enum == discord.ChannelType.voice:
        channel = await guild.create_voice_channel(
            **{
                k: v
                for k, v in kwargs.items()
                if k
                not in [
                    "topic",
                    "nsfw",
                    "rate_limit_per_user",
                    "default_auto_archive_duration",
                    "permission_overwrites",
                ]
            }
        )
    else:
        channel_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "bitrate",
                "user_limit",
                "rtc_region",
                "video_quality_mode",
                "permission_overwrites",
            ]
        }
        if "rate_limit_per_user" in channel_kwargs:
            channel_kwargs["slowmode_delay"] = channel_kwargs.pop("rate_limit_per_user")
        channel = await guild.create_text_channel(**channel_kwargs)

    logger.info("channel_created", channel_id=str(channel.id), name=name, guild_id=guild_id)

    await update_bot_status(f"Creating channel: {name}", "playing")

    return {
        "id": str(channel.id),
        "name": channel.name,
        "type": channel.type.value,
        "guild_id": str(channel.guild.id),
        "position": channel.position,
        "topic": getattr(channel, "topic", None),
        "nsfw": getattr(channel, "nsfw", False),
        "parent_id": str(channel.category.id) if channel.category else None,
    }


async def edit_channel(
    channel_id: str,
    name: Optional[str] = None,
    topic: Optional[str] = None,
    bitrate: Optional[int] = None,
    user_limit: Optional[int] = None,
    position: Optional[int] = None,
    nsfw: Optional[bool] = None,
    rate_limit_per_user: Optional[int] = None,
    permission_overwrites: Optional[list[dict[str, str]]] = None,
    parent_id: Optional[str] = None,
    rtc_region: Optional[str] = None,
    video_quality_mode: Optional[str] = None,
    default_auto_archive_duration: Optional[int] = None,
    lock_permissions: Optional[bool] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    guild = channel.guild

    overwrites = []
    if permission_overwrites:
        for overwrite in permission_overwrites:
            target_id = overwrite.get("id")
            target_type = overwrite.get("type", "role")
            allow = discord.Permissions(int(overwrite.get("allow", 0)))
            deny = discord.Permissions(int(overwrite.get("deny", 0)))

            if target_type == "role":
                target = guild.get_role(int(target_id)) if target_id else None
            else:
                target = guild.get_member(int(target_id)) if target_id else None

            if target:
                overwrites.append(discord.PermissionOverwrite.from_pair(allow, deny))

    category = None
    if parent_id:
        category = discord.utils.get(guild.categories, id=int(parent_id))

    video_quality = None
    if video_quality_mode == "auto":
        video_quality = discord.VideoQualityMode.auto
    elif video_quality_mode == "full":
        video_quality = discord.VideoQualityMode.full

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if topic is not None:
        kwargs["topic"] = topic
    if bitrate is not None:
        kwargs["bitrate"] = bitrate
    if user_limit is not None:
        kwargs["user_limit"] = user_limit
    if position is not None:
        kwargs["position"] = position
    if nsfw is not None:
        kwargs["nsfw"] = nsfw
    if rate_limit_per_user is not None:
        kwargs["rate_limit_per_user"] = rate_limit_per_user
    if overwrites:
        kwargs["overwrites"] = overwrites
    if category is not None:
        kwargs["category"] = category
    if rtc_region is not None:
        kwargs["rtc_region"] = rtc_region
    if video_quality is not None:
        kwargs["video_quality_mode"] = video_quality
    if default_auto_archive_duration is not None:
        kwargs["default_auto_archive_duration"] = default_auto_archive_duration
    if lock_permissions is not None:
        kwargs["lock_permissions"] = lock_permissions

    try:
        await channel.edit(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Editing channel")
    logger.info("channel_edited", channel_id=channel_id)

    return {
        "id": str(channel.id),
        "name": channel.name,
        "type": channel.type.value,
        "guild_id": str(channel.guild.id),
        "position": channel.position,
    }


async def delete_channel(channel_id: str, guild_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    channel_name = channel.name
    try:
        await channel.delete()
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Deleting channel")
    logger.info("channel_deleted", channel_id=channel_id, name=channel_name, guild_id=guild_id)

    return {
        "success": True,
        "channel_id": channel_id,
        "name": channel_name,
        "guild_id": guild_id,
    }


async def move_channel(
    channel_id: str,
    guild_id: str,
    position: Optional[int] = None,
    parent_id: Optional[str] = None,
    lock_permissions: bool = False,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    category = None
    if parent_id:
        category = discord.utils.get(guild.categories, id=int(parent_id))

    kwargs: dict[str, Any] = {"lock_permissions": lock_permissions}
    if position is not None:
        kwargs["position"] = position
    if category is not None:
        kwargs["category"] = category

    try:
        await channel.edit(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Moving channel")
    logger.info("channel_moved", channel_id=channel_id, guild_id=guild_id)

    return {
        "success": True,
        "channel_id": channel_id,
        "guild_id": guild_id,
    }


async def get_channels(guild_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    channels = []
    for channel in guild.channels:
        channels.append(
            {
                "id": str(channel.id),
                "name": channel.name,
                "type": channel.type.value,
                "guild_id": str(guild.id),
                "position": channel.position,
                "category_id": str(channel.category_id) if channel.category_id else None,
            }
        )

    return channels


async def get_channel(channel_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ChannelException

        raise ChannelException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    return {
        "id": str(channel.id),
        "name": channel.name,
        "type": channel.type.value,
        "guild_id": str(channel.guild.id),
        "position": channel.position,
        "topic": getattr(channel, "topic", None),
        "nsfw": getattr(channel, "nsfw", False),
        "parent_id": str(channel.category_id) if channel.category_id else None,
    }
