from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from discord_mcp.tools import messages


@pytest.mark.asyncio
async def test_get_message_includes_embeds(monkeypatch):
    message = SimpleNamespace(
        id=10,
        channel=SimpleNamespace(id=20),
        content="",
        author=SimpleNamespace(id=30, name="Market Board", discriminator="0000"),
        created_at=datetime(2026, 10, 28, tzinfo=UTC),
        edited_at=None,
        tts=False,
        mention_everyone=False,
        mentions=[],
        channel_mentions=[],
        embeds=[discord.Embed(title="📊 Market Board", description="BTC $80,712.00")],
        pinned=False,
    )
    channel = SimpleNamespace(fetch_message=AsyncMock(return_value=message))
    client = SimpleNamespace(get_channel=lambda _channel_id: channel)
    monkeypatch.setattr(
        messages, "get_current_session", AsyncMock(return_value=SimpleNamespace(client=client))
    )

    result = await messages.get_message("20", "10")

    [embed] = result["embeds"]
    assert embed["title"] == "📊 Market Board"
    assert embed["description"] == "BTC $80,712.00"
