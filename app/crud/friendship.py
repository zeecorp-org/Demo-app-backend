from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.user import search_users_by_name
from app.models.friendship import Friendship, FriendshipStatus
from app.models.user import User
from app.schemas.friendship import FriendshipWithUser, UserWithFriendshipStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _friendship_between(db: Session, user_a_id: int, user_b_id: int) -> Friendship | None:
    """Return a friendship row regardless of who is requester/addressee."""
    return (
        db.query(Friendship)
        .filter(
            or_(
                and_(
                    Friendship.requester_id == user_a_id,
                    Friendship.addressee_id == user_b_id,
                ),
                and_(
                    Friendship.requester_id == user_b_id,
                    Friendship.addressee_id == user_a_id,
                ),
            )
        )
        .first()
    )


# ---------------------------------------------------------------------------
# Public CRUD functions
# ---------------------------------------------------------------------------


def send_friend_request(
    db: Session, requester_id: int, addressee_id: int
) -> Friendship:
    """
    Create a PENDING friendship row.

    Raises ValueError if the relationship already exists in any form.
    """
    if requester_id == addressee_id:
        raise ValueError("A user cannot send a friend request to themselves")

    existing = _friendship_between(db, requester_id, addressee_id)
    if existing is not None:
        raise ValueError(
            f"A friendship record already exists with status '{existing.status}'"
        )

    friendship = Friendship(
        requester_id=requester_id,
        addressee_id=addressee_id,
        status=FriendshipStatus.PENDING,
    )
    db.add(friendship)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("A friendship record already exists for this pair") from None
    db.refresh(friendship)
    return friendship


def get_friendship_by_id(db: Session, friendship_id: int) -> Friendship | None:
    return db.query(Friendship).filter(Friendship.id == friendship_id).first()


def respond_to_request(
    db: Session,
    friendship_id: int,
    actor_id: int,
    action: str,
) -> Friendship:
    """
    Accept or decline a pending request.

    - ACCEPTED: updates the row status to ACCEPTED.
    - DECLINED: deletes the row entirely so the requester can send a
      new request in the future without hitting a unique-constraint error.

    Only the addressee may call this function.
    Raises ValueError on bad state or permission.
    """
    friendship = get_friendship_by_id(db, friendship_id)
    if friendship is None:
        raise ValueError("Friend request not found")
    if friendship.addressee_id != actor_id:
        raise ValueError("Only the addressee may respond to a friend request")
    if friendship.status != FriendshipStatus.PENDING:
        raise ValueError(
            f"Cannot respond to a request with status '{friendship.status}'"
        )

    if action == FriendshipStatus.DECLINED.value:
        # Remove the row so the requester can try again later.
        db.delete(friendship)
        db.commit()
        # Return the pre-deletion snapshot so the API can still respond 200.
        return friendship

    friendship.status = FriendshipStatus(action)
    db.commit()
    db.refresh(friendship)
    return friendship


def get_pending_received(db: Session, user_id: int) -> list[FriendshipWithUser]:
    """Return all PENDING requests where the given user is the addressee."""
    rows = (
        db.query(Friendship)
        .filter(
            Friendship.addressee_id == user_id,
            Friendship.status == FriendshipStatus.PENDING,
        )
        .order_by(Friendship.created_at.desc())
        .all()
    )

    return [
        FriendshipWithUser(
            friendship_id=row.id,
            status=row.status,
            created_at=row.created_at,
            friend=row.requester,
        )
        for row in rows
    ]


def get_active_friends(db: Session, user_id: int) -> list[FriendshipWithUser]:
    """Return all ACCEPTED friendships involving the given user."""
    rows = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id,
            ),
            Friendship.status == FriendshipStatus.ACCEPTED,
        )
        .order_by(Friendship.updated_at.desc())
        .all()
    )

    results: list[FriendshipWithUser] = []
    for row in rows:
        other_user = row.addressee if row.requester_id == user_id else row.requester
        results.append(
            FriendshipWithUser(
                friendship_id=row.id,
                status=row.status,
                created_at=row.created_at,
                friend=other_user,
            )
        )
    return results


def remove_friend(db: Session, friendship_id: int, actor_id: int) -> bool:
    """
    Delete a friendship row.

    Either party may remove the friendship.
    Returns True on success, False if the row was not found.
    """
    friendship = get_friendship_by_id(db, friendship_id)
    if friendship is None:
        return False
    if actor_id not in (friendship.requester_id, friendship.addressee_id):
        raise ValueError("You are not part of this friendship")

    db.delete(friendship)
    db.commit()
    return True


def search_users_with_status(
    db: Session,
    current_user_id: int,
    query: str,
) -> list[UserWithFriendshipStatus]:
    """
    Search users by name and annotate each result with the friendship
    status relative to current_user_id.
    """
    users: list[User] = search_users_by_name(db, query)

    results: list[UserWithFriendshipStatus] = []
    for user in users:
        if user.id == current_user_id:
            continue  # exclude self from results

        friendship = _friendship_between(db, current_user_id, user.id)

        results.append(
            UserWithFriendshipStatus(
                id=user.id,
                name=user.name,
                email=user.email,
                friendship_id=friendship.id if friendship else None,
                friendship_status=friendship.status if friendship else None,
                is_requester=(
                    friendship.requester_id == current_user_id if friendship else None
                ),
            )
        )
    return results
