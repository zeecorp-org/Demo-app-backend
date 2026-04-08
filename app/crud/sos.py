from sqlalchemy.orm import Session

from app.models.sos_list import SosList


def create_sos_entry(db: Session, sos_user_id: int, sos_contact_id: int) -> SosList:
    entry = SosList(
        sos_user_id=sos_user_id,
        sos_contact_id=sos_contact_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def delete_sos_entry(db: Session, sos_user_id: int, sos_contact_id: int) -> bool:
    entry = (
        db.query(SosList)
        .filter(
            SosList.sos_user_id == sos_user_id,
            SosList.sos_contact_id == sos_contact_id,
        )
        .first()
    )
    if entry is None:
        return False

    db.delete(entry)
    db.commit()
    return True


def get_users_who_added_sos_contact(db: Session, user_id: int) -> list[int]:
    return [
        sos_user_id
        for (sos_user_id,) in (
            db.query(SosList.sos_user_id)
            .filter(SosList.sos_contact_id == user_id)
            .order_by(SosList.sos_user_id.asc())
            .all()
        )
    ]


def get_sos_contact_ids_for_user(db: Session, user_id: int) -> list[int]:
    return [
        sos_contact_id
        for (sos_contact_id,) in (
            db.query(SosList.sos_contact_id)
            .filter(SosList.sos_user_id == user_id)
            .order_by(SosList.sos_contact_id.asc())
            .all()
        )
    ]
