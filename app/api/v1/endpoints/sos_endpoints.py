from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.sos import (
    create_sos_entry,
    delete_sos_entry,
    get_sos_contact_ids_for_user,
    get_users_who_added_sos_contact,
)
from app.schemas.sos import SosCreateRequest, SosRead, SosUserRequest

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUserId = Annotated[int, Query(alias="current_user_id")]


@router.post("/add_sos", response_model=SosRead, status_code=status.HTTP_201_CREATED)
def create_sos_contact(payload: SosCreateRequest, db: DbSession) -> SosRead:
    try:
        return create_sos_entry(
            db,
            sos_user_id=payload.sos_user_id,
            sos_contact_id=payload.sos_contact_id,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create SOS entry for the provided user ids",
        ) from None


@router.delete("/delete_sos", status_code=status.HTTP_204_NO_CONTENT)
def remove_sos_contact(payload: SosCreateRequest, db: DbSession) -> Response:
    found = delete_sos_entry(
        db,
        sos_user_id=payload.sos_user_id,
        sos_contact_id=payload.sos_contact_id,
    )
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SOS entry not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/added-me",
    response_model=list[int],
    summary="List user ids who added the current user as SOS contact",
)
def list_users_who_added_me_as_sos(
    current_user_id: CurrentUserId,
    db: DbSession,
) -> list[int]:
    return get_users_who_added_sos_contact(db, user_id=current_user_id)


@router.post(
    "/contacts",
    response_model=list[int],
    summary="List SOS contact ids for a user",
)
def list_sos_contacts_for_user(
    payload: SosUserRequest,
    db: DbSession,
) -> list[int]:
    return get_sos_contact_ids_for_user(db, user_id=payload.user_id)
