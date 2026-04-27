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

    await category.set_permissions(target, overwrite=overwrite)

    synced_channels: list[dict[str, str]] = []
    for child_channel in category.channels:
        await child_channel.set_permissions(target, overwrite=overwrite)
        synced_channels.append(
            {
                "channel_id": str(child_channel.id),
                "channel_name": child_channel.name,
            }
        )

    await _with_status(f"Setting category permissions")
    logger.info(
        "category_permissions_set",
        category_id=category_id,
        target_id=target_id,
        target_type=target_type,
        synced_channel_count=len(synced_channels),
    )

    return {
        "success": True,
        "category_id": category_id,
        "target_id": target_id,
        "target_type": target_type,
        "synced_channel_count": len(synced_channels),
        "synced_channels": synced_channels,
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


def _resolve_target(
    guild: discord.Guild, target_id: str, target_type: str
) -> discord.Role | discord.Member:
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

    return target


def _channel_sort_key(channel: discord.abc.GuildChannel) -> tuple[int, int, int, int]:
    category = getattr(channel, "category", None)
    category_position = category.position if category else -1
    category_id = category.id if category else 0
    return (category_position, category_id, channel.position, channel.id)


def _basic_channel_capabilities(perms: discord.Permissions) -> dict[str, bool]:
    return {
        "can_send_messages": getattr(perms, "send_messages", False),
        "can_read_history": getattr(perms, "read_message_history", False),
        "can_connect_voice": getattr(perms, "connect", False),
        "can_speak_voice": getattr(perms, "speak", False),
        "can_manage_channel": getattr(perms, "manage_channels", False),
        "can_manage_permissions": getattr(perms, "manage_roles", False),
        "can_manage_messages": getattr(perms, "manage_messages", False),
        "can_manage_threads": getattr(perms, "manage_threads", False),
        "can_create_public_threads": getattr(perms, "create_public_threads", False),
        "can_create_private_threads": getattr(perms, "create_private_threads", False),
    }


def _channel_summary_row(
    channel: discord.abc.GuildChannel,
    perms: discord.Permissions,
    include_basic_capabilities: bool = False,
) -> dict[str, Any]:
    row = {
        "channel_id": str(channel.id),
        "channel_name": channel.name,
        "channel_type": str(channel.type),
        "category_id": str(channel.category_id) if channel.category_id else None,
        "position": channel.position,
        "can_view": getattr(perms, "view_channel", False),
    }
    if include_basic_capabilities:
        row.update(_basic_channel_capabilities(perms))
    return row


def _channel_detail_row(
    channel: discord.abc.GuildChannel,
    perms: discord.Permissions,
    include_permission_map: bool = True,
) -> dict[str, Any]:
    row = _channel_summary_row(channel=channel, perms=perms, include_basic_capabilities=True)
    allowed, denied = _summarize_allowed_denied(perms)
    row["allowed_permissions"] = allowed
    row["denied_permissions"] = denied
    if include_permission_map:
        row["permissions"] = _permissions_to_dict(perms)
    return row


async def inspect_effective_permissions(
    guild_id: str,
    target_id: str,
    target_type: str,
    preview_limit: int = 20,
    include_permission_maps: bool = False,
    max_channels: int | None = None,
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

    if preview_limit < 1:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            "preview_limit must be greater than 0",
            details={"preview_limit": preview_limit},
        )

    if max_channels is not None and max_channels < 1:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            "max_channels must be greater than 0",
            details={"max_channels": max_channels},
        )

    target = _resolve_target(guild=guild, target_id=target_id, target_type=target_type)
    guild_permissions = (
        target.permissions
        if isinstance(target, discord.Role)
        else target.guild_permissions
    )
    guild_allowed, guild_denied = _summarize_allowed_denied(guild_permissions)

    all_channels = sorted(guild.channels, key=_channel_sort_key)
    evaluated_channels = (
        all_channels[:max_channels] if max_channels is not None else all_channels
    )
    channel_details: list[dict[str, Any]] = []
    accessible_preview: list[dict[str, Any]] = []
    inaccessible_preview: list[dict[str, Any]] = []
    accessible_count = 0
    inaccessible_count = 0

    for channel in evaluated_channels:
        perms = channel.permissions_for(target)
        can_view = perms.view_channel
        if can_view:
            accessible_count += 1
            if len(accessible_preview) < preview_limit:
                accessible_preview.append(
                    _channel_summary_row(channel=channel, perms=perms)
                )
        else:
            inaccessible_count += 1
            if len(inaccessible_preview) < preview_limit:
                inaccessible_preview.append(
                    _channel_summary_row(channel=channel, perms=perms)
                )
        if include_permission_maps:
            channel_details.append(
                _channel_detail_row(
                    channel=channel,
                    perms=perms,
                    include_permission_map=include_permission_maps,
                )
            )

    await _with_status("Inspecting effective permissions")
    logger.info(
        "effective_permissions_inspected",
        guild_id=guild_id,
        target_id=target_id,
        target_type=target_type,
    )

    response = {
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
        "total_channel_count": len(all_channels),
        "evaluated_channel_count": len(evaluated_channels),
        "max_channels_applied": max_channels,
        "accessible_channel_count": accessible_count,
        "inaccessible_channel_count": inaccessible_count,
        "preview_limit": preview_limit,
        "accessible_channels_preview": accessible_preview,
        "inaccessible_channels_preview": inaccessible_preview,
        "accessible_preview_has_more": accessible_count > len(accessible_preview),
        "inaccessible_preview_has_more": inaccessible_count > len(inaccessible_preview),
    }
    if include_permission_maps:
        response["channels"] = channel_details
    return response


async def inspect_target_channel_permissions(
    guild_id: str,
    target_id: str,
    target_type: str,
    channel_id: str,
    include_permission_map: bool = True,
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

    target = _resolve_target(guild=guild, target_id=target_id, target_type=target_type)

    channel = guild.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Channel {channel_id} not found in guild {guild_id}",
            details={"guild_id": guild_id, "channel_id": channel_id},
        )

    perms = channel.permissions_for(target)

    await _with_status("Inspecting channel permissions")
    logger.info(
        "target_channel_permissions_inspected",
        guild_id=guild_id,
        target_id=target_id,
        target_type=target_type,
        channel_id=channel_id,
    )

    return {
        "guild_id": guild_id,
        "target_id": target_id,
        "target_type": target_type,
        "target_name": target.name,
        "channel": _channel_detail_row(
            channel=channel,
            perms=perms,
            include_permission_map=include_permission_map,
        ),
    }


async def list_target_accessible_channels(
    guild_id: str,
    target_id: str,
    target_type: str,
    include_basic_capabilities: bool = False,
    max_channels: int | None = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    if max_channels is not None and max_channels < 1:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            "max_channels must be greater than 0",
            details={"max_channels": max_channels},
        )

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    target = _resolve_target(guild=guild, target_id=target_id, target_type=target_type)

    rows: list[dict[str, Any]] = []
    total_accessible = 0
    for channel in sorted(guild.channels, key=_channel_sort_key):
        perms = channel.permissions_for(target)
        if not perms.view_channel:
            continue
        total_accessible += 1
        if max_channels is not None and len(rows) >= max_channels:
            continue
        rows.append(
            _channel_summary_row(
                channel=channel,
                perms=perms,
                include_basic_capabilities=include_basic_capabilities,
            )
        )

    await _with_status("Listing accessible channels")
    logger.info(
        "target_accessible_channels_listed",
        guild_id=guild_id,
        target_id=target_id,
        target_type=target_type,
        returned_count=len(rows),
        total_accessible=total_accessible,
    )

    return {
        "guild_id": guild_id,
        "target_id": target_id,
        "target_type": target_type,
        "target_name": target.name,
        "returned_count": len(rows),
        "total_accessible_count": total_accessible,
        "max_channels_applied": max_channels,
        "has_more": total_accessible > len(rows),
        "channels": rows,
    }


async def list_target_inaccessible_channels(
    guild_id: str,
    target_id: str,
    target_type: str,
    include_basic_capabilities: bool = False,
    max_channels: int | None = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    if max_channels is not None and max_channels < 1:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            "max_channels must be greater than 0",
            details={"max_channels": max_channels},
        )

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import PermissionException

        raise PermissionException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    target = _resolve_target(guild=guild, target_id=target_id, target_type=target_type)

    rows: list[dict[str, Any]] = []
    total_inaccessible = 0
    for channel in sorted(guild.channels, key=_channel_sort_key):
        perms = channel.permissions_for(target)
        if perms.view_channel:
            continue
        total_inaccessible += 1
        if max_channels is not None and len(rows) >= max_channels:
            continue
        rows.append(
            _channel_summary_row(
                channel=channel,
                perms=perms,
                include_basic_capabilities=include_basic_capabilities,
            )
        )

    await _with_status("Listing inaccessible channels")
    logger.info(
        "target_inaccessible_channels_listed",
        guild_id=guild_id,
        target_id=target_id,
        target_type=target_type,
        returned_count=len(rows),
        total_inaccessible=total_inaccessible,
    )

    return {
        "guild_id": guild_id,
        "target_id": target_id,
        "target_type": target_type,
        "target_name": target.name,
        "returned_count": len(rows),
        "total_inaccessible_count": total_inaccessible,
        "max_channels_applied": max_channels,
        "has_more": total_inaccessible > len(rows),
        "channels": rows,
    }
