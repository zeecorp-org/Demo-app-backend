from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SOSFriendCreate(BaseModel):
    friendship_id: int


class SOSMapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    friendship_id: int
    created_at: datetime
