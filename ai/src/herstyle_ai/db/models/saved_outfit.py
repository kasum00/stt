"""User-owned saved recommendation snapshots."""

from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SavedOutfit(Base):
    """A bookmark-like copy of a recommendation snapshot."""

    __tablename__ = "saved_outfits"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "recommendation_id",
            name="uq_saved_outfits_user_recommendation",
        ),
        Index("ix_saved_outfits_user_saved_at", "user_id", "saved_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey(
            "recommendations.recommendation_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
