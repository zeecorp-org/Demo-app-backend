import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _parse_list(value: str | None, default: list[str]) -> list[str]:
    if value is None or not value.strip():
        return default

    raw = value.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return default
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return default

    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Demo App Backend"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    docs_enabled: bool = True
    api_v1_prefix: str = "/api/v1"
    allowed_origins: list[str] | None = None
    trusted_hosts: list[str] | None = None
    database_url: str = "postgresql://demouser:2g298M2fu299CWoXhNtLfhkewmliEGIv@dpg-d7aisvshg0os73b4a400-a/testdb_vsko"
    sqlalchemy_echo: bool = False
    auto_create_tables: bool = False
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_minutes: int = 60 * 24 * 7
    osrm_base_url: str = "http://osrm:5000"
    osrm_request_timeout_seconds: float = 5.0
    osrm_max_retries: int = 1
    routing_max_snap_distance_m: float = 5000.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", cls.app_name),
            app_version=os.getenv("APP_VERSION", cls.app_version),
            environment=os.getenv("ENVIRONMENT", cls.environment),
            debug=_parse_bool(os.getenv("DEBUG"), cls.debug),
            docs_enabled=_parse_bool(os.getenv("DOCS_ENABLED"), cls.docs_enabled),
            api_v1_prefix=os.getenv("API_V1_PREFIX", cls.api_v1_prefix),
            allowed_origins=_parse_list(os.getenv("ALLOWED_ORIGINS"), ["*"]),
            trusted_hosts=_parse_list(os.getenv("TRUSTED_HOSTS"), ["*"]),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            auto_create_tables=_parse_bool(
                os.getenv("AUTO_CREATE_TABLES"),
                cls.auto_create_tables,
            ),
            sqlalchemy_echo=_parse_bool(
                os.getenv("SQLALCHEMY_ECHO"),
                cls.sqlalchemy_echo,
            ),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", cls.jwt_secret_key),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", cls.jwt_algorithm),
            jwt_access_token_expire_minutes=int(
                os.getenv(
                    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
                    str(cls.jwt_access_token_expire_minutes),
                )
            ),
            jwt_refresh_token_expire_minutes=int(
                os.getenv(
                    "JWT_REFRESH_TOKEN_EXPIRE_MINUTES",
                    str(cls.jwt_refresh_token_expire_minutes),
                )
            ),
            osrm_base_url=os.getenv("OSRM_BASE_URL", cls.osrm_base_url),
            osrm_request_timeout_seconds=_parse_float(
                os.getenv("OSRM_REQUEST_TIMEOUT_SECONDS"),
                cls.osrm_request_timeout_seconds,
            ),
            osrm_max_retries=_parse_int(
                os.getenv("OSRM_MAX_RETRIES"),
                cls.osrm_max_retries,
            ),
            routing_max_snap_distance_m=_parse_float(
                os.getenv("ROUTING_MAX_SNAP_DISTANCE_M"),
                cls.routing_max_snap_distance_m,
            ),
        )


@lru_cache
def get_settings() -> Settings:
    _load_dotenv()
    return Settings.from_env()


settings = get_settings()
