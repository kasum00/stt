"""Validation and response schemas for owned calendar events."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


MAX_STYLING_CONTEXT_BYTES = 16 * 1024
MAX_STYLING_CONTEXT_KEYS = 32
MAX_STYLING_CONTEXT_DEPTH = 4


def _validate_aware_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return value
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must include a timezone offset")
    return value


def _validate_json_shape(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return value
    if len(value) > MAX_STYLING_CONTEXT_KEYS:
        raise ValueError("styling_context has too many top-level keys")

    def depth(item: Any, current: int = 1) -> int:
        if isinstance(item, dict):
            if current > MAX_STYLING_CONTEXT_DEPTH:
                raise ValueError("styling_context is too deeply nested")
            return max(
                [current]
                + [depth(child, current + 1) for child in item.values()]
            )
        if isinstance(item, list):
            if current > MAX_STYLING_CONTEXT_DEPTH:
                raise ValueError("styling_context is too deeply nested")
            return max(
                [current]
                + [depth(child, current + 1) for child in item]
            )
        return current

    depth(value)
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("styling_context must contain JSON values") from exc
    if len(encoded.encode("utf-8")) > MAX_STYLING_CONTEXT_BYTES:
        raise ValueError("styling_context is too large")
    return value


def _validate_event_window(
    start_at: datetime | None,
    end_at: datetime | None,
) -> None:
    if start_at is not None:
        _validate_aware_datetime(start_at)
    if end_at is not None:
        _validate_aware_datetime(end_at)
    if start_at is not None and end_at is not None and end_at < start_at:
        raise ValueError("end_at must be greater than or equal to start_at")


class CalendarEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    start_at: datetime
    end_at: datetime | None = None
    location: str | None = Field(default=None, max_length=2_000)
    event_type: str | None = Field(default=None, max_length=80)
    styling_context: dict[str, Any] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value

    @field_validator("start_at", "end_at")
    @classmethod
    def validate_timestamps(cls, value: datetime | None) -> datetime | None:
        return _validate_aware_datetime(value)

    @field_validator("event_type")
    @classmethod
    def normalize_event_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("styling_context")
    @classmethod
    def validate_styling_context(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        return _validate_json_shape(value)

    @model_validator(mode="after")
    def validate_window(self) -> "CalendarEventCreate":
        _validate_event_window(self.start_at, self.end_at)
        return self


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    start_at: datetime | None = None
    end_at: datetime | None = None
    location: str | None = Field(default=None, max_length=2_000)
    event_type: str | None = Field(default=None, max_length=80)
    styling_context: dict[str, Any] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("title must not be empty")
        return value

    @field_validator("start_at", "end_at")
    @classmethod
    def validate_timestamps(cls, value: datetime | None) -> datetime | None:
        return _validate_aware_datetime(value)

    @field_validator("event_type")
    @classmethod
    def normalize_event_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("styling_context")
    @classmethod
    def validate_styling_context(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        return _validate_json_shape(value)

    @model_validator(mode="after")
    def validate_has_changes(self) -> "CalendarEventUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one event field is required")
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null")
        if "start_at" in self.model_fields_set and self.start_at is None:
            raise ValueError("start_at cannot be null")
        if self.start_at is not None and self.end_at is not None:
            _validate_event_window(self.start_at, self.end_at)
        return self


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime | None
    location: str | None
    event_type: str | None
    styling_context: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class CalendarEventListResponse(BaseModel):
    count: int
    items: list[CalendarEventResponse]
    limit: int
    offset: int
