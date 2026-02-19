from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import ReactionException

        raise ReactionException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import ReactionException

        raise ReactionException("Resource not found", details={"original_error": str(e)})


async def _get_message(client: discord.Client, channel_id: str, message_id: str) -> discord.Message:
    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ReactionException

        raise ReactionException(
            f"Channel {channel_id} not found", details={"channel_id": channel_id}
        )

    try:
        return await channel.fetch_message(int(message_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import ReactionException

        raise ReactionException(
            f"Message {message_id} not found", details={"message_id": message_id}
        )


async def add_reaction(
    channel_id: str, message_id: str, emoji: str
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    message = await _get_message(client, channel_id, message_id)

    try:
        await message.add_reaction(emoji)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Adding reaction")
    logger.info("reaction_added", channel_id=channel_id, message_id=message_id, emoji=emoji)

    return {
        "success": True,
        "channel_id": channel_id,
        "message_id": message_id,
        "emoji": emoji,
    }


async def remove_reaction(
    channel_id: str,
    message_id: str,
    emoji: str,
    user_id: Optional[str] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    message = await _get_message(client, channel_id, message_id)

    try:
        if user_id:
            member = message.guild.get_member(int(user_id)) if message.guild else None
            if member:
                await message.remove_reaction(emoji, member)
            else:
                user = await client.fetch_user(int(user_id))
                await message.remove_reaction(emoji, user)
        else:
            await message.remove_reaction(emoji, client.user)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Removing reaction")
    logger.info("reaction_removed", channel_id=channel_id, message_id=message_id, emoji=emoji)

    return {
        "success": True,
        "channel_id": channel_id,
        "message_id": message_id,
        "emoji": emoji,
        "user_id": user_id,
    }


async def get_reaction_users(
    channel_id: str,
    message_id: str,
    emoji: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    message = await _get_message(client, channel_id, message_id)

    # Find the reaction
    target_reaction = None
    for reaction in message.reactions:
        if str(reaction.emoji) == emoji:
            target_reaction = reaction
            break

    if not target_reaction:
        return []

    users = []
    async for user in target_reaction.users(limit=min(limit, 100)):
        users.append({
            "id": str(user.id),
            "username": user.name,
            "discriminator": user.discriminator,
            "bot": user.bot,
        })

    return users


async def clear_reactions(
    channel_id: str,
    message_id: str,
    emoji: Optional[str] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    message = await _get_message(client, channel_id, message_id)

    try:
        if emoji:
            await message.clear_reaction(emoji)
        else:
            await message.clear_reactions()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Clearing reactions")
    logger.info("reactions_cleared", channel_id=channel_id, message_id=message_id, emoji=emoji)

    return {
        "success": True,
        "channel_id": channel_id,
        "message_id": message_id,
        "emoji": emoji,
        "cleared_all": emoji is None,
    }
