"""FastAPI dependencies for authenticated requests."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.core.config import get_settings
from herstyle_ai.core.security import (
    InvalidAccessTokenError,
    decode_access_token,
)
from herstyle_ai.db.models import User
from herstyle_ai.db.session import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve identity from a verified JWT subject, never from the client body."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _credentials_error()

    try:
        user_id = decode_access_token(
            credentials.credentials,
            settings=get_settings(),
        )
    except (InvalidAccessTokenError, RuntimeError):
        raise _credentials_error()

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise _credentials_error()

    return user
