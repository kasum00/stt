"""Ownership and persistence helpers for recommendations and saved outfits."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.db.models import RecommendationRecord, SavedOutfit
from herstyle_ai.personalization.recommendation_snapshot import (
    build_recommendation_snapshot,
)


class RecommendationPersistenceError(RuntimeError):
    """Raised when a generated recommendation cannot be registered."""


def _build_operational_snapshot(
    *,
    recommendation_id: str,
    user_id: UUID,
    outfit: Mapping[str, Any],
    weather: Mapping[str, Any] | None,
    request_applied: Any,
    day: Any,
    generation_id: str | None = None,
) -> dict[str, Any]:
    snapshot = build_recommendation_snapshot(
        recommendation_id=recommendation_id,
        user_id=str(user_id),
        outfit=outfit,
        weather=weather or {},
        request_applied=request_applied,
    )
    snapshot["day"] = day
    if generation_id:
        snapshot["generation_id"] = generation_id
    explanation = outfit.get("explanation")
    if isinstance(explanation, Mapping):
        snapshot["explanation"] = dict(explanation)
    return snapshot


def _snapshots_from_result(
    *,
    result: Mapping[str, Any],
    user_id: UUID,
) -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    schedule = result.get("schedule", [])
    generation_id = result.get("generation_id")
    if not isinstance(schedule, list):
        return snapshots

    for schedule_day in schedule:
        if not isinstance(schedule_day, Mapping):
            continue
        outfit = schedule_day.get("outfit")
        if not isinstance(outfit, Mapping):
            continue
        recommendation_id = outfit.get("recommendation_id")
        if recommendation_id is None or not str(recommendation_id).strip():
            continue
        recommendation_id = str(recommendation_id)
        snapshots[recommendation_id] = _build_operational_snapshot(
            recommendation_id=recommendation_id,
            user_id=user_id,
            outfit=outfit,
            weather=schedule_day.get("weather"),
            request_applied=schedule_day.get("request_applied"),
            day=schedule_day.get("day"),
            generation_id=str(generation_id) if generation_id else None,
        )
    return snapshots


async def persist_generated_recommendations(
    db: AsyncSession,
    *,
    user_id: UUID,
    result: Mapping[str, Any],
    source: str = "weekly",
) -> list[RecommendationRecord]:
    """Register all recommendation IDs in a generated response.

    Existing rows are only refreshed when they already belong to the same
    user. A recommendation ID collision with another user is a hard failure;
    ownership is never reassigned.
    """

    snapshots = _snapshots_from_result(result=result, user_id=user_id)
    if not snapshots:
        return []

    recommendation_ids = list(snapshots)
    existing_rows = list(
        (
            await db.scalars(
                select(RecommendationRecord).where(
                    RecommendationRecord.recommendation_id.in_(recommendation_ids)
                )
            )
        ).all()
    )
    existing_by_id = {row.recommendation_id: row for row in existing_rows}
    persisted: list[RecommendationRecord] = []

    for recommendation_id, snapshot in snapshots.items():
        row = existing_by_id.get(recommendation_id)
        if row is not None:
            if row.user_id != user_id:
                raise RecommendationPersistenceError(
                    "Generated recommendation ID is already owned by another user"
                )
            row.snapshot = snapshot
            row.source = source
            persisted.append(row)
            continue

        row = RecommendationRecord(
            recommendation_id=recommendation_id,
            user_id=user_id,
            snapshot=snapshot,
            source=source,
        )
        db.add(row)
        persisted.append(row)

    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise RecommendationPersistenceError(
            "Could not persist recommendation ownership"
        ) from exc

    return persisted


async def replace_owned_recommendation_day(
    db: AsyncSession,
    *,
    user_id: UUID,
    generation_id: str,
    day: int,
) -> int:
    """Hide the previous version of one day before saving its replacement."""

    records = list(
        (
            await db.scalars(
                select(RecommendationRecord).where(
                    RecommendationRecord.user_id == user_id,
                    RecommendationRecord.source == "weekly",
                    RecommendationRecord.deleted_at.is_(None),
                )
            )
        ).all()
    )
    replaced = 0
    timestamp = datetime.now(timezone.utc)
    for record in records:
        snapshot = record.snapshot or {}
        if (
            snapshot.get("generation_id") == generation_id
            and int(snapshot.get("day") or 0) == int(day)
        ):
            record.deleted_at = timestamp
            replaced += 1
    return replaced


async def list_owned_recommendations(
    db: AsyncSession,
    *,
    user_id: UUID,
    source: str = "weekly",
    limit: int = 50,
) -> list[RecommendationRecord]:
    """Return the user's newest persisted recommendations for restoration."""

    safe_limit = max(1, min(int(limit), 200))
    result = await db.scalars(
        select(RecommendationRecord)
        .where(
            RecommendationRecord.user_id == user_id,
            RecommendationRecord.source == source,
            RecommendationRecord.deleted_at.is_(None),
        )
        .order_by(RecommendationRecord.created_at.desc())
        .limit(safe_limit)
    )
    return list(result.all())


async def get_owned_recommendation(
    db: AsyncSession,
    *,
    recommendation_id: str,
    user_id: UUID,
) -> RecommendationRecord | None:
    """Return a recommendation only when it belongs to the requesting user."""

    normalized_id = str(recommendation_id or "").strip()
    if not normalized_id:
        return None
    return await db.scalar(
        select(RecommendationRecord).where(
            RecommendationRecord.recommendation_id == normalized_id,
            RecommendationRecord.user_id == user_id,
            RecommendationRecord.deleted_at.is_(None),
        )
    )


async def get_owned_saved_outfit(
    db: AsyncSession,
    *,
    saved_outfit_id: str,
    user_id: UUID,
) -> SavedOutfit | None:
    try:
        parsed_id = UUID(str(saved_outfit_id))
    except (TypeError, ValueError, AttributeError):
        return None
    return await db.scalar(
        select(SavedOutfit).where(
            SavedOutfit.id == parsed_id,
            SavedOutfit.user_id == user_id,
        )
    )
