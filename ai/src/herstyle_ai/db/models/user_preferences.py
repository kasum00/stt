"""Database model for explicit user-entered preferences.

This table is deliberately separate from P9 learned personalization, which
continues to use its existing feedback/research persistence layer.
"""

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class UserPreferences(Base):
    """One explicit preference row owned by exactly one user."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prefer_dress: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    preferred_colors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    avoided_colors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    preferred_categories: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    avoided_categories: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    preferred_styles: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    avoided_styles: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notification_preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
