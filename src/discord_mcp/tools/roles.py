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
            from discord_mcp.discord.exceptions import RoleException

            raise RoleException(
                "Bot lacks required permissions. Please ensure the bot has the necessary permissions in Discord server settings.",
                details={"error_code": error_code, "original_error": str(e)},
            )
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Permission denied: {str(e)}",
            details={"error_code": error_code, "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            "Resource not found",
            details={"original_error": str(e)},
        )


async def create_role(
    guild_id: str,
    name: str,
    permissions: Optional[str] = None,
    color: int = 0,
    hoist: bool = False,
    icon: Optional[str] = None,
    unicode_emoji: Optional[str] = None,
    mentionable: bool = False,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    perms = discord.Permissions(int(permissions)) if permissions else discord.Permissions()

    kwargs: dict[str, Any] = {
        "name": name,
        "permissions": perms,
        "color": discord.Color(color),
        "hoist": hoist,
        "mentionable": mentionable,
    }

    # Icon should be bytes, not string - skip if string provided
    if icon and isinstance(icon, bytes):
        kwargs["icon"] = icon
    elif icon:
        logger.warning("icon_must_be_bytes", icon_type=type(icon))

    role = await guild.create_role(**kwargs)

    await _with_status(f"Creating role: {name}")
    logger.info("role_created", role_id=str(role.id), name=name, guild_id=guild_id)

    return {
        "id": str(role.id),
        "name": role.name,
        "color": role.color.value,
        "hoist": role.hoist,
        "position": role.position,
        "permissions": str(role.permissions.value),
        "managed": role.managed,
        "mentionable": role.mentionable,
    }


async def edit_role(
    role_id: str,
    guild_id: str,
    name: Optional[str] = None,
    permissions: Optional[str] = None,
    color: Optional[int] = None,
    hoist: Optional[bool] = None,
    icon: Optional[str] = None,
    unicode_emoji: Optional[str] = None,
    mentionable: Optional[bool] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    role = guild.get_role(int(role_id))
    if not role:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Role {role_id} not found",
            details={"role_id": role_id},
        )

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if permissions is not None:
        kwargs["permissions"] = discord.Permissions(int(permissions))
    if color is not None:
        kwargs["color"] = discord.Color(color)
    if hoist is not None:
        kwargs["hoist"] = hoist
    if mentionable is not None:
        kwargs["mentionable"] = mentionable
    if icon is not None and isinstance(icon, bytes):
        kwargs["icon"] = icon

    await role.edit(**kwargs)

    await _with_status(f"Editing role")
    logger.info("role_edited", role_id=role_id, guild_id=guild_id)

    return {
        "id": str(role.id),
        "name": role.name,
        "color": role.color.value,
        "hoist": role.hoist,
        "position": role.position,
        "permissions": str(role.permissions.value),
        "managed": role.managed,
        "mentionable": role.mentionable,
    }


async def delete_role(role_id: str, guild_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    role = guild.get_role(int(role_id))
    if not role:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Role {role_id} not found",
            details={"role_id": role_id},
        )

    role_name = role.name
    await role.delete()

    await _with_status(f"Deleting role")
    logger.info("role_deleted", role_id=role_id, name=role_name, guild_id=guild_id)

    return {
        "success": True,
        "role_id": role_id,
        "name": role_name,
        "guild_id": guild_id,
    }


async def assign_role(user_id: str, role_id: str, guild_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Member {user_id} not found",
            details={"user_id": user_id},
        )

    role = guild.get_role(int(role_id))
    if not role:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Role {role_id} not found",
            details={"role_id": role_id},
        )

    try:
        await member.add_roles(role)
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Adding role to member")
    logger.info("role_assigned", user_id=user_id, role_id=role_id, guild_id=guild_id)

    return {
        "success": True,
        "user_id": user_id,
        "role_id": role_id,
        "guild_id": guild_id,
    }


async def remove_role(user_id: str, role_id: str, guild_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Member {user_id} not found",
            details={"user_id": user_id},
        )

    role = guild.get_role(int(role_id))
    if not role:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Role {role_id} not found",
            details={"role_id": role_id},
        )

    try:
        await member.remove_roles(role)
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Removing role from member")
    logger.info("role_removed", user_id=user_id, role_id=role_id, guild_id=guild_id)

    return {
        "success": True,
        "user_id": user_id,
        "role_id": role_id,
        "guild_id": guild_id,
    }


async def get_roles(guild_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    roles = []
    for role in guild.roles:
        roles.append(
            {
                "id": str(role.id),
                "name": role.name,
                "color": role.color.value,
                "hoist": role.hoist,
                "position": role.position,
                "permissions": str(role.permissions.value),
                "managed": role.managed,
                "mentionable": role.mentionable,
            }
        )

    return roles


async def get_role(role_id: str, guild_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Guild {guild_id} not found",
            details={"guild_id": guild_id},
        )

    role = guild.get_role(int(role_id))
    if not role:
        from discord_mcp.discord.exceptions import RoleException

        raise RoleException(
            f"Role {role_id} not found",
            details={"role_id": role_id},
        )

    return {
        "id": str(role.id),
        "name": role.name,
        "color": role.color.value,
        "hoist": role.hoist,
        "position": role.position,
        "permissions": str(role.permissions.value),
        "managed": role.managed,
        "mentionable": role.mentionable,
    }
