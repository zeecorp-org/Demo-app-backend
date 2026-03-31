from datetime import datetime, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.circle import Circle, CircleMember
from app.models.friendship import Friendship, FriendshipStatus
from app.models.location import UserLocation
from app.models.user import User
from app.schemas.circle import (
    CircleMapFriend,
    CircleMemberPublic,
    CircleRead,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Users whose location was updated within this many minutes count as "online".
ONLINE_THRESHOLD_MINUTES = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_online(updated_at: datetime | None) -> bool:
    """Return True if the timestamp is within the online threshold."""
    if updated_at is None:
        return False

    now = datetime.now(timezone.utc)
    # Handle timezone-naive timestamps from the DB
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    delta = (now - updated_at).total_seconds()
    return delta <= ONLINE_THRESHOLD_MINUTES * 60


def _build_circle_read(
    circle: Circle,
    db: Session,
) -> CircleRead:
    """Convert an ORM Circle to the API response shape."""
    members: list[CircleMemberPublic] = []
    online_count = 0

    for cm in circle.members:
        user: User = cm.user
        # Check location recency for online status
        loc = (
            db.query(UserLocation)
            .filter(UserLocation.user_id == user.id)
            .first()
        )
        is_online = _is_online(loc.updated_at if loc else None)
        if is_online:
            online_count += 1

        members.append(
            CircleMemberPublic(
                user_id=user.id,
                name=user.name,
                email=user.email,
                is_online=is_online,
            )
        )

    return CircleRead(
        id=circle.id,
        name=circle.name,
        color=circle.color,
        is_active=circle.is_active,
        owner_id=circle.owner_id,
        member_count=len(members),
        online_count=online_count,
        members=members,
        created_at=circle.created_at,
        updated_at=circle.updated_at,
    )


# ---------------------------------------------------------------------------
# Public CRUD functions
# ---------------------------------------------------------------------------


def create_circle(
    db: Session,
    owner_id: int,
    name: str,
    color: str,
    member_ids: list[int],
) -> CircleRead:
    """Create a circle and optionally add initial members."""
    circle = Circle(
        name=name,
        color=color,
        owner_id=owner_id,
        is_active=True,
    )
    db.add(circle)
    db.flush()  # get circle.id before adding members

    # Only add accepted friends as members
    valid_friend_ids = _get_accepted_friend_ids(db, owner_id)

    for uid in member_ids:
        if uid not in valid_friend_ids:
            continue  # silently skip non-friends
        cm = CircleMember(circle_id=circle.id, user_id=uid)
        db.add(cm)

    db.commit()
    db.refresh(circle)
    return _build_circle_read(circle, db)


def get_circles_by_owner(db: Session, owner_id: int) -> list[CircleRead]:
    """Return all circles owned by a user."""
    rows = (
        db.query(Circle)
        .filter(Circle.owner_id == owner_id)
        .order_by(Circle.created_at.desc())
        .all()
    )
    return [_build_circle_read(c, db) for c in rows]


def get_circle_by_id(
    db: Session, circle_id: int, owner_id: int
) -> CircleRead | None:
    """Return a single circle if it belongs to the owner."""
    circle = (
        db.query(Circle)
        .filter(Circle.id == circle_id, Circle.owner_id == owner_id)
        .first()
    )
    if circle is None:
        return None
    return _build_circle_read(circle, db)


def update_circle(
    db: Session,
    circle_id: int,
    owner_id: int,
    name: str | None = None,
    color: str | None = None,
    is_active: bool | None = None,
) -> CircleRead | None:
    """Update circle attributes. Returns None if not found/not owned."""
    circle = (
        db.query(Circle)
        .filter(Circle.id == circle_id, Circle.owner_id == owner_id)
        .first()
    )
    if circle is None:
        return None

    if name is not None:
        circle.name = name
    if color is not None:
        circle.color = color
    if is_active is not None:
        circle.is_active = is_active

    db.commit()
    db.refresh(circle)
    return _build_circle_read(circle, db)


def delete_circle(db: Session, circle_id: int, owner_id: int) -> bool:
    """Delete a circle. Returns False if not found/not owned."""
    circle = (
        db.query(Circle)
        .filter(Circle.id == circle_id, Circle.owner_id == owner_id)
        .first()
    )
    if circle is None:
        return False

    db.delete(circle)
    db.commit()
    return True


def add_members_to_circle(
    db: Session,
    circle_id: int,
    owner_id: int,
    user_ids: list[int],
) -> CircleRead | None:
    """Add members to a circle. Silently skips non-friends and duplicates."""
    circle = (
        db.query(Circle)
        .filter(Circle.id == circle_id, Circle.owner_id == owner_id)
        .first()
    )
    if circle is None:
        return None

    valid_friend_ids = _get_accepted_friend_ids(db, owner_id)
    existing_member_ids = {cm.user_id for cm in circle.members}

    for uid in user_ids:
        if uid not in valid_friend_ids or uid in existing_member_ids:
            continue
        cm = CircleMember(circle_id=circle.id, user_id=uid)
        db.add(cm)

    db.commit()
    db.refresh(circle)
    return _build_circle_read(circle, db)


def remove_member_from_circle(
    db: Session,
    circle_id: int,
    owner_id: int,
    user_id: int,
) -> CircleRead | None:
    """Remove a single member from a circle."""
    circle = (
        db.query(Circle)
        .filter(Circle.id == circle_id, Circle.owner_id == owner_id)
        .first()
    )
    if circle is None:
        return None

    member = (
        db.query(CircleMember)
        .filter(
            CircleMember.circle_id == circle_id,
            CircleMember.user_id == user_id,
        )
        .first()
    )
    if member is not None:
        db.delete(member)
        db.commit()
        db.refresh(circle)

    return _build_circle_read(circle, db)


def get_friends_with_circle_info(
    db: Session,
    owner_id: int,
) -> list[CircleMapFriend]:
    """
    Return friend locations enriched with the first active circle's color
    and name, for map rendering.
    """
    # Get all accepted friendships for this user
    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.requester_id == owner_id,
                Friendship.addressee_id == owner_id,
            ),
            Friendship.status == FriendshipStatus.ACCEPTED,
        )
        .all()
    )

    friend_ids: list[int] = []
    for f in friendships:
        friend_id = (
            f.addressee_id if f.requester_id == owner_id else f.requester_id
        )
        friend_ids.append(friend_id)

    if not friend_ids:
        return []

    # Get active circles owned by this user
    active_circles = (
        db.query(Circle)
        .filter(Circle.owner_id == owner_id, Circle.is_active.is_(True))
        .order_by(Circle.created_at.asc())
        .all()
    )

    # Build friend_id -> (circle_id, circle_name, circle_color) mapping
    # First active circle wins
    friend_circle_map: dict[int, tuple[int, str, str]] = {}
    for circle in active_circles:
        for cm in circle.members:
            if cm.user_id not in friend_circle_map:
                friend_circle_map[cm.user_id] = (
                    circle.id,
                    circle.name,
                    circle.color,
                )

    # Get friend locations
    locations = (
        db.query(UserLocation)
        .filter(
            UserLocation.user_id.in_(friend_ids),
            UserLocation.is_visible.is_(True),
        )
        .all()
    )

    results: list[CircleMapFriend] = []
    for loc in locations:
        user: User = loc.user
        circle_info = friend_circle_map.get(loc.user_id)
        is_online = _is_online(loc.updated_at)

        results.append(
            CircleMapFriend(
                user_id=loc.user_id,
                name=user.name,
                latitude=float(loc.latitude),
                longitude=float(loc.longitude),
                last_seen=loc.updated_at.isoformat() if loc.updated_at else "Recently",
                circle_id=circle_info[0] if circle_info else None,
                circle_name=circle_info[1] if circle_info else None,
                circle_color=circle_info[2] if circle_info else None,
                is_online=is_online,
            )
        )

    return results


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _get_accepted_friend_ids(db: Session, user_id: int) -> set[int]:
    """Return a set of user IDs that are accepted friends of the given user."""
    friendships = (
        db.query(Friendship)
        .filter(
            or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id,
            ),
            Friendship.status == FriendshipStatus.ACCEPTED,
        )
        .all()
    )

    ids: set[int] = set()
    for f in friendships:
        other_id = (
            f.addressee_id if f.requester_id == user_id else f.requester_id
        )
        ids.add(other_id)
    return ids
