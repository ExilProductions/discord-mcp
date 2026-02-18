from typing import Optional

from discord_mcp.discord.session import session_manager
from discord_mcp.discord.events import event_stream_manager
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)


class AuthHandler:
    @staticmethod
    def extract_token_from_header(authorization: Optional[str]) -> str:
        if not authorization:
            from discord_mcp.discord.exceptions import AuthenticationException

            raise AuthenticationException("Missing Authorization header")

        token = authorization.strip()
        if not token:
            from discord_mcp.discord.exceptions import AuthenticationException

            raise AuthenticationException("Empty token provided")

        return token

    @staticmethod
    async def authenticate(authorization: Optional[str]) -> str:
        token = AuthHandler.extract_token_from_header(authorization)

        logger.info("authentication_attempt", token_prefix=token[:10] + "...")

        existing_session = await session_manager.get_session_by_token(token)
        if existing_session:
            logger.info("existing_session_found", session_id=existing_session.session_id)
            return existing_session.session_id

        session = await session_manager.create_session(
            token=token,
            max_shards=1,
            event_callback=None,
        )

        stream = event_stream_manager.create_stream(session.session_id)
        await stream.start()

        logger.info("authentication_success", session_id=session.session_id)
        return session.session_id

    @staticmethod
    async def deauthenticate(session_id: str) -> None:
        await session_manager.remove_session(session_id)
        await event_stream_manager.remove_stream(session_id)
        logger.info("deauthentication_success", session_id=session_id)


auth_handler = AuthHandler()
