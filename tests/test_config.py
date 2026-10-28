from discord_mcp.config import MCPSettings


def test_mcp_settings_read_prefixed_env(monkeypatch):
    monkeypatch.setenv("MCP_PORT", "9999")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")

    mcp_settings = MCPSettings(_env_file=None)

    assert mcp_settings.port == 9999
    assert mcp_settings.host == "0.0.0.0"


def test_mcp_settings_ignore_unprefixed_env(monkeypatch):
    monkeypatch.setenv("PORT", "1234")

    assert MCPSettings(_env_file=None).port == 8000
