import asyncio
from collections import deque
from collections.abc import Callable
from typing import Any, Optional

from discord_mcp.config import settings
from discord_mcp.discord.exceptions import EventStreamException
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class EventStream:
    def __init__(self, session_id: str, buffer_size: int = 100):
        self.session_id = session_id
        self.buffer_size = buffer_size
        self._buffer: deque[dict[str, Any]] = deque(maxlen=buffer_size)
        self._subscribers: dict[str, asyncio.Queue[Any]] = {}
        self._lock = asyncio.Lock()
        self._running = False

    async def start(self):
        self._running = True
        logger.info("event_stream_started", session_id=self.session_id)

    async def stop(self):
        self._running = False
        async with self._lock:
            for queue in self._subscribers.values():
                await queue.put(None)
            self._subscribers.clear()
        logger.info("event_stream_stopped", session_id=self.session_id)

    async def publish(self, event: dict[str, Any]):
        if not self._running:
            return

        async with self._lock:
            self._buffer.append(event)

        for subscriber_id, queue in self._subscribers.items():
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("subscriber_queue_full", subscriber_id=subscriber_id)

    def subscribe(self, subscriber_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(
            maxsize=settings.event_stream.buffer_size
        )
        self._subscribers[subscriber_id] = queue
        logger.info("subscriber_added", session_id=self.session_id, subscriber_id=subscriber_id)
        return queue

    def unsubscribe(self, subscriber_id: str) -> None:
        self._subscribers.pop(subscriber_id, None)
        logger.info("subscriber_removed", session_id=self.session_id, subscriber_id=subscriber_id)

    def get_buffer(self) -> list[dict[str, Any]]:
        return list(self._buffer)


class EventStreamManager:
    _instance: Optional["EventStreamManager"] = None

    def __new__(cls) -> "EventStreamManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._streams: dict[str, EventStream] = {}

    def create_stream(self, session_id: str) -> EventStream:
        if session_id in self._streams:
            return self._streams[session_id]

        stream = EventStream(
            session_id=session_id,
            buffer_size=settings.event_stream.buffer_size,
        )
        self._streams[session_id] = stream
        return stream

    def get_stream(self, session_id: str) -> EventStream:
        stream = self._streams.get(session_id)
        if not stream:
            raise EventStreamException(
                f"No event stream found for session {session_id}",
                details={"session_id": session_id},
            )
        return stream

    async def remove_stream(self, session_id: str):
        stream = self._streams.pop(session_id, None)
        if stream:
            await stream.stop()

    def get_all_streams(self) -> list[str]:
        return list(self._streams.keys())


event_stream_manager = EventStreamManager()
