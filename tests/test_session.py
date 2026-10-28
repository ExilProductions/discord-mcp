from types import SimpleNamespace

from discord_mcp.discord.session import session_manager


def test_get_all_sessions_counts_client_guilds(monkeypatch):
    client = SimpleNamespace(user=SimpleNamespace(id=1, avatar=None), guilds=[object(), object()])
    session = SimpleNamespace(
        session_id="s1", is_active=True, created_at=0.0, last_activity=0.0, client=client
    )
    monkeypatch.setattr(session_manager, "_sessions", {"s1": session})

    [info] = session_manager.get_all_sessions()

    assert info["bot_connected"] is True
    assert info["guild_count"] == 2
