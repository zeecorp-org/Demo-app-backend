from difflib import SequenceMatcher

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id.asc()).all()


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def _get_name_similarity_score(name: str, query: str) -> float:
    normalized_name = name.strip().lower()
    normalized_query = query.strip().lower()

    if not normalized_name or not normalized_query:
        return 0

    if normalized_name == normalized_query:
        return 1_000

    score = SequenceMatcher(None, normalized_name, normalized_query).ratio() * 100

    if normalized_name.startswith(normalized_query):
        score += 200
    elif normalized_query in normalized_name:
        score += 120

    name_parts = normalized_name.split()
    query_parts = normalized_query.split()

    for query_part in query_parts:
        if any(part.startswith(query_part) for part in name_parts):
            score += 45
        elif any(query_part in part for part in name_parts):
            score += 20

    return score


def search_users_by_name(db: Session, query: str) -> list[User]:
    normalized_query = query.strip()
    if not normalized_query:
        return []

    query_parts = [part for part in normalized_query.split() if part]
    filters = [User.name.ilike(f"%{normalized_query}%")]
    filters.extend(User.name.ilike(f"%{part}%") for part in query_parts)

    users = db.query(User).filter(or_(*filters)).all()

    return sorted(
        users,
        key=lambda user: (
            -_get_name_similarity_score(user.name, normalized_query),
            user.name.lower(),
            user.id,
        ),
    )


async def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=await hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if user is None:
        return False

    db.delete(user)
    db.commit()
    return True
