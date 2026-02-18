from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    channel_type: Literal["text", "voice", "category", "news", "stage", "forum", "media"] = "text"
    guild_id: str = Field(..., description="Guild ID where to create the channel")
    topic: Optional[str] = Field(None, max_length=1024)
    bitrate: Optional[int] = Field(None, ge=8000, le=128000)
    user_limit: Optional[int] = Field(None, ge=0, le=99)
    position: Optional[int] = Field(None, ge=0)
    nsfw: bool = False
    rate_limit_per_user: Optional[int] = Field(None, ge=0, le=21600)
    permission_overwrites: Optional[list[dict[str, str]]] = None
    parent_id: Optional[str] = Field(None, description="Category ID to move channel to")
    rtc_region: Optional[str] = None
    video_quality_mode: Optional[Literal["auto", "full"]] = "auto"
    default_auto_archive_duration: Optional[int] = Field(None, ge=60, le=10080)
    default_thread_reaction_emoji: Optional[dict[str, str]] = None
    available_tags: Optional[list[dict[str, str]]] = None


class ChannelEdit(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    topic: Optional[str] = Field(None, max_length=1024)
    bitrate: Optional[int] = Field(None, ge=8000, le=128000)
    user_limit: Optional[int] = Field(None, ge=0, le=99)
    position: Optional[int] = Field(None, ge=0)
    nsfw: Optional[bool] = None
    rate_limit_per_user: Optional[int] = Field(None, ge=0, le=21600)
    permission_overwrites: Optional[list[dict[str, str]]] = None
    parent_id: Optional[str] = None
    rtc_region: Optional[str] = None
    video_quality_mode: Optional[Literal["auto", "full"]] = None
    default_auto_archive_duration: Optional[int] = Field(None, ge=60, le=10080)
    lock_permissions: Optional[bool] = None
    default_thread_reaction_emoji: Optional[dict[str, str]] = None


class ChannelDelete(BaseModel):
    channel_id: str = Field(..., description="ID of the channel to delete")
    guild_id: str = Field(..., description="Guild ID")


class ChannelMove(BaseModel):
    channel_id: str = Field(..., description="ID of the channel to move")
    guild_id: str = Field(..., description="Guild ID")
    position: Optional[int] = Field(None, ge=0)
    parent_id: Optional[str] = Field(None, description="Category ID to move channel to")
    lock_permissions: bool = False


class ChannelResponse(BaseModel):
    id: str
    name: str
    type: int
    guild_id: str
    position: Optional[int] = None
    topic: Optional[str] = None
    nsfw: bool = False
    parent_id: Optional[str] = None
