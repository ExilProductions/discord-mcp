import contextvars
from typing import Optional

from discord_mcp.discord.session import DiscordSession, session_manager
from discord_mcp.mcp.server import get_current_session
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)

current_session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_session_id", default=None
)


class MCPSessionContext:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._session: Optional[DiscordSession] = None

    async def __aenter__(self) -> DiscordSession:
        token = current_session_id.set(self.session_id)
        try:
            self._session = await session_manager.get_session(self.session_id)
            logger.debug("mcp_context_entered", session_id=self.session_id)
            return self._session
        except Exception:
            current_session_id.reset(token)
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        current_session_id.set(None)
        logger.debug("mcp_context_exited", session_id=self.session_id)
        return False


def get_current_session_id() -> Optional[str]:
    return current_session_id.get()


async def update_bot_status(activity: str, activity_type: str = "playing") -> None:
    """Update the bot's Discord status/activity."""
    session_id = get_current_session_id()
    if session_id:
        try:
            session = await session_manager.get_session(session_id)
            await session.set_bot_status(activity=activity, activity_type=activity_type)
        except Exception:
            pass


async def clear_bot_status() -> None:
    """Clear the bot's Discord status/activity."""
    session_id = get_current_session_id()
    if session_id:
        try:
            session = await session_manager.get_session(session_id)
            await session.set_bot_status(activity=None)
        except Exception:
            pass


def with_bot_status(activity: str, activity_type: str = "playing"):
    """Decorator to update bot status during function execution."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            await update_bot_status(activity, activity_type)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                await clear_bot_status()

        return wrapper

    return decorator


__all__ = [
    "MCPSessionContext",
    "get_current_session",
    "get_current_session_id",
    "update_bot_status",
    "clear_bot_status",
    "with_bot_status",
]
