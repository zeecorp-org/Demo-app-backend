from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.circle import (
    add_members_to_circle,
    create_circle,
    delete_circle,
    get_circle_by_id,
    get_circles_by_owner,
    get_friends_with_circle_info,
    remove_member_from_circle,
    update_circle,
)
from app.schemas.circle import (
    CircleCreate,
    CircleMapFriend,
    CircleMemberAdd,
    CircleRead,
    CircleUpdate,
)

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]

# ---------------------------------------------------------------------------
# Temporary: current_user_id is passed as a query param until auth
# middleware is wired in (mirrors friends.py pattern).
# ---------------------------------------------------------------------------
CurrentUserId = Annotated[int, Query(alias="current_user_id")]


@router.post(
    "",
    response_model=CircleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new circle",
)
def create_new_circle(
    payload: CircleCreate,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> CircleRead:
    return create_circle(
        db,
        owner_id=current_user_id,
        name=payload.name,
        color=payload.color,
        member_ids=payload.member_ids,
    )


@router.get(
    "",
    response_model=list[CircleRead],
    summary="List all circles for the current user",
)
def list_circles(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> list[CircleRead]:
    return get_circles_by_owner(db, owner_id=current_user_id)


@router.get(
    "/map-data",
    response_model=list[CircleMapFriend],
    summary="Get friend locations enriched with circle info for map",
)
def get_circle_map_data(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> list[CircleMapFriend]:
    return get_friends_with_circle_info(db, owner_id=current_user_id)


@router.get(
    "/{circle_id}",
    response_model=CircleRead,
    summary="Get a single circle by ID",
)
def get_circle(
    circle_id: int,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> CircleRead:
    circle = get_circle_by_id(db, circle_id=circle_id, owner_id=current_user_id)
    if circle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found",
        )
    return circle


@router.patch(
    "/{circle_id}",
    response_model=CircleRead,
    summary="Update a circle (name, color, or active toggle)",
)
def patch_circle(
    circle_id: int,
    payload: CircleUpdate,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> CircleRead:
    result = update_circle(
        db,
        circle_id=circle_id,
        owner_id=current_user_id,
        name=payload.name,
        color=payload.color,
        is_active=payload.is_active,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found",
        )
    return result


@router.delete(
    "/{circle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a circle",
)
def remove_circle(
    circle_id: int,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> Response:
    found = delete_circle(db, circle_id=circle_id, owner_id=current_user_id)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{circle_id}/members",
    response_model=CircleRead,
    summary="Add members to a circle",
)
def add_members(
    circle_id: int,
    payload: CircleMemberAdd,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> CircleRead:
    result = add_members_to_circle(
        db,
        circle_id=circle_id,
        owner_id=current_user_id,
        user_ids=payload.user_ids,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found",
        )
    return result


@router.delete(
    "/{circle_id}/members/{user_id}",
    response_model=CircleRead,
    summary="Remove a member from a circle",
)
def remove_member(
    circle_id: int,
    user_id: int,
    current_user_id: CurrentUserId,
    db: DbSession,
) -> CircleRead:
    result = remove_member_from_circle(
        db,
        circle_id=circle_id,
        owner_id=current_user_id,
        user_id=user_id,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found",
        )
    return result
