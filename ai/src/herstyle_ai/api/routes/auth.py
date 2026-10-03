"""Authentication and current-user endpoints."""

from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.api.dependencies import get_current_user
from herstyle_ai.core.config import get_settings
from herstyle_ai.core.password_reset import (
    build_password_reset_link,
    deliver_password_reset_email,
)
from herstyle_ai.core.security import (
    create_access_token,
    generate_password_reset_token,
    generate_refresh_token,
    hash_password,
    hash_password_reset_token,
    hash_refresh_token,
    verify_password,
)
from herstyle_ai.db.models import AuthSession, PasswordResetToken, User
from herstyle_ai.db.session import get_db
from herstyle_ai.core.rate_limit import rate_limiter
from herstyle_ai.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateMeRequest,
    UserResponse,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


def _invalid_login() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _invalid_refresh() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )


def _client_host(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _enforce_rate_limit(
    request: Request,
    bucket: str,
    identifier: str,
    limit: int,
) -> None:
    settings = get_settings()
    allowed, retry_after = rate_limiter.check(
        f"{bucket}:{_client_host(request)}:{identifier}",
        limit,
        settings.rate_limit_window_seconds,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please retry later.",
            headers={"Retry-After": str(retry_after)},
        )


def _set_refresh_cookie(response: Response, raw_refresh_token: str, settings) -> None:
    if settings.refresh_token_mode != "cookie":
        return
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        domain=settings.refresh_cookie_domain,
        path=settings.refresh_cookie_path,
    )


def _clear_refresh_cookie(response: Response, settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        domain=settings.refresh_cookie_domain,
        path=settings.refresh_cookie_path,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
    )


def _resolve_refresh_token(
    request: Request,
    payload: RefreshRequest | None,
) -> str | None:
    settings = get_settings()
    cookie_token = request.cookies.get(settings.refresh_cookie_name)
    if cookie_token:
        return cookie_token
    if settings.refresh_token_mode == "body" and payload is not None:
        return payload.refresh_token
    return None


def _validate_cookie_origin(request: Request, settings) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in settings.frontend_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin is not allowed",
        )


def _token_response(user_id, raw_refresh_token: str) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(user_id, settings=settings),
        refresh_token=(
            raw_refresh_token if settings.refresh_token_mode == "body" else None
        ),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    email = _normalize_email(str(payload.email))
    _enforce_rate_limit(
        request=request,
        bucket="register",
        identifier=email,
        limit=get_settings().register_rate_limit,
    )
    existing_user = await db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc

    return _user_response(user)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_202_ACCEPTED,
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    """Create a one-time reset token without revealing whether an email exists."""

    settings = get_settings()
    _enforce_rate_limit(
        request=request,
        bucket="password-reset-request",
        identifier="all",
        limit=settings.password_reset_rate_limit,
    )
    email = _normalize_email(str(payload.email))
    now = datetime.now(timezone.utc)
    raw_token: str | None = None
    user_email: str | None = None

    async with db.begin():
        user = await db.scalar(select(User).where(User.email == email))
        if user is not None and user.is_active:
            raw_token = generate_password_reset_token()
            user_email = user.email
            await db.execute(
                update(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                )
                .values(used_at=now)
            )
            db.add(
                PasswordResetToken(
                    user_id=user.id,
                    token_hash=hash_password_reset_token(raw_token),
                    expires_at=now
                    + timedelta(
                        minutes=settings.password_reset_token_expire_minutes
                    ),
                )
            )

    if raw_token is not None and user_email is not None:
        if settings.password_reset_delivery == "email":
            try:
                await deliver_password_reset_email(
                    settings,
                    user_email,
                    build_password_reset_link(settings, raw_token),
                )
            except Exception:
                # Keep the response indistinguishable from an unknown email.
                # The token remains short-lived and can be replaced by a new request.
                logger.exception("password_reset_email_delivery_failed")
        else:
            return ForgotPasswordResponse(
                message="If the email is registered, reset instructions are available.",
                reset_token=raw_token,
            )

    return ForgotPasswordResponse(
        message="If the email is registered, reset instructions have been sent."
    )


@router.post(
    "/reset-password",
    response_model=ForgotPasswordResponse,
    response_model_exclude_none=True,
)
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> ForgotPasswordResponse:
    """Consume a reset token, update the password, and revoke refresh sessions."""

    settings = get_settings()
    _enforce_rate_limit(
        request=request,
        bucket="password-reset-submit",
        identifier="all",
        limit=settings.password_reset_rate_limit,
    )
    now = datetime.now(timezone.utc)

    async with db.begin():
        reset_record = await db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash
                == hash_password_reset_token(payload.token),
            )
            .with_for_update()
        )
        if (
            reset_record is None
            or reset_record.used_at is not None
            or reset_record.expires_at <= now
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        user = await db.scalar(select(User).where(User.id == reset_record.user_id))
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        user.password_hash = hash_password(payload.new_password)
        reset_record.used_at = now
        await db.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    _clear_refresh_cookie(response, settings)
    return ForgotPasswordResponse(message="Password reset successfully.")


@router.post(
    "/login",
    response_model=TokenResponse,
    response_model_exclude_none=True,
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    email = _normalize_email(str(payload.email))
    _enforce_rate_limit(
        request=request,
        bucket="login",
        identifier=email,
        limit=get_settings().login_rate_limit,
    )
    user = await db.scalar(select(User).where(User.email == email))

    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise _invalid_login()

    settings = get_settings()
    now = datetime.now(timezone.utc)
    raw_refresh_token = generate_refresh_token()
    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        user_agent=request.headers.get("user-agent"),
    )
    user.last_login_at = now
    db.add(session)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create authentication session",
        ) from exc

    _set_refresh_cookie(response, raw_refresh_token, settings)
    return _token_response(user.id, raw_refresh_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    response_model_exclude_none=True,
)
async def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    _enforce_rate_limit(
        request=request,
        bucket="refresh",
        identifier="cookie-or-body",
        limit=settings.refresh_rate_limit,
    )
    _validate_cookie_origin(request, settings)
    now = datetime.now(timezone.utc)
    raw_old_refresh_token = _resolve_refresh_token(request, payload)
    if not raw_old_refresh_token:
        raise _invalid_refresh()
    old_hash = hash_refresh_token(raw_old_refresh_token)

    async with db.begin():
        session = await db.scalar(
            select(AuthSession)
            .where(AuthSession.refresh_token_hash == old_hash)
            .with_for_update()
        )

        if (
            session is None
            or session.revoked_at is not None
            or session.replaced_by_session_id is not None
            or session.expires_at <= now
        ):
            raise _invalid_refresh()

        user = await db.scalar(select(User).where(User.id == session.user_id))
        if user is None or not user.is_active:
            raise _invalid_refresh()

        raw_refresh_token = generate_refresh_token()
        replacement = AuthSession(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(raw_refresh_token),
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            user_agent=request.headers.get("user-agent"),
        )
        db.add(replacement)
        await db.flush()

        session.revoked_at = now
        session.replaced_by_session_id = replacement.id
        session.last_used_at = now

    _set_refresh_cookie(response, raw_refresh_token, settings)
    return _token_response(user.id, raw_refresh_token)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    settings = get_settings()
    _validate_cookie_origin(request, settings)
    raw_refresh_token = _resolve_refresh_token(request, payload)
    if raw_refresh_token:
        session = await db.scalar(
            select(AuthSession).where(
                AuthSession.refresh_token_hash == hash_refresh_token(
                    raw_refresh_token
                )
            )
        )
    else:
        session = None
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        await db.commit()

    _clear_refresh_cookie(response, settings)
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if payload.email is None:
        return _user_response(current_user)

    email = _normalize_email(str(payload.email))
    if email == current_user.email:
        return _user_response(current_user)

    existing_user = await db.scalar(select(User).where(User.email == email))
    if existing_user is not None and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    current_user.email = email
    current_user.is_verified = False
    try:
        await db.commit()
        await db.refresh(current_user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc

    return _user_response(current_user)


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from current password",
        )

    current_user.password_hash = hash_password(payload.new_password)
    now = datetime.now(timezone.utc)
    await db.execute(
        update(AuthSession)
        .where(
            AuthSession.user_id == current_user.id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    await db.commit()
    _clear_refresh_cookie(response, get_settings())

    return {"status": "password_changed"}
