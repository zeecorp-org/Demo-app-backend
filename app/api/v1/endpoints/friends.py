from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.crud.friendship import (
    get_active_friends,
    get_pending_received,
    remove_friend,
    respond_to_request,
    search_users_with_status,
    send_friend_request,
)
from app.schemas.friendship import (
    FriendRequestAction,
    FriendRequestCreate,
    FriendshipRead,
    FriendshipWithUser,
    UserWithFriendshipStatus,
)

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[int, Depends(get_current_user_id)]


@router.post(
    "/request",
    response_model=FriendshipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Send a friend request",
)
def create_friend_request(
    payload: FriendRequestCreate,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> FriendshipRead:
    try:
        friendship = send_friend_request(
            db,
            requester_id=current_user_id,
            addressee_id=payload.addressee_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from None
    return friendship  # type: ignore[return-value]


@router.patch(
    "/{friendship_id}/respond",
    response_model=FriendshipRead,
    summary="Accept or decline a pending friend request",
)
def respond_to_friend_request(
    friendship_id: int,
    payload: FriendRequestAction,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> FriendshipRead:
    try:
        friendship = respond_to_request(
            db,
            friendship_id=friendship_id,
            actor_id=current_user_id,
            action=payload.action,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from None
    return friendship  # type: ignore[return-value]


@router.delete(
    "/{friendship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a friend or cancel a request",
)
def delete_friend(
    friendship_id: int,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> Response:
    try:
        found = remove_friend(db, friendship_id=friendship_id, actor_id=current_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from None
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Friendship not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/pending",
    response_model=list[FriendshipWithUser],
    summary="List incoming pending friend requests",
)
def list_pending_requests(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> list[FriendshipWithUser]:
    return get_pending_received(db, user_id=current_user_id)


@router.get(
    "/active",
    response_model=list[FriendshipWithUser],
    summary="List accepted friends",
)
def list_active_friends(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> list[FriendshipWithUser]:
    return get_active_friends(db, user_id=current_user_id)


@router.get(
    "/search",
    response_model=list[UserWithFriendshipStatus],
    summary="Search users and see friendship status",
)
def search_users(
    current_user_id: CurrentUserId,
    db: DbSession,
    name: Annotated[str, Query(min_length=1)],
) -> list[UserWithFriendshipStatus]:
    return search_users_with_status(db, current_user_id=current_user_id, query=name)
