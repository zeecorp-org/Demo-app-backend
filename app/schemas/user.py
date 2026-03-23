from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(validation_alias=AliasChoices("name", "fullName", "full_name"))
    email: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name is required")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid email address")
        return normalized


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(value) > 16:
            raise ValueError("Password must be at most 16 characters long")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must include at least one letter")
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
