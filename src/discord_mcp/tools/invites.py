from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import InviteException

        raise InviteException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import InviteException

        raise InviteException("Resource not found", details={"original_error": str(e)})


async def create_invite(
    channel_id: str,
    max_age: int = 86400,
    max_uses: int = 0,
    temporary: bool = False,
    unique: bool = True,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import InviteException

        raise InviteException(
            f"Channel {channel_id} not found", details={"channel_id": channel_id}
        )

    try:
        invite = await channel.create_invite(
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
        )
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating invite")
    logger.info("invite_created", code=invite.code, channel_id=channel_id)

    return {
        "code": invite.code,
        "url": invite.url,
        "channel_id": str(invite.channel.id) if invite.channel else None,
        "guild_id": str(invite.guild.id) if invite.guild else None,
        "max_age": invite.max_age,
        "max_uses": invite.max_uses,
        "temporary": invite.temporary,
        "uses": invite.uses,
        "created_at": invite.created_at.isoformat() if invite.created_at else None,
    }


async def list_invites(guild_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import InviteException

        raise InviteException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        invites = await guild.invites()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    return [
        {
            "code": invite.code,
            "url": invite.url,
            "channel_id": str(invite.channel.id) if invite.channel else None,
            "inviter": {
                "id": str(invite.inviter.id),
                "username": invite.inviter.name,
            }
            if invite.inviter
            else None,
            "max_age": invite.max_age,
            "max_uses": invite.max_uses,
            "temporary": invite.temporary,
            "uses": invite.uses,
            "created_at": invite.created_at.isoformat() if invite.created_at else None,
        }
        for invite in invites
    ]


async def delete_invite(invite_code: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    try:
        invite = await client.fetch_invite(invite_code)
    except discord.NotFound:
        from discord_mcp.discord.exceptions import InviteException

        raise InviteException(
            f"Invite {invite_code} not found", details={"invite_code": invite_code}
        )

    try:
        await invite.delete()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Deleting invite")
    logger.info("invite_deleted", code=invite_code)

    return {"success": True, "invite_code": invite_code}
