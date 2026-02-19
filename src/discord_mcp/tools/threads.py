from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException("Resource not found", details={"original_error": str(e)})


def _thread_to_dict(thread: discord.Thread) -> dict[str, Any]:
    return {
        "id": str(thread.id),
        "name": thread.name,
        "parent_id": str(thread.parent_id) if thread.parent_id else None,
        "owner_id": str(thread.owner_id) if thread.owner_id else None,
        "archived": thread.archived,
        "locked": thread.locked,
        "auto_archive_duration": thread.auto_archive_duration,
        "slowmode_delay": thread.slowmode_delay,
        "member_count": thread.member_count,
        "message_count": thread.message_count,
        "created_at": thread.created_at.isoformat() if thread.created_at else None,
    }


async def create_thread(
    channel_id: str,
    name: str,
    message_id: Optional[str] = None,
    auto_archive_duration: int = 1440,
    slowmode_delay: Optional[int] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Channel {channel_id} not found", details={"channel_id": channel_id}
        )

    if not isinstance(channel, discord.TextChannel):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Channel {channel_id} is not a text channel",
            details={"channel_id": channel_id},
        )

    kwargs: dict[str, Any] = {
        "name": name,
        "auto_archive_duration": auto_archive_duration,
    }
    if slowmode_delay is not None:
        kwargs["slowmode_delay"] = slowmode_delay

    try:
        if message_id:
            message = await channel.fetch_message(int(message_id))
            thread = await message.create_thread(**kwargs)
        else:
            thread = await channel.create_thread(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating thread")
    logger.info("thread_created", thread_id=str(thread.id), channel_id=channel_id)

    return _thread_to_dict(thread)


async def edit_thread(
    thread_id: str,
    name: Optional[str] = None,
    archived: Optional[bool] = None,
    locked: Optional[bool] = None,
    slowmode_delay: Optional[int] = None,
    auto_archive_duration: Optional[int] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    thread = client.get_channel(int(thread_id))
    if not thread or not isinstance(thread, discord.Thread):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Thread {thread_id} not found", details={"thread_id": thread_id}
        )

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if archived is not None:
        kwargs["archived"] = archived
    if locked is not None:
        kwargs["locked"] = locked
    if slowmode_delay is not None:
        kwargs["slowmode_delay"] = slowmode_delay
    if auto_archive_duration is not None:
        kwargs["auto_archive_duration"] = auto_archive_duration

    try:
        await thread.edit(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Editing thread")
    logger.info("thread_edited", thread_id=thread_id)

    return _thread_to_dict(thread)


async def delete_thread(thread_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    thread = client.get_channel(int(thread_id))
    if not thread or not isinstance(thread, discord.Thread):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Thread {thread_id} not found", details={"thread_id": thread_id}
        )

    try:
        await thread.delete()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Deleting thread")
    logger.info("thread_deleted", thread_id=thread_id)

    return {"success": True, "thread_id": thread_id}


async def list_threads(channel_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Channel {channel_id} not found", details={"channel_id": channel_id}
        )

    if not isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Channel {channel_id} does not support threads",
            details={"channel_id": channel_id},
        )

    threads = []

    # Active threads
    for thread in channel.threads:
        threads.append(_thread_to_dict(thread))

    # Archived threads
    async for thread in channel.archived_threads(limit=100):
        threads.append(_thread_to_dict(thread))

    return threads


async def add_thread_member(thread_id: str, user_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    thread = client.get_channel(int(thread_id))
    if not thread or not isinstance(thread, discord.Thread):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Thread {thread_id} not found", details={"thread_id": thread_id}
        )

    member = thread.guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Member {user_id} not found", details={"user_id": user_id}
        )

    try:
        await thread.add_user(member)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Adding thread member")
    logger.info("thread_member_added", thread_id=thread_id, user_id=user_id)

    return {"success": True, "thread_id": thread_id, "user_id": user_id}


async def remove_thread_member(thread_id: str, user_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    thread = client.get_channel(int(thread_id))
    if not thread or not isinstance(thread, discord.Thread):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Thread {thread_id} not found", details={"thread_id": thread_id}
        )

    member = thread.guild.get_member(int(user_id))
    if not member:
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Member {user_id} not found", details={"user_id": user_id}
        )

    try:
        await thread.remove_user(member)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Removing thread member")
    logger.info("thread_member_removed", thread_id=thread_id, user_id=user_id)

    return {"success": True, "thread_id": thread_id, "user_id": user_id}


async def create_forum_post(
    channel_id: str,
    name: str,
    content: str,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Channel {channel_id} not found", details={"channel_id": channel_id}
        )

    if not isinstance(channel, discord.ForumChannel):
        from discord_mcp.discord.exceptions import ThreadException

        raise ThreadException(
            f"Channel {channel_id} is not a forum channel",
            details={"channel_id": channel_id},
        )

    applied_tags = []
    if tags:
        available_tags = {tag.name.lower(): tag for tag in channel.available_tags}
        for tag_name in tags:
            tag = available_tags.get(tag_name.lower())
            if tag:
                applied_tags.append(tag)

    try:
        thread, message = await channel.create_thread(
            name=name,
            content=content,
            applied_tags=applied_tags if applied_tags else discord.utils.MISSING,
        )
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating forum post")
    logger.info("forum_post_created", thread_id=str(thread.id), channel_id=channel_id)

    result = _thread_to_dict(thread)
    result["first_message_id"] = str(message.id)
    return result
