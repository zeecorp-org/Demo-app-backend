from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.crud.location import (
    get_friends_locations,
    set_location_visibility,
    upsert_user_location,
)
from app.schemas.location import (
    FriendLocationRead,
    LocationUpsertRequest,
    LocationVisibilityRequest,
    UserLocationRead,
)

router = APIRouter()
CurrentUserId = Annotated[int, Depends(get_current_user_id)]


@router.put(
    "/me",
    response_model=UserLocationRead,
    summary="Upsert the current user's location",
)
def upsert_my_location(
    payload: LocationUpsertRequest,
    current_user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> UserLocationRead:
    location = upsert_user_location(
        db,
        user_id=current_user_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_visible=payload.is_visible,
    )
    return location


@router.patch(
    "/me/visibility",
    response_model=UserLocationRead,
    summary="Show or hide the current user's location",
)
def update_location_visibility(
    payload: LocationVisibilityRequest,
    current_user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> UserLocationRead:
    location = set_location_visibility(
        db,
        user_id=current_user_id,
        is_visible=payload.is_visible,
    )
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found. Set your location first.",
        )
    return location


@router.get(
    "/friends",
    response_model=list[FriendLocationRead],
    summary="Get visible last-known locations for accepted friends",
)
def list_friend_locations(
    current_user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> list[FriendLocationRead]:
    return get_friends_locations(db, user_id=current_user_id)
