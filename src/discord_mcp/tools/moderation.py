from datetime import datetime, timedelta
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
            from discord_mcp.discord.exceptions import ModerationException

            raise ModerationException(
                "Bot lacks required permissions. Please ensure the bot has the necessary permissions in Discord server settings.",
                details={"error_code": error_code, "original_error": str(e)},
            )
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Permission denied: {str(e)}",
            details={"error_code": error_code, "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            "Resource not found",
            details={"original_error": str(e)},
        )


async def timeout_user(
    user_id: str,
    guild_id: str,
    duration_seconds: int,
    reason: Optional[str] = None,
) -> dict[str, Any]:
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

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Member {user_id} not found",
            details={"user_id": user_id},
        )

    until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
    try:
        await member.timeout(until, reason=reason)
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Timing out member")
    logger.info(
        "user_timed_out",
        user_id=user_id,
        guild_id=guild_id,
        duration=duration_seconds,
        reason=reason,
    )

    return {
        "success": True,
        "action": "timeout",
        "user_id": user_id,
        "guild_id": guild_id,
        "duration_seconds": duration_seconds,
        "reason": reason,
    }


async def remove_timeout(user_id: str, guild_id: str) -> dict[str, Any]:
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

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Member {user_id} not found",
            details={"user_id": user_id},
        )

    await member.timeout(None)

    await _with_status(f"Removing timeout")
    logger.info("timeout_removed", user_id=user_id, guild_id=guild_id)

    return {
        "success": True,
        "action": "remove_timeout",
        "user_id": user_id,
        "guild_id": guild_id,
    }


async def kick_user(user_id: str, guild_id: str, reason: Optional[str] = None) -> dict[str, Any]:
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

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Member {user_id} not found",
            details={"user_id": user_id},
        )

    try:
        await member.kick(reason=reason)
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Kicking member")
    logger.info("user_kicked", user_id=user_id, guild_id=guild_id, reason=reason)

    return {
        "success": True,
        "action": "kick",
        "user_id": user_id,
        "guild_id": guild_id,
        "reason": reason,
    }


async def ban_user(
    user_id: str,
    guild_id: str,
    delete_message_seconds: int = 0,
    reason: Optional[str] = None,
) -> dict[str, Any]:
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

    try:
        user = await client.fetch_user(int(user_id))
        await guild.ban(
            user=user,
            delete_message_seconds=delete_message_seconds,
            reason=reason,
        )
    except discord.NotFound:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"User {user_id} not found",
            details={"user_id": user_id},
        )
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Banning member")
    logger.info("user_banned", user_id=user_id, guild_id=guild_id, reason=reason)

    return {
        "success": True,
        "action": "ban",
        "user_id": user_id,
        "guild_id": guild_id,
        "reason": reason,
    }


async def unban_user(user_id: str, guild_id: str, reason: Optional[str] = None) -> dict[str, Any]:
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

    try:
        user = await client.fetch_user(int(user_id))
        await guild.unban(user, reason=reason)
    except discord.NotFound:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"User {user_id} is not banned",
            details={"user_id": user_id},
        )
    except discord.HTTPException as e:
        _handle_discord_error(e)

    await _with_status(f"Unbanning member")
    logger.info("user_unbanned", user_id=user_id, guild_id=guild_id, reason=reason)

    return {
        "success": True,
        "action": "unban",
        "user_id": user_id,
        "guild_id": guild_id,
        "reason": reason,
    }


async def enforce_role_policy(
    user_id: str,
    guild_id: str,
    required_role_ids: list[str],
    action: str,
    reason: Optional[str] = None,
) -> dict[str, Any]:
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

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Member {user_id} not found",
            details={"user_id": user_id},
        )

    member_role_ids = {str(r.id) for r in member.roles}
    required_set = set(required_role_ids)

    has_required = required_set.issubset(member_role_ids)

    if has_required:
        return {
            "success": True,
            "action": "policy_check_passed",
            "user_id": user_id,
            "guild_id": guild_id,
            "details": "User has all required roles",
        }

    action = action.lower()
    if action == "kick":
        await member.kick(reason=reason or "Role policy enforcement: missing required roles")
        logger.info(
            "role_policy_kick", user_id=user_id, guild_id=guild_id, required_roles=required_role_ids
        )
        return {
            "success": True,
            "action": "kick",
            "user_id": user_id,
            "guild_id": guild_id,
            "reason": reason or "Role policy enforcement: missing required roles",
            "details": "User kicked for missing required roles",
        }
    elif action == "ban":
        await guild.ban(
            user=member, reason=reason or "Role policy enforcement: missing required roles"
        )
        logger.info(
            "role_policy_ban", user_id=user_id, guild_id=guild_id, required_roles=required_role_ids
        )
        return {
            "success": True,
            "action": "ban",
            "user_id": user_id,
            "guild_id": guild_id,
            "reason": reason or "Role policy enforcement: missing required roles",
            "details": "User banned for missing required roles",
        }
    else:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Invalid action: {action}. Must be 'kick' or 'ban'",
            details={"action": action},
        )


async def get_guild_bans(guild_id: str, limit: int = 100) -> list[dict[str, Any]]:
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

    bans = []
    async for ban in guild.bans(limit=limit):
        bans.append(
            {
                "user_id": str(ban.user.id),
                "reason": ban.reason,
            }
        )

    return bans


async def get_member_timeout_status(user_id: str, guild_id: str) -> dict[str, Any]:
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

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import ModerationException

        raise ModerationException(
            f"Member {user_id} not found",
            details={"user_id": user_id},
        )

    is_timed_out = member.is_timed_out()
    timeout_until = member.timed_out_until

    return {
        "user_id": user_id,
        "guild_id": guild_id,
        "is_timed_out": is_timed_out,
        "timeout_until": timeout_until.isoformat() if timeout_until else None,
    }
