from typing import Any

import uvicorn

from discord_mcp.config import settings
from discord_mcp.discord.session import session_manager
from discord_mcp.mcp.context import get_current_session
from discord_mcp.mcp.server import mcp
from discord_mcp.tools import (
    assign_role,
    ban_user,
    bulk_delete_messages,
    create_channel,
    create_role,
    delete_channel,
    delete_message,
    delete_role,
    edit_channel,
    edit_guild_settings,
    edit_message,
    edit_role,
    enforce_role_policy,
    get_category_permissions,
    get_channel,
    get_channel_messages,
    get_channel_permissions,
    get_channels,
    get_guild_bans,
    get_guild_settings,
    get_member_timeout_status,
    get_message,
    get_role,
    get_roles,
    kick_user,
    move_channel,
    remove_channel_permissions,
    remove_role,
    remove_timeout,
    send_message,
    set_category_permissions,
    set_channel_permissions,
    set_role_permissions,
    timeout_user,
    unban_user,
)
from discord_mcp.utils.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@mcp.tool()
async def create_text_channel(
    name: str,
    guild_id: str,
    topic: str | None = None,
    nsfw: bool = False,
    rate_limit_per_user: int | None = None,
    position: int | None = None,
    parent_id: str | None = None,
) -> dict[str, Any]:
    return await create_channel(
        name=name,
        guild_id=guild_id,
        channel_type="text",
        topic=topic,
        nsfw=nsfw,
        rate_limit_per_user=rate_limit_per_user,
        position=position,
        parent_id=parent_id,
    )


@mcp.tool()
async def create_voice_channel(
    name: str,
    guild_id: str,
    bitrate: int | None = None,
    user_limit: int | None = None,
    position: int | None = None,
    parent_id: str | None = None,
    rtc_region: str | None = None,
) -> dict[str, Any]:
    return await create_channel(
        name=name,
        guild_id=guild_id,
        channel_type="voice",
        bitrate=bitrate,
        user_limit=user_limit,
        position=position,
        parent_id=parent_id,
        rtc_region=rtc_region,
    )


@mcp.tool()
async def create_category(
    name: str,
    guild_id: str,
    position: int | None = None,
) -> dict[str, Any]:
    return await create_channel(
        name=name,
        guild_id=guild_id,
        channel_type="category",
        position=position,
    )


@mcp.tool()
async def edit_text_channel(
    channel_id: str,
    name: str | None = None,
    topic: str | None = None,
    nsfw: bool | None = None,
    rate_limit_per_user: int | None = None,
    position: int | None = None,
    parent_id: str | None = None,
    default_auto_archive_duration: int | None = None,
) -> dict[str, Any]:
    return await edit_channel(
        channel_id=channel_id,
        name=name,
        topic=topic,
        nsfw=nsfw,
        rate_limit_per_user=rate_limit_per_user,
        position=position,
        parent_id=parent_id,
        default_auto_archive_duration=default_auto_archive_duration,
    )


@mcp.tool()
async def edit_voice_channel(
    channel_id: str,
    name: str | None = None,
    bitrate: int | None = None,
    user_limit: int | None = None,
    position: int | None = None,
    parent_id: str | None = None,
    rtc_region: str | None = None,
) -> dict[str, Any]:
    return await edit_channel(
        channel_id=channel_id,
        name=name,
        bitrate=bitrate,
        user_limit=user_limit,
        position=position,
        parent_id=parent_id,
        rtc_region=rtc_region,
    )


@mcp.tool()
async def remove_channel(channel_id: str, guild_id: str) -> dict[str, Any]:
    return await delete_channel(channel_id=channel_id, guild_id=guild_id)


@mcp.tool()
async def move_channel_to_category(
    channel_id: str,
    guild_id: str,
    parent_id: str,
    lock_permissions: bool = False,
) -> dict[str, Any]:
    return await move_channel(
        channel_id=channel_id,
        guild_id=guild_id,
        parent_id=parent_id,
        lock_permissions=lock_permissions,
    )


@mcp.tool()
async def reorder_channels(
    channel_id: str,
    guild_id: str,
    position: int,
) -> dict[str, Any]:
    return await move_channel(
        channel_id=channel_id,
        guild_id=guild_id,
        position=position,
    )


@mcp.tool()
async def list_guilds() -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client
    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guilds = []
    for guild in client.guilds:
        guilds.append(
            {
                "id": str(guild.id),
                "name": guild.name,
                "member_count": guild.member_count,
            }
        )
    return guilds


@mcp.tool()
async def list_channels(guild_id: str) -> list[dict[str, Any]]:
    return await get_channels(guild_id=guild_id)


@mcp.tool()
async def get_channel_info(channel_id: str) -> dict[str, Any]:
    return await get_channel(channel_id=channel_id)


@mcp.tool()
async def create_new_role(
    guild_id: str,
    name: str,
    color: int = 0,
    hoist: bool = False,
    mentionable: bool = False,
    permissions: str | None = None,
) -> dict[str, Any]:
    return await create_role(
        guild_id=guild_id,
        name=name,
        color=color,
        hoist=hoist,
        mentionable=mentionable,
        permissions=permissions,
    )


@mcp.tool()
async def modify_role(
    role_id: str,
    guild_id: str,
    name: str | None = None,
    color: int | None = None,
    hoist: bool | None = None,
    mentionable: bool | None = None,
    permissions: str | None = None,
) -> dict[str, Any]:
    return await edit_role(
        role_id=role_id,
        guild_id=guild_id,
        name=name,
        color=color,
        hoist=hoist,
        mentionable=mentionable,
        permissions=permissions,
    )


@mcp.tool()
async def remove_role_from_guild(role_id: str, guild_id: str) -> dict[str, Any]:
    return await delete_role(role_id=role_id, guild_id=guild_id)


@mcp.tool()
async def add_role_to_member(
    user_id: str,
    role_id: str,
    guild_id: str,
) -> dict[str, Any]:
    return await assign_role(user_id=user_id, role_id=role_id, guild_id=guild_id)


@mcp.tool()
async def remove_role_from_member(
    user_id: str,
    role_id: str,
    guild_id: str,
) -> dict[str, Any]:
    return await remove_role(user_id=user_id, role_id=role_id, guild_id=guild_id)


@mcp.tool()
async def list_roles(guild_id: str) -> list[dict[str, Any]]:
    return await get_roles(guild_id=guild_id)


@mcp.tool()
async def get_role_info(role_id: str, guild_id: str) -> dict[str, Any]:
    return await get_role(role_id=role_id, guild_id=guild_id)


@mcp.tool()
async def configure_channel_permissions(
    channel_id: str,
    target_id: str,
    target_type: str,
    allow: str | None = None,
    deny: str | None = None,
) -> dict[str, Any]:
    return await set_channel_permissions(
        channel_id=channel_id,
        target_id=target_id,
        target_type=target_type,
        allow=allow,
        deny=deny,
    )


@mcp.tool()
async def configure_category_permissions(
    category_id: str,
    target_id: str,
    target_type: str,
    allow: str | None = None,
    deny: str | None = None,
) -> dict[str, Any]:
    return await set_category_permissions(
        category_id=category_id,
        target_id=target_id,
        target_type=target_type,
        allow=allow,
        deny=deny,
    )


@mcp.tool()
async def update_role_permissions(
    role_id: str,
    guild_id: str,
    permissions: str,
) -> dict[str, Any]:
    return await set_role_permissions(
        role_id=role_id,
        guild_id=guild_id,
        permissions=permissions,
    )


@mcp.tool()
async def view_channel_permissions(channel_id: str) -> list[dict[str, Any]]:
    return await get_channel_permissions(channel_id=channel_id)


@mcp.tool()
async def view_category_permissions(category_id: str) -> list[dict[str, Any]]:
    return await get_category_permissions(category_id=category_id)


@mcp.tool()
async def clear_channel_permissions(
    channel_id: str,
    target_id: str,
    target_type: str,
) -> dict[str, Any]:
    return await remove_channel_permissions(
        channel_id=channel_id,
        target_id=target_id,
        target_type=target_type,
    )


@mcp.tool()
async def send_message_to_channel(
    channel_id: str,
    content: str,
    tts: bool = False,
) -> dict[str, Any]:
    return await send_message(
        channel_id=channel_id,
        content=content,
        tts=tts,
    )


@mcp.tool()
async def modify_message(
    channel_id: str,
    message_id: str,
    content: str | None = None,
) -> dict[str, Any]:
    return await edit_message(
        channel_id=channel_id,
        message_id=message_id,
        content=content,
    )


@mcp.tool()
async def remove_message(
    channel_id: str, message_id: str, guild_id: str | None = None
) -> dict[str, Any]:
    return await delete_message(
        channel_id=channel_id,
        message_id=message_id,
        guild_id=guild_id,
    )


@mcp.tool()
async def remove_multiple_messages(
    channel_id: str,
    messages: list[str],
    guild_id: str | None = None,
) -> dict[str, Any]:
    return await bulk_delete_messages(
        channel_id=channel_id,
        messages=messages,
        guild_id=guild_id,
    )


@mcp.tool()
async def fetch_message(channel_id: str, message_id: str) -> dict[str, Any]:
    return await get_message(channel_id=channel_id, message_id=message_id)


@mcp.tool()
async def fetch_channel_history(
    channel_id: str,
    limit: int = 50,
    before: str | None = None,
    after: str | None = None,
) -> list[dict[str, Any]]:
    return await get_channel_messages(
        channel_id=channel_id,
        limit=limit,
        before=before,
        after=after,
    )


@mcp.tool()
async def timeout_member(
    user_id: str,
    guild_id: str,
    duration_seconds: int,
    reason: str | None = None,
) -> dict[str, Any]:
    return await timeout_user(
        user_id=user_id,
        guild_id=guild_id,
        duration_seconds=duration_seconds,
        reason=reason,
    )


@mcp.tool()
async def remove_member_timeout(user_id: str, guild_id: str) -> dict[str, Any]:
    return await remove_timeout(user_id=user_id, guild_id=guild_id)


@mcp.tool()
async def kick_member(user_id: str, guild_id: str, reason: str | None = None) -> dict[str, Any]:
    return await kick_user(user_id=user_id, guild_id=guild_id, reason=reason)


@mcp.tool()
async def ban_member(
    user_id: str,
    guild_id: str,
    delete_message_seconds: int = 0,
    reason: str | None = None,
) -> dict[str, Any]:
    return await ban_user(
        user_id=user_id,
        guild_id=guild_id,
        delete_message_seconds=delete_message_seconds,
        reason=reason,
    )


@mcp.tool()
async def unban_member(user_id: str, guild_id: str, reason: str | None = None) -> dict[str, Any]:
    return await unban_user(user_id=user_id, guild_id=guild_id, reason=reason)


@mcp.tool()
async def enforce_member_role_policy(
    user_id: str,
    guild_id: str,
    required_role_ids: list[str],
    action: str,
    reason: str | None = None,
) -> dict[str, Any]:
    return await enforce_role_policy(
        user_id=user_id,
        guild_id=guild_id,
        required_role_ids=required_role_ids,
        action=action,
        reason=reason,
    )


@mcp.tool()
async def list_guild_bans(guild_id: str, limit: int = 100) -> list[dict[str, Any]]:
    return await get_guild_bans(guild_id=guild_id, limit=limit)


@mcp.tool()
async def get_guild_info(guild_id: str) -> dict[str, Any]:
    return await get_guild_settings(guild_id=guild_id)


@mcp.tool()
async def edit_guild(
    guild_id: str,
    name: str | None = None,
    description: str | None = None,
    verification_level: str | None = None,
    explicit_content_filter: str | None = None,
    default_notifications: str | None = None,
    afk_timeout: int | None = None,
    afk_channel_id: str | None = None,
    system_channel_id: str | None = None,
    rules_channel_id: str | None = None,
    public_updates_channel_id: str | None = None,
) -> dict[str, Any]:
    return await edit_guild_settings(
        guild_id=guild_id,
        name=name,
        description=description,
        verification_level=verification_level,
        explicit_content_filter=explicit_content_filter,
        default_notifications=default_notifications,
        afk_timeout=afk_timeout,
        afk_channel_id=afk_channel_id,
        system_channel_id=system_channel_id,
        rules_channel_id=rules_channel_id,
        public_updates_channel_id=public_updates_channel_id,
    )


@mcp.tool()
async def check_member_timeout_status(user_id: str, guild_id: str) -> dict[str, Any]:
    return await get_member_timeout_status(user_id=user_id, guild_id=guild_id)


@mcp.tool()
async def get_bot_status() -> dict[str, Any]:
    sessions = session_manager.get_all_sessions()
    return {
        "active_sessions": len([s for s in sessions if s["is_active"]]),
        "total_sessions": len(sessions),
        "sessions": sessions,
    }


def main():
    logger.info(
        "starting_mcp_server",
        host=settings.mcp.host,
        port=settings.mcp.port,
    )

    uvicorn.run(
        mcp.http_app(),
        host=settings.mcp.host,
        port=settings.mcp.port,
        log_level=settings.mcp.log_level.lower(),
    )


if __name__ == "__main__":
    main()
