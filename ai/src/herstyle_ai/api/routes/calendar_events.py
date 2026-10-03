"""Authenticated CRUD API for user-owned calendar events."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from herstyle_ai.api.dependencies import get_current_user
from herstyle_ai.db.calendar_events import (
    get_owned_calendar_event,
    list_owned_calendar_events,
)
from herstyle_ai.db.models import CalendarEvent, User
from herstyle_ai.db.session import get_db
from herstyle_ai.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventListResponse,
    CalendarEventResponse,
    CalendarEventUpdate,
    _validate_event_window,
)


router = APIRouter(prefix="/api/v1/calendar-events", tags=["calendar-events"])


def _require_aware(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return value
    if value.tzinfo is None or value.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must include a timezone offset",
        )
    return value


def _event_response(event: CalendarEvent) -> CalendarEventResponse:
    return CalendarEventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        start_at=event.start_at,
        end_at=event.end_at,
        location=event.location,
        event_type=event.event_type,
        styling_context=event.styling_context,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _event_context(event: CalendarEvent) -> dict:
    """Return a JSON-safe, shallow context bridge for recommendations."""

    return {
        "event_id": str(event.id),
        "event_type": event.event_type,
        "title": event.title,
        "start_at": event.start_at.isoformat(),
        "end_at": event.end_at.isoformat() if event.end_at is not None else None,
        "location": event.location,
        "styling_context": dict(event.styling_context or {}),
    }


@router.post(
    "",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_calendar_event(
    payload: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    event = CalendarEvent(user_id=current_user.id, **payload.model_dump())
    db.add(event)
    try:
        await db.commit()
        await db.refresh(event)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not create calendar event") from exc
    return _event_response(event)


@router.get("", response_model=CalendarEventListResponse)
async def list_calendar_events(
    from_at: datetime | None = Query(default=None, alias="from"),
    to_at: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarEventListResponse:
    from_at = _require_aware(from_at, "from")
    to_at = _require_aware(to_at, "to")
    if from_at is not None and to_at is not None and to_at < from_at:
        raise HTTPException(status_code=422, detail="to must be greater than or equal to from")

    events = await list_owned_calendar_events(
        db,
        user_id=current_user.id,
        from_at=from_at,
        to_at=to_at,
        limit=limit,
        offset=offset,
    )
    return CalendarEventListResponse(
        count=len(events),
        items=[_event_response(event) for event in events],
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    event = await get_owned_calendar_event(db, event_id=event_id, user_id=current_user.id)
    if event is None:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    return _event_response(event)


@router.patch("/{event_id}", response_model=CalendarEventResponse)
async def patch_calendar_event(
    event_id: UUID,
    payload: CalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    event = await get_owned_calendar_event(db, event_id=event_id, user_id=current_user.id)
    if event is None:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    values = payload.model_dump(exclude_unset=True)
    candidate_start = values.get("start_at", event.start_at)
    candidate_end = values.get("end_at", event.end_at)
    try:
        _validate_event_window(candidate_start, candidate_end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    for field, value in values.items():
        setattr(event, field, value)

    try:
        await db.commit()
        await db.refresh(event)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not update calendar event") from exc
    return _event_response(event)


@router.delete("/{event_id}")
async def delete_calendar_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    event = await get_owned_calendar_event(db, event_id=event_id, user_id=current_user.id)
    if event is None:
        raise HTTPException(status_code=404, detail="Calendar event not found")

    await db.delete(event)
    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete calendar event") from exc
    return {"status": "deleted", "id": str(event_id)}
