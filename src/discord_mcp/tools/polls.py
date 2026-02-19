from datetime import timedelta
from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import PollException

        raise PollException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import PollException

        raise PollException("Resource not found", details={"original_error": str(e)})


async def create_poll(
    channel_id: str,
    question: str,
    answers: list[str],
    duration_hours: int = 24,
    allow_multiselect: bool = False,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import PollException

        raise PollException(f"Channel {channel_id} not found", details={"channel_id": channel_id})

    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        from discord_mcp.discord.exceptions import PollException

        raise PollException(
            f"Channel {channel_id} is not a text channel",
            details={"channel_id": channel_id},
        )

    poll = discord.Poll(
        question=question,
        duration=timedelta(hours=duration_hours),
        multiple=allow_multiselect,
    )
    for answer in answers:
        poll.add_answer(text=answer)

    try:
        message = await channel.send(poll=poll)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating poll")
    logger.info("poll_created", channel_id=channel_id, message_id=str(message.id))

    return {
        "success": True,
        "message_id": str(message.id),
        "channel_id": channel_id,
        "question": question,
        "answers": answers,
        "duration_hours": duration_hours,
        "allow_multiselect": allow_multiselect,
    }


async def end_poll(channel_id: str, message_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import PollException

        raise PollException(f"Channel {channel_id} not found", details={"channel_id": channel_id})

    try:
        message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import PollException

        raise PollException(
            f"Message {message_id} not found", details={"message_id": message_id}
        )

    if not message.poll:
        from discord_mcp.discord.exceptions import PollException

        raise PollException(
            f"Message {message_id} does not contain a poll",
            details={"message_id": message_id},
        )

    try:
        await message.end_poll()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Ending poll")
    logger.info("poll_ended", channel_id=channel_id, message_id=message_id)

    return {
        "success": True,
        "message_id": message_id,
        "channel_id": channel_id,
    }


async def get_poll_results(channel_id: str, message_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import PollException

        raise PollException(f"Channel {channel_id} not found", details={"channel_id": channel_id})

    try:
        message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import PollException

        raise PollException(
            f"Message {message_id} not found", details={"message_id": message_id}
        )

    if not message.poll:
        from discord_mcp.discord.exceptions import PollException

        raise PollException(
            f"Message {message_id} does not contain a poll",
            details={"message_id": message_id},
        )

    poll = message.poll
    results = []
    for answer in poll.answers:
        results.append({
            "id": answer.id,
            "text": answer.text,
            "vote_count": answer.vote_count,
        })

    return {
        "message_id": message_id,
        "channel_id": channel_id,
        "question": poll.question,
        "answers": results,
        "allow_multiselect": poll.multiple,
        "is_finalized": poll.is_finalised(),
        "total_votes": poll.total_votes,
    }
