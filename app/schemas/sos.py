from pydantic import BaseModel, ConfigDict


class SosCreateRequest(BaseModel):
    sos_user_id: int
    sos_contact_id: int


class SosUserRequest(BaseModel):
    user_id: int


class SosRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sos_user_id: int
    sos_contact_id: int
