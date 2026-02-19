from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


async def get_audit_log(
    guild_id: str,
    user_id: Optional[str] = None,
    action_type: Optional[int] = None,
    limit: int = 50,
    before: Optional[str] = None,
) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import AuditLogException

        raise AuditLogException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    kwargs: dict[str, Any] = {"limit": min(limit, 100)}

    if user_id:
        try:
            user = await client.fetch_user(int(user_id))
            kwargs["user"] = user
        except discord.NotFound:
            from discord_mcp.discord.exceptions import AuditLogException

            raise AuditLogException(
                f"User {user_id} not found", details={"user_id": user_id}
            )

    if action_type is not None:
        try:
            kwargs["action"] = discord.AuditLogAction(action_type)
        except ValueError:
            from discord_mcp.discord.exceptions import AuditLogException

            raise AuditLogException(
                f"Invalid action_type: {action_type}",
                details={"action_type": action_type},
            )

    if before:
        kwargs["before"] = discord.Object(id=int(before))

    try:
        entries = []
        async for entry in guild.audit_logs(**kwargs):
            entry_data: dict[str, Any] = {
                "id": str(entry.id),
                "action": entry.action.name if entry.action else None,
                "user": {
                    "id": str(entry.user.id),
                    "username": entry.user.name,
                }
                if entry.user
                else None,
                "target": str(entry.target.id) if entry.target and hasattr(entry.target, "id") else str(entry.target) if entry.target else None,
                "reason": entry.reason,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }

            if entry.changes:
                changes = []
                for change in entry.changes:
                    changes.append({
                        "attribute": change.attribute,
                        "before": str(change.before) if change.before is not None else None,
                        "after": str(change.after) if change.after is not None else None,
                    })
                entry_data["changes"] = changes

            entries.append(entry_data)
    except discord.Forbidden:
        from discord_mcp.discord.exceptions import AuditLogException

        raise AuditLogException(
            "Bot lacks permission to view audit logs",
            details={"guild_id": guild_id},
        )
    except discord.HTTPException as e:
        from discord_mcp.discord.exceptions import AuditLogException

        raise AuditLogException(
            f"Failed to fetch audit logs: {str(e)}",
            details={"guild_id": guild_id, "original_error": str(e)},
        )

    return entries
