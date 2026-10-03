"""Authenticated CRUD for user-owned saved outfit snapshots."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.api.dependencies import get_current_user
from herstyle_ai.db.models import SavedOutfit, User
from herstyle_ai.db.recommendations import get_owned_recommendation, get_owned_saved_outfit
from herstyle_ai.db.session import get_db
from herstyle_ai.schemas.saved_outfit import (
    SavedOutfitCreateRequest,
    SavedOutfitPatchRequest,
)


router = APIRouter(prefix="/api/v1/saved-outfits", tags=["saved-outfits"])


def _saved_outfit_response(saved_outfit: SavedOutfit) -> dict:
    return {
        "id": str(saved_outfit.id),
        "user_id": str(saved_outfit.user_id),
        "recommendation_id": saved_outfit.recommendation_id,
        "title": saved_outfit.title,
        "snapshot": saved_outfit.snapshot,
        "saved_at": saved_outfit.saved_at.isoformat(),
        "created_at": saved_outfit.created_at.isoformat(),
        "updated_at": saved_outfit.updated_at.isoformat(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_saved_outfit(
    payload: SavedOutfitCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recommendation = await get_owned_recommendation(
        db,
        recommendation_id=payload.recommendation_id,
        user_id=current_user.id,
    )
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    saved_outfit = SavedOutfit(
        user_id=current_user.id,
        recommendation_id=recommendation.recommendation_id,
        title=payload.title,
        snapshot=dict(recommendation.snapshot or {}),
    )
    db.add(saved_outfit)
    try:
        await db.commit()
        await db.refresh(saved_outfit)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Recommendation is already saved",
        ) from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save outfit",
        ) from exc

    return _saved_outfit_response(saved_outfit)


@router.get("")
async def list_saved_outfits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    saved_outfits = list(
        (
            await db.scalars(
                select(SavedOutfit)
                .where(SavedOutfit.user_id == current_user.id)
                .order_by(SavedOutfit.saved_at.desc())
            )
        ).all()
    )
    return {
        "count": len(saved_outfits),
        "items": [_saved_outfit_response(item) for item in saved_outfits],
    }


@router.get("/{saved_outfit_id}")
async def get_saved_outfit(
    saved_outfit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    saved_outfit = await get_owned_saved_outfit(
        db,
        saved_outfit_id=saved_outfit_id,
        user_id=current_user.id,
    )
    if saved_outfit is None:
        raise HTTPException(status_code=404, detail="Saved outfit not found")
    return _saved_outfit_response(saved_outfit)


@router.patch("/{saved_outfit_id}")
async def patch_saved_outfit(
    saved_outfit_id: str,
    payload: SavedOutfitPatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    saved_outfit = await get_owned_saved_outfit(
        db,
        saved_outfit_id=saved_outfit_id,
        user_id=current_user.id,
    )
    if saved_outfit is None:
        raise HTTPException(status_code=404, detail="Saved outfit not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(saved_outfit, field, value)
    try:
        await db.commit()
        await db.refresh(saved_outfit)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update saved outfit",
        ) from exc
    return _saved_outfit_response(saved_outfit)


@router.delete("/{saved_outfit_id}")
async def delete_saved_outfit(
    saved_outfit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    saved_outfit = await get_owned_saved_outfit(
        db,
        saved_outfit_id=saved_outfit_id,
        user_id=current_user.id,
    )
    if saved_outfit is None:
        raise HTTPException(status_code=404, detail="Saved outfit not found")

    await db.delete(saved_outfit)
    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete saved outfit",
        ) from exc
    return {"status": "deleted", "id": saved_outfit_id}
