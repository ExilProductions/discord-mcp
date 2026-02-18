import contextvars

from fastmcp import FastMCP
from fastmcp.contrib.bulk_tool_caller import BulkToolCaller
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext

from discord_mcp.discord.events import event_stream_manager
from discord_mcp.discord.session import session_manager
from discord_mcp.utils.logging import get_logger

logger = get_logger(__name__)

mcp = FastMCP("Discord MCP Server")

current_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_session_id", default=None
)


async def authenticate_and_get_session(auth_header: str) -> str:
    if not auth_header:
        from discord_mcp.discord.exceptions import AuthenticationException

        raise AuthenticationException("Missing Authorization header")

    # Strip Bearer or Bot prefix if present
    token = auth_header.strip()
    if token.startswith("Bearer "):
        token = token[7:].strip()
    elif token.startswith("Bot "):
        token = token[4:].strip()

    if not token:
        from discord_mcp.discord.exceptions import AuthenticationException

        raise AuthenticationException("Empty token provided")

    logger.info("authentication_attempt", token_prefix=token[:10] + "...")

    existing_session = await session_manager.get_session_by_token(token)
    if existing_session:
        logger.info("existing_session_found", session_id=existing_session.session_id)
        return existing_session.session_id

    try:
        session = await session_manager.create_session(
            token=token,
            max_shards=1,
            event_callback=None,
        )

        stream = event_stream_manager.create_stream(session.session_id)
        await stream.start()

        bot_user = "unknown"
        if session.client and session.client.user:
            bot_user = str(session.client.user)

        logger.info(
            "authentication_success",
            session_id=session.session_id,
            bot_user=bot_user,
        )
        return session.session_id
    except Exception as e:
        logger.error("session_creation_failed", error=str(e))
        raise


class AuthMiddleware(Middleware):
    async def on_initialize(
        self,
        context: MiddlewareContext,
        call_next,
    ):
        # Start Discord bot when MCP session initializes
        request = get_http_request()
        if request:
            auth_header = request.headers.get("Authorization", "")
            if auth_header:
                try:
                    session_id = await authenticate_and_get_session(auth_header)
                    current_session_id.set(session_id)
                    logger.info("bot_started_on_session_init", session_id=session_id)
                except Exception as e:
                    logger.error("bot_start_failed_on_init", error=str(e))

        return await call_next(context)

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next,
    ):
        request = get_http_request()
        auth_header = ""
        if request:
            auth_header = request.headers.get("Authorization", "")

        if auth_header:
            try:
                session_id = await authenticate_and_get_session(auth_header)
                token_var = current_session_id.set(session_id)
                try:
                    result = await call_next(context)
                    return result
                finally:
                    current_session_id.set(None)
                    current_session_id.reset(token_var)
            except Exception as e:
                logger.error("tool_call_auth_error", error=str(e))
                raise
        else:
            return await call_next(context)


mcp.add_middleware(AuthMiddleware())

bulk_tool_caller = BulkToolCaller()
bulk_tool_caller.register_tools(mcp)


def get_current_session_id() -> str | None:
    return current_session_id.get()


async def get_current_session():
    session_id = get_current_session_id()
    if not session_id:
        from discord_mcp.discord.exceptions import SessionException

        raise SessionException("No active session context - Authorization header required")
    return await session_manager.get_session(session_id)
