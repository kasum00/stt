"""Authenticated profile endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from herstyle_ai.api.dependencies import get_current_user
from herstyle_ai.db.models import User, UserProfile
from herstyle_ai.db.session import get_db
from herstyle_ai.schemas.profile import ProfilePatchRequest


router = APIRouter()


def _profile_response(profile: UserProfile) -> dict:
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "display_name": profile.display_name,
        "avatar_url": profile.avatar_url,
        "timezone": profile.timezone,
        "locale": profile.locale,
        "location_name": profile.location_name,
        "latitude": profile.latitude,
        "longitude": profile.longitude,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


async def _get_or_create_profile(db: AsyncSession, user: User) -> UserProfile:
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("/api/v1/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user)
    return _profile_response(profile)


@router.patch("/api/v1/profile")
async def patch_profile(
    payload: ProfilePatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_profile(db, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return _profile_response(profile)
