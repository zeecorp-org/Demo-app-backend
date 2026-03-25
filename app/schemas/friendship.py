from __future__ import annotations

import enum
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Enum (mirrors the DB-level enum)
# ---------------------------------------------------------------------------


class FriendshipStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    BLOCKED = "BLOCKED"


# ---------------------------------------------------------------------------
# Nested user snapshot (safe public fields only)
# ---------------------------------------------------------------------------


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class FriendRequestCreate(BaseModel):
    """Body for POST /friends/request."""

    addressee_id: int


class FriendRequestAction(BaseModel):
    """Body for PATCH /friends/{friendship_id}/respond."""

    action: Literal["ACCEPTED", "DECLINED"]


# ---------------------------------------------------------------------------
# Response shapes
# ---------------------------------------------------------------------------


class FriendshipRead(BaseModel):
    """Full friendship row — used when the caller needs both sides."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    requester: UserPublic
    addressee: UserPublic
    status: FriendshipStatusEnum
    created_at: datetime
    updated_at: datetime


class FriendshipWithUser(BaseModel):
    """
    Flattened response — returns the *other* user's info alongside the
    friendship metadata.  Used for the active-friends and pending lists.
    """

    model_config = ConfigDict(from_attributes=True)

    friendship_id: int
    status: FriendshipStatusEnum
    created_at: datetime
    friend: UserPublic


class UserWithFriendshipStatus(BaseModel):
    """
    Search result row — user info plus the current friendship status
    toward the searching user (None if no relationship exists yet).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    friendship_id: int | None = None
    friendship_status: FriendshipStatusEnum | None = None
    is_requester: bool | None = None  # True if current user sent the request
