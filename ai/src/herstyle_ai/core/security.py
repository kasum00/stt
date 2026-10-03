"""Password and token primitives for authentication."""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from .config import Settings, get_settings


_PASSWORD_HASHER = PasswordHasher()


class InvalidAccessTokenError(ValueError):
    """Raised when an access token cannot be trusted."""


def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""

    return _PASSWORD_HASHER.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password without exposing hashing-library errors."""

    try:
        return _PASSWORD_HASHER.verify(password_hash, plain_password)
    except (InvalidHashError, VerificationError, VerifyMismatchError, TypeError):
        return False


def create_access_token(
    user_id: UUID,
    settings: Settings | None = None,
) -> str:
    """Create a short-lived JWT access token."""

    settings = settings or get_settings()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes,
    )

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
        "type": "access",
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
    settings: Settings | None = None,
) -> UUID:
    """Validate a JWT access token and return its UUID subject."""

    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp", "type"]},
        )
    except (jwt.InvalidTokenError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError("Invalid access token") from exc

    if payload.get("type") != "access":
        raise InvalidAccessTokenError("Invalid access token type")

    try:
        return UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError("Invalid access token subject") from exc


def generate_refresh_token() -> str:
    """Generate an opaque refresh token with high entropy."""

    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash an opaque refresh token for database lookup/storage."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_password_reset_token() -> str:
    """Generate a high-entropy, one-time password-reset token."""

    return secrets.token_urlsafe(32)


def hash_password_reset_token(token: str) -> str:
    """Hash a password-reset token before database lookup/storage."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
