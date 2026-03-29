from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class LocationUpsertRequest(BaseModel):
    latitude: float
    longitude: float
    is_visible: bool | None = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if value < -90 or value > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if value < -180 or value > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return value


class LocationVisibilityRequest(BaseModel):
    is_visible: bool


class UserLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    latitude: float
    longitude: float
    is_visible: bool
    updated_at: datetime


class FriendLocationRead(BaseModel):
    friend_id: int
    friend_email: str
    friend_name: str
    latitude: float
    longitude: float
    location_updated_at: datetime
    last_seen: str
