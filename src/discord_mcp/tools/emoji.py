import base64
from typing import Any

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import EmojiException

        raise EmojiException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import EmojiException

        raise EmojiException("Resource not found", details={"original_error": str(e)})


async def create_emoji(
    guild_id: str, name: str, image_base64: str
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EmojiException

        raise EmojiException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    image_data = base64.b64decode(image_base64)

    try:
        emoji = await guild.create_custom_emoji(name=name, image=image_data)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating emoji")
    logger.info("emoji_created", guild_id=guild_id, emoji_id=str(emoji.id))

    return {
        "id": str(emoji.id),
        "name": emoji.name,
        "animated": emoji.animated,
        "url": str(emoji.url),
    }


async def delete_emoji(guild_id: str, emoji_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EmojiException

        raise EmojiException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    emoji = None
    for e in guild.emojis:
        if str(e.id) == emoji_id:
            emoji = e
            break

    if not emoji:
        from discord_mcp.discord.exceptions import EmojiException

        raise EmojiException(
            f"Emoji {emoji_id} not found", details={"emoji_id": emoji_id}
        )

    try:
        await emoji.delete()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Deleting emoji")
    logger.info("emoji_deleted", guild_id=guild_id, emoji_id=emoji_id)

    return {"success": True, "emoji_id": emoji_id, "guild_id": guild_id}


async def list_emojis(guild_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EmojiException

        raise EmojiException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    return [
        {
            "id": str(emoji.id),
            "name": emoji.name,
            "animated": emoji.animated,
            "url": str(emoji.url),
            "available": emoji.available,
        }
        for emoji in guild.emojis
    ]


async def list_stickers(guild_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EmojiException

        raise EmojiException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    return [
        {
            "id": str(sticker.id),
            "name": sticker.name,
            "description": sticker.description,
            "format": sticker.format.name if sticker.format else None,
            "url": str(sticker.url),
            "available": sticker.available,
        }
        for sticker in guild.stickers
    ]
