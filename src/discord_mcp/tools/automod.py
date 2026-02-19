from typing import Any, Optional

import discord

from discord_mcp.mcp.context import get_current_session, update_bot_status
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


async def _with_status(activity: str):
    await update_bot_status(activity, "playing")


def _handle_discord_error(e: discord.HTTPException) -> None:
    if isinstance(e, discord.Forbidden):
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(
            f"Permission denied: {str(e)}",
            details={"error_code": getattr(e, "code", None), "original_error": str(e)},
        )
    elif isinstance(e, discord.NotFound):
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException("Resource not found", details={"original_error": str(e)})


def _rule_to_dict(rule: discord.AutoModRule) -> dict[str, Any]:
    return {
        "id": str(rule.id),
        "guild_id": str(rule.guild.id),
        "name": rule.name,
        "enabled": rule.enabled,
        "trigger_type": rule.trigger.type.name if rule.trigger else None,
        "event_type": rule.event_type.name if rule.event_type else None,
        "actions": [
            {
                "type": action.type.name,
            }
            for action in rule.actions
        ],
        "exempt_roles": [str(r.id) for r in rule.exempt_roles] if rule.exempt_roles else [],
        "exempt_channels": [str(c.id) for c in rule.exempt_channels] if rule.exempt_channels else [],
    }


def _parse_trigger(trigger_type: str, trigger_metadata: Optional[dict[str, Any]] = None) -> discord.AutoModTrigger:
    trigger_type_lower = trigger_type.lower()

    if trigger_type_lower == "keyword":
        return discord.AutoModTrigger(
            type=discord.AutoModRuleTriggerType.keyword,
            keyword_filter=trigger_metadata.get("keyword_filter", []) if trigger_metadata else [],
            regex_patterns=trigger_metadata.get("regex_patterns", []) if trigger_metadata else [],
        )
    elif trigger_type_lower == "spam":
        return discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.spam)
    elif trigger_type_lower == "keyword_preset":
        presets = []
        if trigger_metadata:
            preset_map = {
                "profanity": discord.AutoModRuleActionType.block_message,
                "sexual_content": discord.AutoModRuleActionType.block_message,
                "slurs": discord.AutoModRuleActionType.block_message,
            }
            for preset_name in trigger_metadata.get("presets", []):
                preset_map_values = {
                    "profanity": discord.AutoModPresets.profanity,
                    "sexual_content": discord.AutoModPresets.sexual_content,
                    "slurs": discord.AutoModPresets.slurs,
                }
                preset = preset_map_values.get(preset_name.lower())
                if preset:
                    presets.append(preset)
        return discord.AutoModTrigger(
            type=discord.AutoModRuleTriggerType.keyword_preset,
            presets=presets,
        )
    elif trigger_type_lower == "mention_spam":
        mention_limit = 5
        if trigger_metadata:
            mention_limit = trigger_metadata.get("mention_total_limit", 5)
        return discord.AutoModTrigger(
            type=discord.AutoModRuleTriggerType.mention_spam,
            mention_limit=mention_limit,
        )
    else:
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(
            f"Invalid trigger_type: {trigger_type}. Must be one of: keyword, spam, keyword_preset, mention_spam",
            details={"trigger_type": trigger_type},
        )


def _parse_actions(actions: list[dict[str, Any]]) -> list[discord.AutoModRuleAction]:
    result = []
    for action_data in actions:
        action_type = action_data.get("type", "block_message").lower()
        if action_type == "block_message":
            result.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.block_message))
        elif action_type == "send_alert_message":
            channel_id = action_data.get("channel_id")
            if channel_id:
                result.append(discord.AutoModRuleAction(
                    type=discord.AutoModRuleActionType.send_alert_message,
                    channel_id=int(channel_id),
                ))
        elif action_type == "timeout":
            duration = action_data.get("duration_seconds", 60)
            result.append(discord.AutoModRuleAction(
                type=discord.AutoModRuleActionType.timeout,
                duration=duration,
            ))

    if not result:
        result.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.block_message))

    return result


async def create_automod_rule(
    guild_id: str,
    name: str,
    trigger_type: str,
    trigger_metadata: Optional[dict[str, Any]] = None,
    actions: Optional[list[dict[str, Any]]] = None,
    enabled: bool = True,
    exempt_roles: Optional[list[str]] = None,
    exempt_channels: Optional[list[str]] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    trigger = _parse_trigger(trigger_type, trigger_metadata)
    action_list = _parse_actions(actions or [{"type": "block_message"}])

    kwargs: dict[str, Any] = {
        "name": name,
        "event_type": discord.AutoModRuleEventType.message_send,
        "trigger": trigger,
        "actions": action_list,
        "enabled": enabled,
    }

    if exempt_roles:
        kwargs["exempt_roles"] = [
            guild.get_role(int(r)) for r in exempt_roles if guild.get_role(int(r))
        ]
    if exempt_channels:
        kwargs["exempt_channels"] = [
            client.get_channel(int(c)) for c in exempt_channels if client.get_channel(int(c))
        ]

    try:
        rule = await guild.create_automod_rule(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Creating automod rule")
    logger.info("automod_rule_created", guild_id=guild_id, rule_id=str(rule.id))

    return _rule_to_dict(rule)


async def edit_automod_rule(
    guild_id: str,
    rule_id: str,
    name: Optional[str] = None,
    trigger_metadata: Optional[dict[str, Any]] = None,
    actions: Optional[list[dict[str, Any]]] = None,
    enabled: Optional[bool] = None,
    exempt_roles: Optional[list[str]] = None,
    exempt_channels: Optional[list[str]] = None,
) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        rule = await guild.fetch_automod_rule(int(rule_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(
            f"AutoMod rule {rule_id} not found", details={"rule_id": rule_id}
        )

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if enabled is not None:
        kwargs["enabled"] = enabled
    if actions is not None:
        kwargs["actions"] = _parse_actions(actions)
    if exempt_roles is not None:
        kwargs["exempt_roles"] = [
            guild.get_role(int(r)) for r in exempt_roles if guild.get_role(int(r))
        ]
    if exempt_channels is not None:
        kwargs["exempt_channels"] = [
            client.get_channel(int(c)) for c in exempt_channels if client.get_channel(int(c))
        ]

    try:
        rule = await rule.edit(**kwargs)
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Editing automod rule")
    logger.info("automod_rule_edited", guild_id=guild_id, rule_id=rule_id)

    return _rule_to_dict(rule)


async def delete_automod_rule(guild_id: str, rule_id: str) -> dict[str, Any]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        rule = await guild.fetch_automod_rule(int(rule_id))
    except discord.NotFound:
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(
            f"AutoMod rule {rule_id} not found", details={"rule_id": rule_id}
        )

    try:
        await rule.delete()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    await _with_status("Deleting automod rule")
    logger.info("automod_rule_deleted", guild_id=guild_id, rule_id=rule_id)

    return {"success": True, "rule_id": rule_id, "guild_id": guild_id}


async def list_automod_rules(guild_id: str) -> list[dict[str, Any]]:
    session = await get_current_session()
    client = session.client

    if not client:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("Client not initialized")

    guild = client.get_guild(int(guild_id))
    if not guild:
        from discord_mcp.discord.exceptions import AutoModException

        raise AutoModException(f"Guild {guild_id} not found", details={"guild_id": guild_id})

    try:
        rules = await guild.fetch_automod_rules()
    except discord.HTTPException as e:
        _handle_discord_error(e)
        raise

    return [_rule_to_dict(rule) for rule in rules]
