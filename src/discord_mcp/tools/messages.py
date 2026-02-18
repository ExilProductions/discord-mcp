from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status, clear_bot_status
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
            from discord_mcp.discord.exceptions import MessageException

            raise MessageException(
                "Bot lacks required permissions. Please ensure the bot has the necessary permissions in Discord server settings.",
                details={"error_code": error_code, "original_error": str(e)},
            )
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Permission denied: {str(e)}",
            details={"error_code": error_code, "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            "Message not found",
            details={"original_error": str(e)},
        )


async def send_message(
    channel_id: str,
    content: str,
    tts: bool = False,
    embeds: Optional[list[dict[str, Any]]] = None,
    allowed_mentions: Optional[dict[str, list[str]]] = None,
    message_reference: Optional[dict[str, str]] = None,
    components: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    if not isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.GroupChannel)):
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} is not a text channel",
            details={"channel_id": channel_id, "type": channel.type},
        )

    embed_objects = None
    if embeds:
        embed_objects = [discord.Embed.from_dict(e) for e in embeds]

    allowed_mentions_obj = None
    if allowed_mentions:
        allowed_mentions_obj = discord.AllowedMentions(
            everyone=allowed_mentions.get("everyone", False),
            users=allowed_mentions.get("users", []),
            roles=allowed_mentions.get("roles", []),
        )

    reference = None
    if message_reference:
        reference = discord.MessageReference(
            message_id=int(message_reference.get("message_id")),
            channel_id=int(message_reference.get("channel_id", channel_id)),
            guild_id=int(message_reference.get("guild_id"))
            if message_reference.get("guild_id")
            else None,
        )

    # Components need special handling - skip for now to avoid errors
    send_kwargs: dict[str, Any] = {
        "content": content,
        "tts": tts,
        "allowed_mentions": allowed_mentions_obj,
        "reference": reference,
    }

    if embeds:
        if len(embeds) == 1:
            send_kwargs["embed"] = embed_objects[0]
        else:
            send_kwargs["embeds"] = embed_objects

    message = await channel.send(**send_kwargs)

    await update_bot_status(f"Sending message", "playing")

    logger.info("message_sent", message_id=str(message.id), channel_id=channel_id)

    return {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "content": message.content,
        "author": {
            "id": str(message.author.id),
            "username": message.author.name,
            "discriminator": message.author.discriminator,
        },
        "timestamp": message.created_at.isoformat(),
    }


async def edit_message(
    channel_id: str,
    message_id: str,
    content: Optional[str] = None,
    embeds: Optional[list[dict[str, Any]]] = None,
    flags: Optional[int] = None,
    allowed_mentions: Optional[dict[str, list[str]]] = None,
    components: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    try:
        message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Message {message_id} not found",
            details={"message_id": message_id},
        )

    embed_objects = None
    if embeds:
        embed_objects = [discord.Embed.from_dict(e) for e in embeds]

    allowed_mentions_obj = None
    if allowed_mentions:
        allowed_mentions_obj = discord.AllowedMentions(
            everyone=allowed_mentions.get("everyone", False),
            users=allowed_mentions.get("users", []),
            roles=allowed_mentions.get("roles", []),
        )

    component_objects = None
    if components:
        component_objects = [discord.Component.from_dict(c) for c in components]

    kwargs: dict[str, Any] = {}
    if content is not None:
        kwargs["content"] = content
    if embed_objects is not None:
        kwargs["embeds"] = embed_objects
    if flags is not None:
        kwargs["flags"] = discord.MessageFlags(flags)
    if allowed_mentions_obj is not None:
        kwargs["allowed_mentions"] = allowed_mentions_obj
    if component_objects is not None:
        kwargs["components"] = component_objects

    await message.edit(**kwargs)

    await _with_status(f"Editing message")
    logger.info("message_edited", message_id=message_id, channel_id=channel_id)

    return {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "content": message.content,
        "edited_timestamp": message.edited_at.isoformat() if message.edited_at else None,
    }


async def delete_message(
    channel_id: str, message_id: str, guild_id: Optional[str] = None
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    try:
        message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Message {message_id} not found",
            details={"message_id": message_id},
        )

    await message.delete()

    await _with_status(f"Deleting message")
    logger.info("message_deleted", message_id=message_id, channel_id=channel_id)

    return {
        "success": True,
        "message_id": message_id,
        "channel_id": channel_id,
    }


async def bulk_delete_messages(
    channel_id: str,
    messages: list[str],
    guild_id: Optional[str] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    if not isinstance(channel, discord.TextChannel):
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} is not a text channel",
            details={"channel_id": channel_id},
        )

    message_ids = [int(m) for m in messages]
    deleted = await channel.purge(limit=len(messages), check=lambda m: m.id in message_ids)

    await _with_status(f"Bulk deleting messages")
    logger.info("messages_bulk_deleted", count=len(deleted), channel_id=channel_id)

    return {
        "success": True,
        "deleted_count": len(deleted),
        "channel_id": channel_id,
    }


async def get_message(channel_id: str, message_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    try:
        message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Message {message_id} not found",
            details={"message_id": message_id},
        )

    return {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "content": message.content,
        "author": {
            "id": str(message.author.id),
            "username": message.author.name,
            "discriminator": message.author.discriminator,
        },
        "timestamp": message.created_at.isoformat(),
        "edited_timestamp": message.edited_at.isoformat() if message.edited_at else None,
        "tts": message.tts,
        "mention_everyone": message.mention_everyone,
        "mentions": [str(m.id) for m in message.mentions],
        "channel_mentions": [str(c.id) for c in message.channel_mentions],
        "pinned": message.pinned,
    }


async def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    before: Optional[str] = None,
    after: Optional[str] = None,
) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} not found",
            details={"channel_id": channel_id},
        )

    if not isinstance(channel, (discord.TextChannel, discord.DMChannel)):
        from discord_mcp.discord.exceptions import MessageException

        raise MessageException(
            f"Channel {channel_id} is not a text channel",
            details={"channel_id": channel_id},
        )

    before_msg = None
    after_msg = None
    if before:
        before_msg = await channel.fetch_message(int(before))
    if after:
        after_msg = await channel.fetch_message(int(after))

    messages = []
    async for message in channel.history(
        limit=min(limit, 100),
        before=before_msg,
        after=after_msg,
    ):
        messages.append(
            {
                "id": str(message.id),
                "channel_id": str(message.channel.id),
                "content": message.content,
                "author": {
                    "id": str(message.author.id),
                    "username": message.author.name,
                    "discriminator": message.author.discriminator,
                },
                "timestamp": message.created_at.isoformat(),
                "edited_timestamp": message.edited_at.isoformat() if message.edited_at else None,
                "pinned": message.pinned,
            }
        )

    return messages
