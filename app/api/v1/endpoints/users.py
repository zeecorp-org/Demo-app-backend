from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.user import create_user, delete_user, get_user, list_users
from app.schemas.user import UserCreate, UserRead

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_model=list[UserRead])
async def get_users(db: DbSession) -> list[UserRead]:
    return list_users(db)


@router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(user_id: int, db: DbSession) -> UserRead:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(payload: UserCreate, db: DbSession) -> UserRead:
    try:
        return await create_user(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(user_id: int, db: DbSession) -> Response:
    if not delete_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
