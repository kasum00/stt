"""create owned calendar events table

Revision ID: 20261003_0005
Revises: 20261003_0004
Create Date: 2026-10-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261003_0005"
down_revision: Union[str, None] = "20261003_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=True),
        sa.Column("styling_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(btrim(title)) BETWEEN 1 AND 200",
            name="ck_calendar_events_title_nonempty",
        ),
        sa.CheckConstraint(
            "end_at IS NULL OR end_at >= start_at",
            name="ck_calendar_events_end_at_after_start_at",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_calendar_events_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_calendar_events"),
    )
    op.create_index(
        "ix_calendar_events_user_id",
        "calendar_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_calendar_events_user_start_at",
        "calendar_events",
        ["user_id", "start_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_calendar_events_user_start_at", table_name="calendar_events")
    op.drop_index("ix_calendar_events_user_id", table_name="calendar_events")
    op.drop_table("calendar_events")
