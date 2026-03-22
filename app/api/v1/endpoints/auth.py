from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_refresh_token,
)
from app.crud.user import create_user, get_user, get_user_by_email
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserRead

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, db: DbSession) -> RegisterResponse:
    try:
        user = await create_user(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from None

    subject = str(user.id)
    return RegisterResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
        user=UserRead.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not await verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    subject = str(user.id)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(payload: RefreshRequest, db: DbSession) -> AccessTokenResponse:
    try:
        subject = verify_refresh_token(payload.refresh_token)
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None

    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return AccessTokenResponse(access_token=create_access_token(str(user.id)))

