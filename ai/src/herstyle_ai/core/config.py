"""Validated environment-backed settings for the API runtime."""

from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _non_negative_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc

    if value < 0:
        raise RuntimeError(f"{name} must not be negative")
    return value


def _bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean")


def _csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    values = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    if not values:
        raise RuntimeError(f"{name} must contain at least one value")
    return values


def _secret_is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        len(value) < 32
        or normalized in {"change-me", "changeme", "secret", "password"}
        or "change-me" in normalized
        or "set_a_strong" in normalized
        or "example" in normalized
        or normalized.startswith("<")
        or normalized.endswith(">")
    )


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings required by authentication and deployment hardening."""

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    app_env: str = "development"
    frontend_origins: tuple[str, ...] = ()
    trusted_hosts: tuple[str, ...] = ()
    enable_api_docs: bool = True
    log_level: str = "INFO"
    public_base_url: str | None = None
    password_reset_url: str = "http://localhost:3000/reset-password"
    password_reset_delivery: str = "token"
    password_reset_token_expire_minutes: int = 30
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_starttls: bool = True
    refresh_cookie_name: str = "herstyleai_refresh"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: str = "lax"
    refresh_cookie_domain: str | None = None
    refresh_cookie_path: str = "/api/v1/auth"
    refresh_token_mode: str = "cookie"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_connect_timeout: int = 10
    db_ssl_mode: str = "disable"
    storage_backend: str = "local"
    storage_root: str | None = None
    max_upload_bytes: int = 10 * 1024 * 1024
    login_rate_limit: int = 10
    register_rate_limit: int = 5
    refresh_rate_limit: int = 30
    password_reset_rate_limit: int = 5
    ai_rate_limit: int = 20
    rate_limit_window_seconds: int = 60

    @classmethod
    def from_env(cls) -> "Settings":
        app_env = os.getenv("APP_ENV", "development").strip().lower()
        if app_env not in {"development", "test", "staging", "production"}:
            raise RuntimeError(
                "APP_ENV must be one of development, test, staging, production"
            )
        is_production = app_env == "production"

        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise RuntimeError("DATABASE_URL must be set")
        if "<" in database_url or ">" in database_url:
            raise RuntimeError("DATABASE_URL contains an unresolved placeholder")
        if is_production and any(
            local_host in database_url.lower()
            for local_host in ("localhost", "127.0.0.1", "[::1]")
        ):
            raise RuntimeError(
                "Production DATABASE_URL must target a managed/non-local database"
            )

        db_ssl_mode = os.getenv(
            "DB_SSL_MODE",
            "require" if is_production else "disable",
        ).strip().lower()
        if db_ssl_mode not in {"disable", "require", "verify-ca", "verify-full"}:
            raise RuntimeError(
                "DB_SSL_MODE must be disable, require, verify-ca, or verify-full"
            )
        url_ssl_mode = parse_qs(urlsplit(database_url).query).get("sslmode", [None])[-1]
        effective_ssl_mode = (url_ssl_mode or db_ssl_mode).strip().lower()
        if effective_ssl_mode not in {
            "disable",
            "require",
            "verify-ca",
            "verify-full",
        }:
            raise RuntimeError(
                "DATABASE_URL sslmode must be disable, require, verify-ca, or verify-full"
            )
        if is_production and effective_ssl_mode == "disable":
            raise RuntimeError("Production PostgreSQL connections must use TLS")

        jwt_secret_key = os.getenv("JWT_SECRET_KEY", "").strip()
        if not jwt_secret_key:
            raise RuntimeError("JWT_SECRET_KEY must be set")
        if _secret_is_placeholder(jwt_secret_key):
            raise RuntimeError("JWT_SECRET_KEY must be a strong non-placeholder secret")

        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256").strip().upper()
        if jwt_algorithm not in {"HS256", "HS384", "HS512"}:
            raise RuntimeError("JWT_ALGORITHM must be HS256, HS384, or HS512")

        origins_raw = os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN")
        if origins_raw:
            frontend_origins = tuple(
                item.strip() for item in origins_raw.split(",") if item.strip()
            )
        elif is_production:
            raise RuntimeError("FRONTEND_ORIGINS must be set in production")
        else:
            frontend_origins = (
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            )
        if is_production and "*" in frontend_origins:
            raise RuntimeError("Wildcard CORS origin is forbidden in production")

        trusted_hosts = _csv(
            "TRUSTED_HOSTS",
            ("localhost", "127.0.0.1", "testserver"),
        )
        if is_production and "*" in trusted_hosts:
            raise RuntimeError("Wildcard trusted host is forbidden in production")

        public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip() or None
        password_reset_delivery = os.getenv(
            "PASSWORD_RESET_DELIVERY",
            "email" if is_production else "token",
        ).strip().lower()
        if password_reset_delivery not in {"token", "email"}:
            raise RuntimeError("PASSWORD_RESET_DELIVERY must be token or email")
        if is_production and password_reset_delivery != "email":
            raise RuntimeError(
                "Production password reset must deliver tokens by email"
            )

        password_reset_url = os.getenv("PASSWORD_RESET_URL", "").strip()
        if not password_reset_url and public_base_url:
            password_reset_url = f"{public_base_url.rstrip('/')}/reset-password"
        if not password_reset_url:
            password_reset_url = "http://localhost:3000/reset-password"
        parsed_reset_url = urlsplit(password_reset_url)
        if parsed_reset_url.scheme not in {"http", "https"} or not parsed_reset_url.netloc:
            raise RuntimeError("PASSWORD_RESET_URL must be an absolute http(s) URL")
        if is_production and parsed_reset_url.scheme != "https":
            raise RuntimeError("Production PASSWORD_RESET_URL must use HTTPS")

        smtp_host = os.getenv("SMTP_HOST", "").strip() or None
        smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or None
        smtp_starttls = _bool("SMTP_STARTTLS", True)
        if password_reset_delivery == "email" and (
            not smtp_host or not smtp_from_email
        ):
            raise RuntimeError(
                "SMTP_HOST and SMTP_FROM_EMAIL are required for email password reset delivery"
            )
        if is_production and not smtp_starttls:
            raise RuntimeError("Production SMTP password reset delivery must use TLS")

        refresh_cookie_samesite = os.getenv(
            "REFRESH_COOKIE_SAMESITE",
            "lax",
        ).strip().lower()
        if refresh_cookie_samesite not in {"strict", "lax", "none"}:
            raise RuntimeError("REFRESH_COOKIE_SAMESITE must be strict, lax, or none")

        refresh_cookie_secure = _bool(
            "REFRESH_COOKIE_SECURE",
            is_production,
        )
        if is_production and not refresh_cookie_secure:
            raise RuntimeError("REFRESH_COOKIE_SECURE must be true in production")
        if refresh_cookie_samesite == "none" and not refresh_cookie_secure:
            raise RuntimeError("SameSite=None requires a Secure refresh cookie")

        refresh_token_mode = os.getenv(
            "REFRESH_TOKEN_MODE",
            "cookie",
        ).strip().lower()
        if refresh_token_mode not in {"cookie", "body"}:
            raise RuntimeError("REFRESH_TOKEN_MODE must be cookie or body")
        if is_production and refresh_token_mode != "cookie":
            raise RuntimeError("Production refresh tokens must use HttpOnly cookies")

        storage_backend = os.getenv("STORAGE_BACKEND", "local").strip().lower()
        if storage_backend != "local":
            raise RuntimeError(
                "Only STORAGE_BACKEND=local is implemented; configure an object-storage adapter before using another value"
            )
        storage_root = os.getenv("STORAGE_ROOT", "").strip() or None
        if is_production and not storage_root:
            raise RuntimeError(
                "STORAGE_ROOT must point to a persistent volume in production"
            )
        if storage_root and is_production and not Path(storage_root).is_absolute():
            raise RuntimeError("Production STORAGE_ROOT must be an absolute path")

        return cls(
            database_url=database_url,
            jwt_secret_key=jwt_secret_key,
            jwt_algorithm=jwt_algorithm,
            access_token_expire_minutes=_positive_int(
                "ACCESS_TOKEN_EXPIRE_MINUTES",
                15,
            ),
            refresh_token_expire_days=_positive_int(
                "REFRESH_TOKEN_EXPIRE_DAYS",
                30,
            ),
            app_env=app_env,
            frontend_origins=frontend_origins,
            trusted_hosts=trusted_hosts,
            enable_api_docs=_bool("ENABLE_API_DOCS", not is_production),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
            public_base_url=public_base_url,
            password_reset_url=password_reset_url,
            password_reset_delivery=password_reset_delivery,
            password_reset_token_expire_minutes=_positive_int(
                "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
                30,
            ),
            smtp_host=smtp_host,
            smtp_port=_positive_int("SMTP_PORT", 587),
            smtp_username=os.getenv("SMTP_USERNAME", "").strip() or None,
            smtp_password=os.getenv("SMTP_PASSWORD", "").strip() or None,
            smtp_from_email=smtp_from_email,
            smtp_starttls=smtp_starttls,
            refresh_cookie_name=os.getenv(
                "REFRESH_COOKIE_NAME",
                "herstyleai_refresh",
            ).strip(),
            refresh_cookie_secure=refresh_cookie_secure,
            refresh_cookie_samesite=refresh_cookie_samesite,
            refresh_cookie_domain=os.getenv("REFRESH_COOKIE_DOMAIN", "").strip()
            or None,
            refresh_cookie_path=os.getenv(
                "REFRESH_COOKIE_PATH",
                "/api/v1/auth",
            ).strip(),
            refresh_token_mode=refresh_token_mode,
            db_pool_size=_positive_int("DB_POOL_SIZE", 5),
            db_max_overflow=_non_negative_int("DB_MAX_OVERFLOW", 10),
            db_pool_timeout=_positive_int("DB_POOL_TIMEOUT", 30),
            db_pool_recycle=_positive_int("DB_POOL_RECYCLE", 1800),
            db_connect_timeout=_positive_int("DB_CONNECT_TIMEOUT", 10),
            db_ssl_mode=db_ssl_mode,
            storage_backend=storage_backend,
            storage_root=storage_root,
            max_upload_bytes=_positive_int(
                "MAX_UPLOAD_BYTES",
                10 * 1024 * 1024,
            ),
            login_rate_limit=_positive_int("LOGIN_RATE_LIMIT", 10),
            register_rate_limit=_positive_int("REGISTER_RATE_LIMIT", 5),
            refresh_rate_limit=_positive_int("REFRESH_RATE_LIMIT", 30),
            password_reset_rate_limit=_positive_int(
                "PASSWORD_RESET_RATE_LIMIT",
                5,
            ),
            ai_rate_limit=_positive_int("AI_RATE_LIMIT", 20),
            rate_limit_window_seconds=_positive_int(
                "RATE_LIMIT_WINDOW_SECONDS",
                60,
            ),
        )


def get_settings() -> Settings:
    """Load settings for the current process environment."""

    return Settings.from_env()
