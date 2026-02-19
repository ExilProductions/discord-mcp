from datetime import datetime
from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import EventException

        raise EventException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import EventException

        raise EventException("Resource not found", details={"original_error": str(e)})


def _event_to_dict(event: discord.ScheduledEvent) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "guild_id": str(event.guild_id),
        "name": event.name,
        "description": event.description,
        "start_time": event.start_time.isoformat() if event.start_time else None,
        "end_time": event.end_time.isoformat() if event.end_time else None,
        "status": event.status.name if event.status else None,
        "entity_type": event.entity_type.name if event.entity_type else None,
        "channel_id": str(event.channel_id) if event.channel_id else None,
        "location": event.location,
        "user_count": event.user_count,
    }


async def create_scheduled_event(
    guild_id: str,
    name: str,
    start_time: str,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    channel_id: Optional[str] = None,
    location: Optional[str] = None,
    entity_type: str = "voice",
    privacy_level: str = "guild_only",
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    entity_type_map = {
        "stage_instance": discord.EntityType.stage_instance,
        "voice": discord.EntityType.voice,
        "external": discord.EntityType.external,
    }
    et = entity_type_map.get(entity_type.lower())
    if not et:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(
            f"Invalid entity_type: {entity_type}. Must be one of: stage_instance, voice, external",
            details={"entity_type": entity_type},
        )

    kwargs: dict[str, Any] = {
        "name": name,
        "start_time": datetime.fromisoformat(start_time),
        "entity_type": et,
        "privacy_level": discord.PrivacyLevel.guild_only,
    }

    if description:
        kwargs["description"] = description
    if end_time:
        kwargs["end_time"] = datetime.fromisoformat(end_time)
    if channel_id and et != discord.EntityType.external:
        kwargs["channel"] = client.get_channel(int(channel_id))
    if location and et == discord.EntityType.external:
        kwargs["location"] = location
        if not end_time:
            from discord_mcp.discord.exceptions import EventException

            raise EventException(
                "end_time is required for external events",
                details={"entity_type": entity_type},
            )

    try:
        event = await guild.create_scheduled_event(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating scheduled event")
    logger.info("scheduled_event_created", guild_id=guild_id, event_id=str(event.id))

    return _event_to_dict(event)


async def edit_scheduled_event(
    guild_id: str,
    event_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    status: Optional[str] = None,
    channel_id: Optional[str] = None,
    location: Optional[str] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        event = await guild.fetch_scheduled_event(int(event_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(
            f"Event {event_id} not found", details={"event_id": event_id}
        )

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if start_time is not None:
        kwargs["start_time"] = datetime.fromisoformat(start_time)
    if end_time is not None:
        kwargs["end_time"] = datetime.fromisoformat(end_time)
    if status is not None:
        status_map = {
            "scheduled": discord.EventStatus.scheduled,
            "active": discord.EventStatus.active,
            "completed": discord.EventStatus.completed,
            "cancelled": discord.EventStatus.cancelled,
        }
        kwargs["status"] = status_map.get(status.lower())
    if channel_id is not None:
        kwargs["channel"] = client.get_channel(int(channel_id))
    if location is not None:
        kwargs["location"] = location

    try:
        event = await event.edit(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Editing scheduled event")
    logger.info("scheduled_event_edited", guild_id=guild_id, event_id=event_id)

    return _event_to_dict(event)


async def delete_scheduled_event(guild_id: str, event_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        event = await guild.fetch_scheduled_event(int(event_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(
            f"Event {event_id} not found", details={"event_id": event_id}
        )

    try:
        await event.delete()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Deleting scheduled event")
    logger.info("scheduled_event_deleted", guild_id=guild_id, event_id=event_id)

    return {"success": True, "event_id": event_id, "guild_id": guild_id}


async def list_scheduled_events(guild_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        events = await guild.fetch_scheduled_events()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    return [_event_to_dict(event) for event in events]


async def get_scheduled_event_users(
    guild_id: str, event_id: str, limit: int = 100
) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        event = await guild.fetch_scheduled_event(int(event_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import EventException

        raise EventException(
            f"Event {event_id} not found", details={"event_id": event_id}
        )

    users = []
    async for user in event.users(limit=min(limit, 100)):
        users.append({
            "id": str(user.id),
            "username": user.name,
            "discriminator": user.discriminator,
        })

    return users
