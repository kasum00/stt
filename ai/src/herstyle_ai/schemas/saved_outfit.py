"""Schemas for saved outfit bookmark operations."""

from pydantic import BaseModel, Field


class SavedOutfitCreateRequest(BaseModel):
    recommendation_id: str = Field(min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=160)


class SavedOutfitPatchRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
