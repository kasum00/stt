"""Ownership-aware persistence helpers for wardrobe API routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.db.models import WardrobeItemRecord


STYLE_COOLDOWN_DAYS = 7


def parse_wardrobe_id(item_id: str) -> UUID | None:
    """Parse both UUID strings and the legacy 32-character UUID form."""

    try:
        return UUID(str(item_id))
    except (TypeError, ValueError, AttributeError):
        return None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def record_to_domain_item(record: WardrobeItemRecord) -> dict[str, Any]:
    """Convert a DB row to the existing AI pipeline's dict contract."""

    metadata = dict(record.ai_metadata or {})
    last_styled_at = record.last_styled_at
    styling_available_at = (
        last_styled_at + timedelta(days=STYLE_COOLDOWN_DAYS)
        if last_styled_at is not None
        else None
    )
    now = datetime.now(timezone.utc)
    if styling_available_at is not None and styling_available_at.tzinfo is None:
        styling_available_at = styling_available_at.replace(tzinfo=timezone.utc)

    item = {
        "item_id": record.id.hex,
        "image_path": record.image_url,
        "created_at": _iso(record.created_at),
        "updated_at": _iso(record.updated_at),
        "category": record.category,
        "subcategory": record.subcategory,
        "color": record.color,
        "material": record.material,
        "pattern": record.pattern,
        # Domain/pipeline name remains sleeve_length; DB boundary is sleeve.
        "sleeve_length": record.sleeve,
        "neckline": record.neckline,
        "fit": record.fit,
        "design_details": record.design_details or [],
        "color_profile": metadata.pop("color_profile", {}),
        "pattern_profile": metadata.pop("pattern_profile", {}),
        "style_tags": metadata.pop("style_tags", []),
        "material_candidates": metadata.pop("material_candidates", []),
        "needs_confirmation": metadata.pop("needs_confirmation", []),
        "recognition_sources": metadata.pop("recognition_sources", {}),
        "office_relevance": metadata.pop("office_relevance", None),
        "office_relevance_reasons": metadata.pop("office_relevance_reasons", []),
        "last_styled_at": _iso(last_styled_at),
        "styling_available_at": _iso(styling_available_at),
        "styling_cooldown_active": bool(
            styling_available_at is not None and styling_available_at > now
        ),
    }
    item.update(metadata)
    if record.processed_image_url:
        item["transparent_image_path"] = record.processed_image_url
    return item


def _metadata_from_domain(item: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = dict(existing or {})
    for key in (
        "color_profile",
        "pattern_profile",
        "style_tags",
        "material_candidates",
        "needs_confirmation",
        "recognition_sources",
        "office_relevance",
        "office_relevance_reasons",
        "original_image_path",
        "transparent_image_path",
        "model_input_path",
        "source_sha256",
    ):
        if key in item:
            metadata[key] = item[key]
    return metadata


def apply_domain_item_to_record(
    record: WardrobeItemRecord,
    item: dict[str, Any],
) -> WardrobeItemRecord:
    """Apply existing domain data to a DB record without changing taxonomy."""

    image_url = item.get("image_path") or item.get("image_url")
    category = item.get("category")
    if not image_url:
        raise ValueError("Wardrobe item image_url is required")
    if not category:
        raise ValueError("Wardrobe item category is required")

    record.image_url = str(image_url)
    record.processed_image_url = item.get("transparent_image_path") or item.get("processed_image_url")
    record.category = str(category)
    record.subcategory = item.get("subcategory")
    record.color = item.get("color")
    record.pattern = item.get("pattern")
    record.sleeve = item.get("sleeve") or item.get("sleeve_length")
    record.neckline = item.get("neckline")
    record.fit = item.get("fit")
    record.design_details = item.get("design_details") or []
    record.material = item.get("material")
    needs_confirmation = item.get("needs_confirmation") or []
    record.material_confirmed = bool(record.material) and "material" not in needs_confirmation
    office_relevance = item.get("office_relevance")
    record.office_suitable = (
        True if office_relevance == "positive" else
        False if office_relevance == "negative" else
        None
    )
    record.ai_metadata = _metadata_from_domain(item, record.ai_metadata)
    return record


def new_record_from_domain(
    *,
    user_id: UUID,
    item: dict[str, Any],
) -> WardrobeItemRecord:
    item_id = parse_wardrobe_id(item.get("item_id")) or uuid4()
    record = WardrobeItemRecord(id=item_id, user_id=user_id)
    return apply_domain_item_to_record(record, item)


async def list_owned_wardrobe(
    db: AsyncSession,
    user_id: UUID,
) -> list[WardrobeItemRecord]:
    result = await db.scalars(
        select(WardrobeItemRecord)
        .where(
            WardrobeItemRecord.user_id == user_id,
            WardrobeItemRecord.deleted_at.is_(None),
        )
        .order_by(WardrobeItemRecord.created_at.desc())
    )
    return list(result.all())


async def get_owned_wardrobe(
    db: AsyncSession,
    *,
    user_id: UUID,
    item_id: str,
) -> WardrobeItemRecord | None:
    parsed_id = parse_wardrobe_id(item_id)
    if parsed_id is None:
        return None
    return await db.scalar(
        select(WardrobeItemRecord).where(
            WardrobeItemRecord.id == parsed_id,
            WardrobeItemRecord.user_id == user_id,
            WardrobeItemRecord.deleted_at.is_(None),
        )
    )


async def mark_styled_wardrobe_items(
    db: AsyncSession,
    *,
    user_id: UUID,
    item_ids: set[str],
    styled_at: datetime | None = None,
) -> int:
    """Persist the time each wardrobe item was last used in a generated outfit."""

    parsed_ids = {
        parsed
        for item_id in item_ids
        if (parsed := parse_wardrobe_id(item_id)) is not None
    }
    if not parsed_ids:
        return 0

    records = list(
        (
            await db.scalars(
                select(WardrobeItemRecord).where(
                    WardrobeItemRecord.id.in_(parsed_ids),
                    WardrobeItemRecord.user_id == user_id,
                    WardrobeItemRecord.deleted_at.is_(None),
                )
            )
        ).all()
    )
    timestamp = styled_at or datetime.now(timezone.utc)
    for record in records:
        record.last_styled_at = timestamp
    return len(records)
