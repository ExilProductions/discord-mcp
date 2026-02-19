from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import WebhookException

        raise WebhookException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import WebhookException

        raise WebhookException("Resource not found", details={"original_error": str(e)})


def _webhook_to_dict(webhook: discord.Webhook) -> dict[str, Any]:
    return {
        "id": str(webhook.id),
        "name": webhook.name,
        "channel_id": str(webhook.channel_id) if webhook.channel_id else None,
        "guild_id": str(webhook.guild_id) if webhook.guild_id else None,
        "url": webhook.url,
        "type": webhook.type.name if webhook.type else None,
    }


async def create_webhook(
    channel_id: str, name: str, reason: Optional[str] = None
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    channel = client.get_channel(int(channel_id))
    if not channel:
        from discord_mcp.discord.exceptions import WebhookException

        raise WebhookException(
            f"Channel {channel_id} not found", details={"channel_id": channel_id}
        )

    if not isinstance(channel, discord.TextChannel):
        from discord_mcp.discord.exceptions import WebhookException

        raise WebhookException(
            f"Channel {channel_id} is not a text channel",
            details={"channel_id": channel_id},
        )

    try:
        webhook = await channel.create_webhook(name=name, reason=reason)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating webhook")
    logger.info("webhook_created", webhook_id=str(webhook.id), channel_id=channel_id)

    return _webhook_to_dict(webhook)


async def send_webhook_message(
    webhook_id: str,
    content: str,
    username: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    try:
        webhook = await client.fetch_webhook(int(webhook_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import WebhookException

        raise WebhookException(
            f"Webhook {webhook_id} not found", details={"webhook_id": webhook_id}
        )

    kwargs: dict[str, Any] = {"content": content, "wait": True}
    if username:
        kwargs["username"] = username
    if avatar_url:
        kwargs["avatar_url"] = avatar_url

    try:
        message = await webhook.send(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Sending webhook message")
    logger.info("webhook_message_sent", webhook_id=webhook_id)

    return {
        "success": True,
        "message_id": str(message.id),
        "webhook_id": webhook_id,
    }


async def list_webhooks(
    guild_id: Optional[str] = None, channel_id: Optional[str] = None
) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    if channel_id:
        channel = client.get_channel(int(channel_id))
        if not channel:
            from discord_mcp.discord.exceptions import WebhookException

            raise WebhookException(
                f"Channel {channel_id} not found", details={"channel_id": channel_id}
            )
        if not isinstance(channel, discord.TextChannel):
            from discord_mcp.discord.exceptions import WebhookException

            raise WebhookException(
                f"Channel {channel_id} is not a text channel",
                details={"channel_id": channel_id},
            )
        try:
            webhooks = await channel.webhooks()
        except discord.HTTPException as e:
            _handle_discord_error(e)
            raise
    elif guild_id:
        guild = client.get_guild(int(guild_id))
        if not guild:
            from discord_mcp.discord.exceptions import WebhookException

            raise WebhookException(
                f"Guild {guild_id} not found", details={"guild_id": guild_id}
            )
        try:
            webhooks = await guild.webhooks()
        except discord.HTTPException as e:
            _handle_discord_error(e)
            raise
    else:
        from discord_mcp.discord.exceptions import WebhookException

        raise WebhookException(
            "Either guild_id or channel_id must be provided",
            details={},
        )

    return [_webhook_to_dict(w) for w in webhooks]


async def delete_webhook(webhook_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    try:
        webhook = await client.fetch_webhook(int(webhook_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import WebhookException

        raise WebhookException(
            f"Webhook {webhook_id} not found", details={"webhook_id": webhook_id}
        )

    try:
        await webhook.delete()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Deleting webhook")
    logger.info("webhook_deleted", webhook_id=webhook_id)

    return {"success": True, "webhook_id": webhook_id}
