from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.friendship import UserPublic


class LiveSOSLocationUpsert(BaseModel):
    latitude: float
    longitude: float
    accuracy: float | None = None
    altitude: float | None = None
    altitude_accuracy: float | None = None
    heading: float | None = None
    speed: float | None = None
    timestamp_ms: int | None = None


class LiveSOSStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_active: bool
    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None
    altitude: float | None = None
    altitude_accuracy: float | None = None
    heading: float | None = None
    speed: float | None = None
    timestamp_ms: int | None = None
    updated_at: datetime | None = None


class LiveSOSFriendRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: UserPublic
    latitude: float
    longitude: float
    accuracy: float | None = None
    altitude: float | None = None
    altitude_accuracy: float | None = None
    heading: float | None = None
    speed: float | None = None
    timestamp_ms: int | None = None
    updated_at: datetime
