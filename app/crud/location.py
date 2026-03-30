from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, case, or_
from sqlalchemy.orm import Session

from app.models.friendship import Friendship, FriendshipStatus
from app.models.location import UserLocation
from app.models.user import User
from app.schemas.location import FriendLocationRead


def _format_last_seen(location_updated_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    delta = now - location_updated_at
    total_seconds = max(int(delta.total_seconds()), 0)

    minutes = total_seconds // 60
    if minutes < 60:
        if minutes <= 1:
            return "1 min ago"
        return f"{minutes} mins ago"

    hours = minutes // 60
    if hours < 24:
        if hours == 1:
            return "1 hour ago"
        return f"{hours} hours ago"

    days = hours // 24
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


def upsert_user_location(
    db: Session,
    user_id: int,
    latitude: float,
    longitude: float,
    is_visible: bool | None = None,
) -> UserLocation:
    location = db.query(UserLocation).filter(UserLocation.user_id == user_id).first()
    if location is None:
        location = UserLocation(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            is_visible=True if is_visible is None else is_visible,
        )
        db.add(location)
    else:
        location.latitude = latitude
        location.longitude = longitude
        if is_visible is not None:
            location.is_visible = is_visible

    db.commit()
    db.refresh(location)
    return location


def set_location_visibility(db: Session, user_id: int, is_visible: bool) -> UserLocation | None:
    location = db.query(UserLocation).filter(UserLocation.user_id == user_id).first()
    if location is None:
        return None

    location.is_visible = is_visible
    db.commit()
    db.refresh(location)
    return location


def get_friends_locations(
    db: Session,
    user_id: int,
) -> list[FriendLocationRead]:
    friend_id_expr = case(
        (Friendship.requester_id == user_id, Friendship.addressee_id),
        else_=Friendship.requester_id,
    )

    rows = (
        db.query(
            User.id.label("friend_id"),
            User.email.label("friend_email"),
            User.name.label("friend_name"),
            UserLocation.latitude,
            UserLocation.longitude,
            UserLocation.updated_at.label("location_updated_at"),
        )
        .join(
            Friendship,
            and_(
                or_(
                    Friendship.requester_id == user_id,
                    Friendship.addressee_id == user_id,
                ),
                Friendship.status == FriendshipStatus.ACCEPTED,
                friend_id_expr == User.id,
            ),
        )
        .join(
            UserLocation,
            and_(
                UserLocation.user_id == User.id,
                UserLocation.is_visible.is_(True),
            ),
        )
        .order_by(UserLocation.updated_at.desc(), User.id.asc())
        .all()
    )

    return [
        FriendLocationRead(
            friend_id=row.friend_id,
            friend_email=row.friend_email,
            friend_name=row.friend_name,
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            location_updated_at=row.location_updated_at,
            last_seen=_format_last_seen(row.location_updated_at),
        )
        for row in rows
    ]
