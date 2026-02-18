from typing import Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    channel_id: str = Field(..., description="Channel ID to send message to")
    content: str = Field(..., min_length=1, max_length=2000)
    tts: bool = False
    embeds: Optional[list[dict[str, str]]] = None
    allowed_mentions: Optional[dict[str, list[str]]] = None
    message_reference: Optional[dict[str, str]] = None
    components: Optional[list[dict[str, str]]] = None
    stickers: Optional[list[str]] = None
    files: Optional[list[str]] = None


class MessageEdit(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    embeds: Optional[list[dict[str, str]]] = None
    flags: Optional[int] = None
    allowed_mentions: Optional[dict[str, list[str]]] = None
    components: Optional[list[dict[str, str]]] = None


class MessageDelete(BaseModel):
    message_id: str = Field(..., description="ID of the message to delete")
    channel_id: str = Field(..., description="Channel ID where the message is")
    guild_id: Optional[str] = Field(None, description="Guild ID")


class MessageBulkDelete(BaseModel):
    channel_id: str = Field(..., description="Channel ID where messages are")
    guild_id: Optional[str] = Field(None, description="Guild ID")
    messages: list[str] = Field(
        ..., min_length=2, max_length=100, description="List of message IDs to delete"
    )


class MessageResponse(BaseModel):
    id: str
    channel_id: str
    content: str
    author: dict[str, str]
    timestamp: str
    edited_timestamp: Optional[str] = None
    tts: bool = False
    mention_everyone: bool = False
    mentions: list[str] = []
    channel_mentions: list[str] = []
    attachments: list[dict[str, str]] = []
    embeds: list[dict[str, str]] = []
    reactions: list[dict[str, str]] = []
    nonce: Optional[str] = None
    pinned: bool = False
    webhook_id: Optional[str] = None
    type: int = 0
