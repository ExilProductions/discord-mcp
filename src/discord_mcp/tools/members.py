from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import MemberException

        raise MemberException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import MemberException

        raise MemberException("Resource not found", details={"original_error": str(e)})


async def get_member_info(guild_id: str, user_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import MemberException

        raise MemberException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    member = guild.get_member(int(user_id))
    if not member:
        try:
            member = await guild.fetch_member(int(user_id))
        except discord.NotFound:
            from discord_mcp.discord.exceptions import MemberException

            raise MemberException(
                f"Member {user_id} not found", details={"user_id": user_id}
            )

    return {
        "id": str(member.id),
        "username": member.name,
        "discriminator": member.discriminator,
        "display_name": member.display_name,
        "nick": member.nick,
        "bot": member.bot,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "created_at": member.created_at.isoformat() if member.created_at else None,
        "premium_since": member.premium_since.isoformat() if member.premium_since else None,
        "roles": [
            {"id": str(role.id), "name": role.name}
            for role in member.roles
            if role.name != "@everyone"
        ],
        "top_role": {"id": str(member.top_role.id), "name": member.top_role.name},
        "avatar_url": str(member.display_avatar.url) if member.display_avatar else None,
        "status": str(member.status) if hasattr(member, "status") else None,
        "is_timed_out": member.is_timed_out(),
        "timed_out_until": member.timed_out_until.isoformat() if member.timed_out_until else None,
        "pending": member.pending,
    }


async def list_members(guild_id: str, limit: int = 100) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import MemberException

        raise MemberException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    members = []
    async for member in guild.fetch_members(limit=min(limit, 1000)):
        members.append({
            "id": str(member.id),
            "username": member.name,
            "display_name": member.display_name,
            "nick": member.nick,
            "bot": member.bot,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "top_role": {"id": str(member.top_role.id), "name": member.top_role.name},
        })

    return members


async def edit_member(
    guild_id: str,
    user_id: str,
    nickname: Optional[str] = None,
    mute: Optional[bool] = None,
    deafen: Optional[bool] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import MemberException

        raise MemberException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    member = guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import MemberException

        raise MemberException(
            f"Member {user_id} not found", details={"user_id": user_id}
        )

    kwargs: dict[str, Any] = {}
    if nickname is not None:
        kwargs["nick"] = nickname
    if mute is not None:
        kwargs["mute"] = mute
    if deafen is not None:
        kwargs["deafen"] = deafen

    try:
        await member.edit(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Editing member")
    logger.info("member_edited", guild_id=guild_id, user_id=user_id)

    return {
        "success": True,
        "guild_id": guild_id,
        "user_id": user_id,
        "changes": kwargs,
    }
