"""PostgreSQL wardrobe persistence model.

The existing AI domain model remains file/pipeline compatible. This model is
the authenticated API's ownership boundary and stores only image paths/URLs,
not binary image data.
"""

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class WardrobeItemRecord(Base):
    """A wardrobe item owned by one user, with soft-delete support."""

    __tablename__ = "wardrobe_items"
    __table_args__ = (
        Index("ix_wardrobe_items_user_created_at", "user_id", "created_at"),
        Index("ix_wardrobe_items_user_deleted_at", "user_id", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    processed_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(120), nullable=True)
    color: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sleeve: Mapped[str | None] = mapped_column(String(120), nullable=True)
    neckline: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    design_details: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    material: Mapped[str | None] = mapped_column(String(120), nullable=True)
    material_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    office_suitable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ai_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
