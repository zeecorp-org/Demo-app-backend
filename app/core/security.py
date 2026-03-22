import bcrypt
from datetime import datetime, timedelta, timezone

import jwt
from starlette.concurrency import run_in_threadpool

from app.core.config import settings


async def hash_password(password: str) -> str:
    """Return a bcrypt hash for the provided plaintext password."""
    hashed = await run_in_threadpool(
        bcrypt.hashpw,
        password.encode("utf-8"),
        bcrypt.gensalt(),
    )
    return hashed.decode("utf-8")


async def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return await run_in_threadpool(
        bcrypt.checkpw,
        password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def _create_token(subject: str, expires_in_minutes: int, token_kind: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_kind,
        "iat": now,
        "exp": now + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(subject: str) -> str:
    return _create_token(
        subject=subject,
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        token_kind="access",
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject=subject,
        expires_in_minutes=settings.jwt_refresh_token_expire_minutes,
        token_kind="refresh",
    )


def _verify_token(token: str, expected_token_kind: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc

    token_kind = payload.get("type")
    if token_kind != expected_token_kind:
        raise ValueError(f"Expected a {expected_token_kind} token")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Token subject is missing")

    return subject


def verify_access_token(token: str) -> str:
    return _verify_token(token=token, expected_token_kind="access")


def verify_refresh_token(token: str) -> str:
    return _verify_token(token=token, expected_token_kind="refresh")
