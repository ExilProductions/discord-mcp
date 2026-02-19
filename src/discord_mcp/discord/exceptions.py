from typing import Any


class DiscordMCPException(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationException(DiscordMCPException):
    pass


class SessionException(DiscordMCPException):
    pass


class SessionNotFoundException(SessionException):
    pass


class SessionAlreadyExistsException(SessionException):
    pass


class DiscordAPIException(DiscordMCPException):
    def __init__(self, message: str, status_code: int | None = None, **kwargs: Any):
        self.status_code = status_code
        super().__init__(message, **kwargs)


class ChannelException(DiscordMCPException):
    pass


class RoleException(DiscordMCPException):
    pass


class MessageException(DiscordMCPException):
    pass


class PermissionException(DiscordMCPException):
    pass


class ModerationException(DiscordMCPException):
    pass


class ValidationException(DiscordMCPException):
    def __init__(self, errors: list[dict[str, Any]], message: str = "Validation failed"):
        self.errors = errors
        super().__init__(message, details={"errors": errors})


class EventStreamException(DiscordMCPException):
    pass


class PollException(DiscordMCPException):
    pass


class EventException(DiscordMCPException):
    pass


class ThreadException(DiscordMCPException):
    pass


class WebhookException(DiscordMCPException):
    pass


class InviteException(DiscordMCPException):
    pass


class EmojiException(DiscordMCPException):
    pass


class ReactionException(DiscordMCPException):
    pass


class AutoModException(DiscordMCPException):
    pass


class AuditLogException(DiscordMCPException):
    pass


class MemberException(DiscordMCPException):
    pass
