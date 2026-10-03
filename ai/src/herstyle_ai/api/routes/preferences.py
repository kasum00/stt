"""Authenticated explicit-preferences endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.api.dependencies import get_current_user
from herstyle_ai.db.models import User, UserPreferences
from herstyle_ai.db.session import get_db
from herstyle_ai.schemas.preferences import PreferencesPatchRequest


router = APIRouter()


def _preferences_response(preferences: UserPreferences) -> dict:
    return {
        "id": str(preferences.id),
        "user_id": str(preferences.user_id),
        "prefer_dress": preferences.prefer_dress,
        "preferred_colors": preferences.preferred_colors,
        "avoided_colors": preferences.avoided_colors,
        "preferred_categories": preferences.preferred_categories,
        "avoided_categories": preferences.avoided_categories,
        "preferred_styles": preferences.preferred_styles,
        "avoided_styles": preferences.avoided_styles,
        "notification_preferences": preferences.notification_preferences,
        "created_at": preferences.created_at.isoformat() if preferences.created_at else None,
        "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None,
    }


async def _get_or_create_preferences(
    db: AsyncSession,
    user: User,
) -> UserPreferences:
    preferences = await db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    if preferences is None:
        preferences = UserPreferences(user_id=user.id)
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
    return preferences


@router.get("/api/v1/preferences")
async def get_explicit_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    preferences = await _get_or_create_preferences(db, current_user)
    return _preferences_response(preferences)


@router.patch("/api/v1/preferences")
async def patch_explicit_preferences(
    payload: PreferencesPatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    preferences = await _get_or_create_preferences(db, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(preferences, field, value)
    await db.commit()
    await db.refresh(preferences)
    return _preferences_response(preferences)
