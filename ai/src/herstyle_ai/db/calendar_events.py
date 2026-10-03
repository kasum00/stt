"""Ownership-scoped database helpers for calendar events."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.db.models import CalendarEvent


async def get_owned_calendar_event(
    db: AsyncSession,
    *,
    event_id: UUID | str,
    user_id: UUID,
) -> CalendarEvent | None:
    """Return an event only when it belongs to the requesting user."""

    try:
        parsed_id = UUID(str(event_id))
    except (TypeError, ValueError, AttributeError):
        return None

    return await db.scalar(
        select(CalendarEvent).where(
            CalendarEvent.id == parsed_id,
            CalendarEvent.user_id == user_id,
        )
    )


async def list_owned_calendar_events(
    db: AsyncSession,
    *,
    user_id: UUID,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[CalendarEvent]:
    """List events owned by a user, optionally applying overlap filters."""

    statement = select(CalendarEvent).where(CalendarEvent.user_id == user_id)

    if from_at is not None and to_at is not None:
        statement = statement.where(
            CalendarEvent.start_at <= to_at,
            or_(CalendarEvent.end_at.is_(None), CalendarEvent.end_at >= from_at),
        )
    elif from_at is not None:
        statement = statement.where(
            or_(CalendarEvent.end_at.is_(None), CalendarEvent.end_at >= from_at)
        )
    elif to_at is not None:
        statement = statement.where(CalendarEvent.start_at <= to_at)

    statement = (
        statement.order_by(CalendarEvent.start_at.asc(), CalendarEvent.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list((await db.scalars(statement)).all())
