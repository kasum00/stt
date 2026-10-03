"""Unit tests for password and token security primitives."""

from uuid import uuid4

import pytest

from herstyle_ai.core.config import Settings
from herstyle_ai.core.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def _settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://unused",
        jwt_secret_key="test-secret-" + "x" * 48,
    )


def test_passwords_use_argon2id_and_verify() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert password_hash.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_access_token_round_trip_and_invalid_token() -> None:
    settings = _settings()
    user_id = uuid4()
    token = create_access_token(user_id, settings=settings)

    assert decode_access_token(token, settings=settings) == user_id

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token("not-a-jwt", settings=settings)


def test_refresh_tokens_are_opaque_and_hashed() -> None:
    token = generate_refresh_token()
    token_hash = hash_refresh_token(token)

    assert len(token) >= 64
    assert len(token_hash) == 64
    assert token_hash != token
