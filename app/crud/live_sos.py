from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.live_sos_location import LiveSOSLocation
from app.models.friendship import FriendshipStatus
from app.models.sos_map import SOSMap
from app.schemas.live_sos import LiveSOSFriendRead, LiveSOSLocationUpsert, LiveSOSStatusRead

LIVE_SOS_STALE_AFTER_SECONDS = 8


def _is_live_sos_recent(live_sos: LiveSOSLocation) -> bool:
    if not live_sos.is_active or live_sos.updated_at is None:
        return False

    updated_at = live_sos.updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) - updated_at <= timedelta(
        seconds=LIVE_SOS_STALE_AFTER_SECONDS
    )


def _build_live_sos_status(live_sos: LiveSOSLocation) -> LiveSOSStatusRead:
    return LiveSOSStatusRead(
        is_active=live_sos.is_active,
        latitude=live_sos.latitude,
        longitude=live_sos.longitude,
        accuracy=live_sos.accuracy,
        altitude=live_sos.altitude,
        altitude_accuracy=live_sos.altitude_accuracy,
        heading=live_sos.heading,
        speed=live_sos.speed,
        timestamp_ms=live_sos.timestamp_ms,
        updated_at=live_sos.updated_at,
    )


def get_live_sos_status(db: Session, user_id: int) -> LiveSOSStatusRead:
    live_sos = (
        db.query(LiveSOSLocation)
        .filter(LiveSOSLocation.user_id == user_id)
        .first()
    )

    if live_sos is None:
        return LiveSOSStatusRead(is_active=False)

    if not _is_live_sos_recent(live_sos):
        db.delete(live_sos)
        db.commit()
        return LiveSOSStatusRead(is_active=False)

    return _build_live_sos_status(live_sos)


def upsert_live_sos_location(
    db: Session,
    user_id: int,
    payload: LiveSOSLocationUpsert,
) -> LiveSOSStatusRead:
    live_sos = (
        db.query(LiveSOSLocation)
        .filter(LiveSOSLocation.user_id == user_id)
        .first()
    )

    if live_sos is None:
        live_sos = LiveSOSLocation(user_id=user_id)
        db.add(live_sos)

    live_sos.is_active = True
    live_sos.latitude = payload.latitude
    live_sos.longitude = payload.longitude
    live_sos.accuracy = payload.accuracy
    live_sos.altitude = payload.altitude
    live_sos.altitude_accuracy = payload.altitude_accuracy
    live_sos.heading = payload.heading
    live_sos.speed = payload.speed
    live_sos.timestamp_ms = payload.timestamp_ms

    db.commit()
    db.refresh(live_sos)

    return _build_live_sos_status(live_sos)


def disable_live_sos(db: Session, user_id: int) -> bool:
    live_sos = (
        db.query(LiveSOSLocation)
        .filter(LiveSOSLocation.user_id == user_id)
        .first()
    )

    if live_sos is None:
        return False

    db.delete(live_sos)
    db.commit()
    return True


def get_live_sos_friends(db: Session, user_id: int) -> list[LiveSOSFriendRead]:
    sos_rows = (
        db.query(SOSMap)
        .order_by(SOSMap.created_at.desc())
        .all()
    )

    results: list[LiveSOSFriendRead] = []
    seen_user_ids: set[int] = set()
    for row in sos_rows:
        friendship = row.friendship
        if friendship.status != FriendshipStatus.ACCEPTED:
            continue

        if row.user_id == friendship.requester_id:
            target_user_id = friendship.addressee_id
        elif row.user_id == friendship.addressee_id:
            target_user_id = friendship.requester_id
        else:
            continue

        if target_user_id != user_id:
            continue

        live_user = row.user
        if live_user.id in seen_user_ids:
            continue
        live_sos = (
            db.query(LiveSOSLocation)
            .filter(
                LiveSOSLocation.user_id == live_user.id,
                LiveSOSLocation.is_active.is_(True),
            )
            .first()
        )
        if (
            live_sos is None
            or not _is_live_sos_recent(live_sos)
            or live_sos.latitude is None
            or live_sos.longitude is None
        ):
            continue

        seen_user_ids.add(live_user.id)
        results.append(
            LiveSOSFriendRead(
                user=live_user,
                latitude=live_sos.latitude,
                longitude=live_sos.longitude,
                accuracy=live_sos.accuracy,
                altitude=live_sos.altitude,
                altitude_accuracy=live_sos.altitude_accuracy,
                heading=live_sos.heading,
                speed=live_sos.speed,
                timestamp_ms=live_sos.timestamp_ms,
                updated_at=live_sos.updated_at,
            )
        )

    return results
