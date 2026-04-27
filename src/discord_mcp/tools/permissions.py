from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
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
            from discord_mcp.discord.exceptions import PermissionException

            raise PermissionException(
                "Bot lacks required permissions. Please ensure the bot has the necessary permissions in Discord server settings.",
                details={"error_code": error_code, "original_error": str(e)},
            )
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Permission denied: {str(e)}",
            details={"error_code": error_code, "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            "Resource not found",
            details={"original_error": str(e)},
        )


async def set_channel_permissions(
    channel_id: str,
    target_id: str,
    target_type: str,
    allow: Optional[str] = None,
    deny: Optional[str] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    guild = channel.guild

    if target_type == "role":
        target = guild.get_role(int(target_id))
    elif target_type == "member":
        target = guild.get_member(int(target_id))
    else:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Invalid target type: {target_type}",
            details={"target_type": target_type},
        )

    if not target:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Target {target_id} not found",
            details={"target_id": target_id, "target_type": target_type},
        )

    allow_perms = discord.Permissions(int(allow)) if allow else discord.Permissions()
    deny_perms = discord.Permissions(int(deny)) if deny else discord.Permissions()

    overwrite = discord.PermissionOverwrite.from_pair(allow_perms, deny_perms)

    if isinstance(target, discord.Role):
        await channel.set_permissions(target, overwrite=overwrite)
    else:
        await channel.set_permissions(target, overwrite=overwrite)

    await _with_status(f"Setting channel permissions")
    logger.info(
        "channel_permissions_set",
        channel_id=channel_id,
        target_id=target_id,
        target_type=target_type,
    )

    return {
        "success": True,
        "channel_id": channel_id,
        "target_id": target_id,
        "target_type": target_type,
    }


async def set_category_permissions(
    category_id: str,
    target_id: str,
    target_type: str,
    allow: Optional[str] = None,
    deny: Optional[str] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    category = client.get_channel(int(category_id))
    if not category or not isinstance(category, discord.CategoryChannel):
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Category {category_id} not found",
            details={"category_id": category_id},
        )

    guild = category.guild

    if target_type == "role":
        target = guild.get_role(int(target_id))
    elif target_type == "member":
        target = guild.get_member(int(target_id))
    else:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Invalid target type: {target_type}",
            details={"target_type": target_type},
        )

    if not target:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Target {target_id} not found",
            details={"target_id": target_id, "target_type": target_type},
        )

    allow_perms = discord.Permissions(int(allow)) if allow else discord.Permissions()
    deny_perms = discord.Permissions(int(deny)) if deny else discord.Permissions()

    overwrite = discord.PermissionOverwrite.from_pair(allow_perms, deny_perms)

    if isinstance(target, discord.Role):
        await category.set_permissions(target, overwrite=overwrite)
    else:
        await category.set_permissions(target, overwrite=overwrite)

    await _with_status(f"Setting category permissions")
    logger.info(
        "category_permissions_set",
        category_id=category_id,
        target_id=target_id,
        target_type=target_type,
    )

    return {
        "success": True,
        "category_id": category_id,
        "target_id": target_id,
        "target_type": target_type,
    }


async def set_role_permissions(
    role_id: str,
    guild_id: str,
    permissions: str,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    role = guild.get_role(int(role_id))
    if not role:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Role {role_id} not found",
            details={"role_id": role_id},
        )

    await role.edit(permissions=discord.Permissions(int(permissions)))

    await _with_status(f"Setting role permissions")
    logger.info("role_permissions_set", role_id=role_id, guild_id=guild_id)

    return {
        "success": True,
        "role_id": role_id,
        "guild_id": guild_id,
        "permissions": permissions,
    }


async def get_channel_permissions(channel_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    overwrites = []
    for target, overwrite in channel.overwrites.items():
        target_type = "role" if isinstance(target, discord.Role) else "member"
        allow_perms, deny_perms = overwrite.pair()
        overwrites.append(
            {
                "target_id": str(target.id),
                "target_type": target_type,
                "target_name": target.name,
                "allow": str(allow_perms.value),
                "deny": str(deny_perms.value),
            }
        )

    return overwrites


async def get_category_permissions(category_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    category = client.get_channel(int(category_id))
    if not category or not isinstance(category, discord.CategoryChannel):
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Category {category_id} not found",
            details={"category_id": category_id},
        )

    overwrites = []
    for target, overwrite in category.overwrites.items():
        target_type = "role" if isinstance(target, discord.Role) else "member"
        allow_perms, deny_perms = overwrite.pair()
        overwrites.append(
            {
                "target_id": str(target.id),
                "target_type": target_type,
                "target_name": target.name,
                "allow": str(allow_perms.value),
                "deny": str(deny_perms.value),
            }
        )

    return overwrites


async def remove_channel_permissions(
    channel_id: str,
    target_id: str,
    target_type: str,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    guild = channel.guild

    if target_type == "role":
        target = guild.get_role(int(target_id))
    elif target_type == "member":
        target = guild.get_member(int(target_id))
    else:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Invalid target type: {target_type}",
            details={"target_type": target_type},
        )

    if not target:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Target {target_id} not found",
            details={"target_id": target_id, "target_type": target_type},
        )

    await channel.set_permissions(target, overwrite=None)

    logger.info(
        "channel_permissions_removed",
        channel_id=channel_id,
        target_id=target_id,
        target_type=target_type,
    )

    return {
        "success": True,
        "channel_id": channel_id,
        "target_id": target_id,
        "target_type": target_type,
    }


def _permissions_to_dict(perms: discord.Permissions) -> dict[str, bool]:
    return {name: value for name, value in perms}


def _summarize_allowed_denied(perms: discord.Permissions) -> tuple[list[str], list[str]]:
    allowed = []
    denied = []
    for name, value in perms:
        if value:
            allowed.append(name)
        else:
            denied.append(name)
    return allowed, denied


async def inspect_effective_permissions(
    guild_id: str,
    target_id: str,
    target_type: str,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    if target_type == "role":
        target = guild.get_role(int(target_id))
    elif target_type == "member":
        target = guild.get_member(int(target_id))
    else:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Invalid target type: {target_type}",
            details={"target_type": target_type},
        )

    if not target:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Target {target_id} not found",
            details={"target_id": target_id, "target_type": target_type},
        )

    guild_permissions = (
        target.permissions
        if isinstance(target, discord.Role)
        else target.guild_permissions
    )
    guild_allowed, guild_denied = _summarize_allowed_denied(guild_permissions)

    channel_permissions: list[dict[str, Any]] = []
    accessible_channels: list[str] = []
    inaccessible_channels: list[str] = []

    for channel in guild.channels:
        perms = channel.permissions_for(target)
        can_view = perms.view_channel
        if can_view:
            accessible_channels.append(str(channel.id))
        else:
            inaccessible_channels.append(str(channel.id))
        allowed, denied = _summarize_allowed_denied(perms)
        channel_permissions.append(
            {
                "channel_id": str(channel.id),
                "channel_name": channel.name,
                "channel_type": str(channel.type),
                "category_id": str(channel.category_id) if channel.category_id else None,
                "position": channel.position,
                "can_view": can_view,
                "can_send_messages": getattr(perms, "send_messages", False),
                "can_read_history": getattr(perms, "read_message_history", False),
                "can_connect_voice": getattr(perms, "connect", False),
                "can_speak_voice": getattr(perms, "speak", False),
                "can_manage_channel": getattr(perms, "manage_channels", False),
                "can_manage_permissions": getattr(perms, "manage_roles", False),
                "can_manage_messages": getattr(perms, "manage_messages", False),
                "can_manage_threads": getattr(perms, "manage_threads", False),
                "can_create_public_threads": getattr(perms, "create_public_threads", False),
                "can_create_private_threads": getattr(
                    perms, "create_private_threads", False
                ),
                "allowed_permissions": allowed,
                "denied_permissions": denied,
                "permissions": _permissions_to_dict(perms),
            }
        )

    await _with_status("Inspecting effective permissions")
    logger.info(
        "effective_permissions_inspected",
        guild_id=guild_id,
        target_id=target_id,
        target_type=target_type,
    )

    return {
        "guild_id": guild_id,
        "target_id": target_id,
        "target_type": target_type,
        "target_name": target.name,
        "guild_permissions": _permissions_to_dict(guild_permissions),
        "guild_allowed_permissions": guild_allowed,
        "guild_denied_permissions": guild_denied,
        "can_administrator": getattr(guild_permissions, "administrator", False),
        "can_manage_guild": getattr(guild_permissions, "manage_guild", False),
        "can_manage_roles": getattr(guild_permissions, "manage_roles", False),
        "can_manage_channels": getattr(guild_permissions, "manage_channels", False),
        "can_kick_members": getattr(guild_permissions, "kick_members", False),
        "can_ban_members": getattr(guild_permissions, "ban_members", False),
        "can_moderate_members": getattr(guild_permissions, "moderate_members", False),
        "channel_count": len(channel_permissions),
        "accessible_channel_count": len(accessible_channels),
        "inaccessible_channel_count": len(inaccessible_channels),
        "accessible_channel_ids": accessible_channels,
        "inaccessible_channel_ids": inaccessible_channels,
        "channels": channel_permissions,
    }
