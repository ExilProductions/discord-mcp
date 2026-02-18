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
