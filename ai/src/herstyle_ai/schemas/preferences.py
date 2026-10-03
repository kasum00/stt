"""Request validation for explicit user preferences."""

from pydantic import BaseModel, Field


class PreferencesPatchRequest(BaseModel):
    prefer_dress: bool | None = None
    preferred_colors: list[str] | None = None
    avoided_colors: list[str] | None = None
    preferred_categories: list[str] | None = None
    avoided_categories: list[str] | None = None
    preferred_styles: list[str] | None = None
    avoided_styles: list[str] | None = None
    notification_preferences: dict[str, bool | str | int | float | None] | None = None


class PreferencesResponse(BaseModel):
    prefer_dress: bool
    preferred_colors: list[str] | None
    avoided_colors: list[str] | None
    preferred_categories: list[str] | None
    avoided_categories: list[str] | None
    preferred_styles: list[str] | None
    avoided_styles: list[str] | None
    notification_preferences: dict | None
