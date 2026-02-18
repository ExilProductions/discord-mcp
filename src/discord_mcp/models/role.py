from typing import Optional

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    guild_id: str = Field(..., description="Guild ID where to create the role")
    permissions: Optional[str] = Field(None, description="Permission integer string")
    color: int = Field(0, ge=0, le=16777215)
    hoist: bool = False
    icon: Optional[str] = None
    unicode_emoji: Optional[str] = None
    mentionable: bool = False


class RoleEdit(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    permissions: Optional[str] = None
    color: Optional[int] = Field(None, ge=0, le=16777215)
    hoist: Optional[bool] = None
    icon: Optional[str] = None
    unicode_emoji: Optional[str] = None
    mentionable: Optional[bool] = None


class RoleDelete(BaseModel):
    role_id: str = Field(..., description="ID of the role to delete")
    guild_id: str = Field(..., description="Guild ID")


class RoleResponse(BaseModel):
    id: str
    name: str
    color: int
    hoist: bool
    position: int
    permissions: str
    managed: bool
    mentionable: bool


class RoleAssign(BaseModel):
    role_id: str = Field(..., description="Role ID to assign")
    user_id: str = Field(..., description="User ID to assign role to")
    guild_id: str = Field(..., description="Guild ID")


class RoleRemove(BaseModel):
    role_id: str = Field(..., description="Role ID to remove")
    user_id: str = Field(..., description="User ID to remove role from")
    guild_id: str = Field(..., description="Guild ID")
