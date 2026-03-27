from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.friendship import get_friendship_by_id
from app.models.friendship import FriendshipStatus
from app.models.sos_map import SOSMap
from app.schemas.friendship import FriendshipWithUser


def add_sos_friend(db: Session, user_id: int, friendship_id: int) -> SOSMap:
    friendship = get_friendship_by_id(db, friendship_id)
    if friendship is None:
        raise ValueError("Friendship not found")
    if user_id not in (friendship.requester_id, friendship.addressee_id):
        raise ValueError("You are not part of this friendship")
    if friendship.status != FriendshipStatus.ACCEPTED:
        raise ValueError("Only accepted friends can be added to SOS")

    sos_map = SOSMap(user_id=user_id, friendship_id=friendship_id)
    db.add(sos_map)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("This friend is already in your SOS list") from None

    db.refresh(sos_map)
    return sos_map


def get_sos_friends(db: Session, user_id: int) -> list[FriendshipWithUser]:
    rows = (
        db.query(SOSMap)
        .filter(SOSMap.user_id == user_id)
        .order_by(SOSMap.created_at.desc())
        .all()
    )

    results: list[FriendshipWithUser] = []
    for row in rows:
        friendship = row.friendship
        if friendship.status != FriendshipStatus.ACCEPTED:
            continue
        if user_id not in (friendship.requester_id, friendship.addressee_id):
            continue

        other_user = (
            friendship.addressee
            if friendship.requester_id == user_id
            else friendship.requester
        )
        results.append(
            FriendshipWithUser(
                friendship_id=friendship.id,
                status=friendship.status,
                created_at=row.created_at,
                friend=other_user,
            )
        )

    return results


def remove_sos_friend(db: Session, user_id: int, friendship_id: int) -> bool:
    sos_map = (
        db.query(SOSMap)
        .filter(
            SOSMap.user_id == user_id,
            SOSMap.friendship_id == friendship_id,
        )
        .first()
    )

    if sos_map is None:
        return False

    db.delete(sos_map)
    db.commit()
    return True
