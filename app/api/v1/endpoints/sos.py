from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.crud.live_sos import (
    disable_live_sos,
    get_live_sos_friends,
    get_live_sos_status,
    upsert_live_sos_location,
)
from app.crud.sos_map import add_sos_friend, get_sos_friends, remove_sos_friend
from app.schemas.friendship import FriendshipWithUser
from app.schemas.live_sos import (
    LiveSOSFriendRead,
    LiveSOSLocationUpsert,
    LiveSOSStatusRead,
)
from app.schemas.sos_map import SOSFriendCreate, SOSMapRead

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[int, Depends(get_current_user_id)]


@router.get(
    "/sos/list",
    response_model=list[FriendshipWithUser],
    summary="List SOS friends",
)
def list_sos_friends(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> list[FriendshipWithUser]:
    return get_sos_friends(db, user_id=current_user_id)


@router.post(
    "/sos/add",
    response_model=SOSMapRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a friend to the SOS list",
)
def create_sos_friend(
    payload: SOSFriendCreate,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> SOSMapRead:
    try:
        sos_friend = add_sos_friend(
            db,
            user_id=current_user_id,
            friendship_id=payload.friendship_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from None

    return sos_friend


@router.delete(
    "/sos/remove/{friendship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a friend from the SOS list",
)
def delete_sos_friend(
    friendship_id: int,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> Response:
    found = remove_sos_friend(
        db,
        user_id=current_user_id,
        friendship_id=friendship_id,
    )
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOS friend not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/sos/live/me",
    response_model=LiveSOSStatusRead,
    summary="Get the current user's live SOS status",
)
def get_my_live_sos_status(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> LiveSOSStatusRead:
    return get_live_sos_status(db, user_id=current_user_id)


@router.post(
    "/sos/live",
    response_model=LiveSOSStatusRead,
    status_code=status.HTTP_200_OK,
    summary="Create or update the current user's live SOS location",
)
def create_or_update_live_sos_location(
    payload: LiveSOSLocationUpsert,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> LiveSOSStatusRead:
    return upsert_live_sos_location(db, user_id=current_user_id, payload=payload)


@router.delete(
    "/sos/live",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Turn off live SOS for the current user",
)
def turn_off_live_sos(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> Response:
    disable_live_sos(db, user_id=current_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/sos/live/friends",
    response_model=list[LiveSOSFriendRead],
    summary="List SOS friends who are currently live",
)
def list_live_sos_friends(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> list[LiveSOSFriendRead]:
    return get_live_sos_friends(db, user_id=current_user_id)
