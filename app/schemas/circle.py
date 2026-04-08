from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class CircleCreate(BaseModel):
    """Body for POST /circles."""

    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(
        default="#4F46E5",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code e.g. #4F46E5",
    )
    member_ids: list[int] = Field(default_factory=list)


class CircleUpdate(BaseModel):
    """Body for PATCH /circles/{id}."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    is_active: bool | None = None


class CircleMemberAdd(BaseModel):
    """Body for POST /circles/{id}/members."""

    user_ids: list[int] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Response shapes
# ---------------------------------------------------------------------------


class CircleMemberPublic(BaseModel):
    """A single member of a circle — safe public fields."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: str
    is_online: bool = False


class CircleRead(BaseModel):
    """Full circle response with member summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    is_active: bool
    owner_id: int
    member_count: int
    online_count: int
    members: list[CircleMemberPublic]
    created_at: datetime
    updated_at: datetime


class CircleMapFriend(BaseModel):
    """Friend location enriched with circle metadata for map rendering."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    latitude: float
    longitude: float
    last_seen: str
    circle_id: int | None = None
    circle_name: str | None = None
    circle_color: str | None = None
    is_online: bool = False
