import asyncio
import re
import secrets
import time
from collections.abc import Callable
from typing import Any, Optional

import aiohttp

from discord_mcp.config import settings
from discord_mcp.discord.client import DiscordBotClient
from discord_mcp.discord.exceptions import (
    AuthenticationException,
    SessionAlreadyExistsException,
    SessionNotFoundException,
)
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class DiscordSession:
    def __init__(
        self,
        session_id: str,
        token: str,
        max_shards: int = 1,
        event_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.session_id = session_id
        self.token = token
        self.max_shards = max_shards
        self.event_callback = event_callback
        self.client: Optional[DiscordBotClient] = None
        self.task: Optional[asyncio.Task] = None
        self.created_at = time.time()
        self.last_activity = time.time()

    async def start(self) -> None:
        logger.info(
            "session_starting",
            session_id=self.session_id,
            token_prefix=self.token[:10] if self.token else "none",
        )
        self.client = DiscordBotClient(
            token=self.token,
            session_id=self.session_id,
            max_shards=self.max_shards,
            event_callback=self.event_callback,
        )
        logger.info("discord_client_created", session_id=self.session_id)
        self.task = asyncio.create_task(self.client.start_session())
        logger.info("discord_client_task_started", session_id=self.session_id)

        ready = await self.client.wait_until_ready(timeout=30.0)
        if ready:
            logger.info("bot_ready_success", session_id=self.session_id, user=str(self.client.user))
        else:
            logger.error("bot_ready_failed", session_id=self.session_id)

        self.last_activity = time.time()

    async def stop(self) -> None:
        if self.client:
            await self.client.close_session()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("session_stopped", session_id=self.session_id)

    def update_activity(self) -> None:
        self.last_activity = time.time()

    async def set_bot_status(
        self,
        activity: str = None,
        activity_type: str = "playing",
        status: str = "online",
    ) -> None:
        """Update the bot's Discord status/activity."""
        if self.client:
            if activity:
                await self.client.set_activity(
                    activity_type=activity_type, name=activity, status=status
                )
            else:
                await self.client.clear_activity()

    @property
    def is_active(self) -> bool:
        return self.client is not None and getattr(self.client, "is_ready", False)


class SessionManager:
    _instance: Optional["SessionManager"] = None

    def __new__(cls) -> "SessionManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sessions: dict[str, DiscordSession] = {}
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        token: str,
        max_shards: int = 1,
        event_callback: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> DiscordSession:
        async with self._lock:
            session_id = secrets.token_urlsafe(16)
            session = DiscordSession(
                session_id=session_id,
                token=token,
                max_shards=max_shards,
                event_callback=event_callback,
            )

            await session.start()
            self._sessions[session_id] = session
            logger.info("session_created", session_id=session_id)
            return session

    async def get_session(self, session_id: str) -> DiscordSession:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionNotFoundException(
                    f"Session {session_id} not found",
                    details={"session_id": session_id},
                )
            session.update_activity()
            return session

    async def get_session_by_token(self, token: str) -> Optional[DiscordSession]:
        async with self._lock:
            for session in self._sessions.values():
                if session.token == token:
                    session.update_activity()
                    return session
        return None

    async def remove_session(self, session_id: str) -> None:
        async with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                await session.stop()
                logger.info("session_removed", session_id=session_id)

    async def cleanup_inactive_sessions(self, timeout: int = 300) -> int:
        async with self._lock:
            current_time = time.time()
            to_remove = []

            for session_id, session in self._sessions.items():
                if current_time - session.last_activity > timeout:
                    to_remove.append(session_id)

            for session_id in to_remove:
                session = self._sessions.pop(session_id, None)
                if session:
                    await session.stop()
                    logger.info("session_cleaned_up", session_id=session_id, reason="inactive")

            return len(to_remove)

    def get_all_sessions(self) -> list[dict[str, Any]]:
        result = []
        for s in self._sessions.values():
            try:
                bot_username = None
                bot_connected = False
                bot_status = None
                bot_activity = None
                guild_count = 0
                bot_avatar_url = None
                bot_id = None

                if s.client is not None:
                    try:
                        bot_connected = s.client.user is not None
                        if s.client.user:
                            user = s.client.user
                            bot_username = str(user)
                            bot_id = str(user.id)
                            bot_status = str(user.status) if hasattr(user, "status") else None

                            if hasattr(user, "activity") and user.activity:
                                activity = user.activity
                                if hasattr(activity, "type"):
                                    activity_type = str(activity.type).split(".")[-1]
                                    bot_activity = {
                                        "type": activity_type,
                                        "name": getattr(activity, "name", None),
                                    }

                            if hasattr(user, "guilds"):
                                guild_count = len(user.guilds)

                            if hasattr(user, "avatar") and user.avatar:
                                bot_avatar_url = str(user.avatar.url)
                    except Exception:
                        pass

                result.append(
                    {
                        "session_id": s.session_id,
                        "is_active": s.is_active,
                        "created_at": s.created_at,
                        "last_activity": s.last_activity,
                        "bot_connected": bot_connected,
                        "bot_username": bot_username,
                        "bot_id": bot_id,
                        "bot_status": bot_status,
                        "bot_activity": bot_activity,
                        "guild_count": guild_count,
                        "bot_avatar_url": bot_avatar_url,
                    }
                )
            except Exception:
                result.append(
                    {
                        "session_id": s.session_id,
                        "is_active": False,
                        "created_at": s.created_at,
                        "last_activity": s.last_activity,
                        "bot_connected": False,
                        "bot_username": None,
                        "error": "Failed to serialize session",
                    }
                )
        return result


session_manager = SessionManager()
