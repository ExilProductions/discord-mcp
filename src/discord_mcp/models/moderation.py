from typing import Optional

from pydantic import BaseModel, Field


class UserTimeout(BaseModel):
    user_id: str = Field(..., description="User ID to timeout")
    guild_id: str = Field(..., description="Guild ID")
    duration_seconds: int = Field(
        ..., ge=60, le=2419200, description="Duration in seconds (1 minute to 28 days)"
    )
    reason: Optional[str] = Field(None, max_length=512)


class UserRemoveTimeout(BaseModel):
    user_id: str = Field(..., description="User ID to remove timeout from")
    guild_id: str = Field(..., description="Guild ID")


class UserKick(BaseModel):
    user_id: str = Field(..., description="User ID to kick")
    guild_id: str = Field(..., description="Guild ID")
    reason: Optional[str] = Field(None, max_length=512)


class UserBan(BaseModel):
    user_id: str = Field(..., description="User ID to ban")
    guild_id: str = Field(..., description="Guild ID")
    delete_message_seconds: int = Field(
        0, ge=0, le=604800, description="Delete messages from last 7 days"
    )
    delete_message_days: Optional[int] = Field(
        None, ge=0, le=7, description="Delete messages from last N days"
    )
    reason: Optional[str] = Field(None, max_length=512)


class UserUnban(BaseModel):
    user_id: str = Field(..., description="User ID to unban")
    guild_id: str = Field(..., description="Guild ID")
    reason: Optional[str] = Field(None, max_length=512)


class RolePolicyEnforce(BaseModel):
    user_id: str = Field(..., description="User ID to enforce role policy on")
    guild_id: str = Field(..., description="Guild ID")
    required_role_ids: list[str] = Field(
        ..., min_length=1, description="List of role IDs user must have"
    )
    action: str = Field(..., description="Action to take: 'kick' or 'ban' if requirements not met")
    reason: Optional[str] = Field(None, max_length=512)


class ModerationResponse(BaseModel):
    success: bool
    action: str
    user_id: str
    guild_id: str
    details: Optional[dict[str, str]] = None
