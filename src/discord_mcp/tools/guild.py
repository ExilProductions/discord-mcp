from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    """Helper to update bot status."""
    await update_bot_status(activity, "playing")


async def get_guild_settings(guild_id: str) -> dict[str, Any]:
    """Get settings for a guild/server."""
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    return {
        "id": str(guild.id),
        "name": guild.name,
        "description": guild.description,
        "icon_url": str(guild.icon.url) if guild.icon else None,
        "banner_url": str(guild.banner.url) if guild.banner else None,
        "splash_url": str(guild.splash.url) if guild.splash else None,
        "verification_level": guild.verification_level.name,
        "explicit_content_filter": guild.explicit_content_filter.name,
        "default_notifications": guild.default_notifications.name,
        "mfa_level": guild.mfa_level,
        "max_members": guild.max_members,
        "premium_tier": guild.premium_tier,
        "premium_subscription_count": guild.premium_subscription_count,
        "nsfw_level": guild.nsfw_level.name,
        "afk_timeout": guild.afk_timeout,
        "afk_channel_id": str(guild.afk_channel.id) if guild.afk_channel else None,
        "system_channel_id": str(guild.system_channel.id) if guild.system_channel else None,
        "rules_channel_id": str(guild.rules_channel.id) if guild.rules_channel else None,
        "public_updates_channel_id": str(guild.public_updates_channel.id)
        if guild.public_updates_channel
        else None,
    }


async def edit_guild_settings(
    guild_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    verification_level: Optional[str] = None,
    explicit_content_filter: Optional[str] = None,
    default_notifications: Optional[str] = None,
    afk_timeout: Optional[int] = None,
    afk_channel_id: Optional[str] = None,
    system_channel_id: Optional[str] = None,
    rules_channel_id: Optional[str] = None,
    public_updates_channel_id: Optional[str] = None,
    icon_base64: Optional[str] = None,
    banner_base64: Optional[str] = None,
    splash_base64: Optional[str] = None,
) -> dict[str, Any]:
    """Edit settings for a guild/server."""
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    kwargs: dict[str, Any] = {}

    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if afk_timeout is not None:
        kwargs["afk_timeout"] = afk_timeout

    verification_map = {
        "none": discord.VerificationLevel.none,
        "low": discord.VerificationLevel.low,
        "medium": discord.VerificationLevel.medium,
        "high": discord.VerificationLevel.high,
        "highest": discord.VerificationLevel.highest,
    }
    if verification_level and verification_level.lower() in verification_map:
        kwargs["verification_level"] = verification_map[verification_level.lower()]

    explicit_filter_map = {
        "disabled": discord.ExplicitContentFilter.disabled,
        "members_without_roles": discord.ExplicitContentFilter.members_without_roles,
        "all_members": discord.ExplicitContentFilter.all_members,
    }
    if explicit_content_filter and explicit_content_filter.lower() in explicit_filter_map:
        kwargs["explicit_content_filter"] = explicit_filter_map[explicit_content_filter.lower()]

    notifications_map = {
        "all_messages": discord.NotificationLevel.all_messages,
        "mentions_only": discord.NotificationLevel.mentions_only,
    }
    if default_notifications and default_notifications.lower() in notifications_map:
        kwargs["default_notifications"] = notifications_map[default_notifications.lower()]

    if afk_channel_id:
        channel = guild.get_channel(int(afk_channel_id))
        if channel:
            kwargs["afk_channel"] = channel

    if system_channel_id:
        channel = guild.get_channel(int(system_channel_id))
        if channel:
            kwargs["system_channel"] = channel

    if rules_channel_id:
        channel = guild.get_channel(int(rules_channel_id))
        if channel:
            kwargs["rules_channel"] = channel

    if public_updates_channel_id:
        channel = guild.get_channel(int(public_updates_channel_id))
        if channel:
            kwargs["public_updates_channel"] = channel

    await guild.edit(**kwargs)

    await _with_status(f"Editing server settings")
    logger.info("guild_settings_edited", guild_id=guild_id)

    return {
        "success": True,
        "guild_id": guild_id,
        "updated_settings": list(kwargs.keys()),
    }
