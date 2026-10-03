"""create profile, explicit preferences, and owned wardrobe tables

Revision ID: 20261003_0003
Revises: 20261003_0002
Create Date: 2026-10-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261003_0003"
down_revision: Union[str, None] = "20261003_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "timezone",
            sa.String(length=64),
            server_default="Asia/Ho_Chi_Minh",
            nullable=False,
        ),
        sa.Column(
            "locale",
            sa.String(length=32),
            server_default="vi-VN",
            nullable=False,
        ),
        sa.Column("location_name", sa.String(length=160), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_profiles"),
        sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
    )

    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prefer_dress", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("preferred_colors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("avoided_colors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("preferred_categories", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("avoided_categories", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("preferred_styles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("avoided_styles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "notification_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_preferences_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_preferences"),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )

    op.create_table(
        "wardrobe_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("processed_image_url", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("subcategory", sa.String(length=120), nullable=True),
        sa.Column("color", sa.String(length=120), nullable=True),
        sa.Column("pattern", sa.String(length=120), nullable=True),
        sa.Column("sleeve", sa.String(length=120), nullable=True),
        sa.Column("neckline", sa.String(length=120), nullable=True),
        sa.Column("fit", sa.String(length=120), nullable=True),
        sa.Column("design_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("material", sa.String(length=120), nullable=True),
        sa.Column("material_confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("office_suitable", sa.Boolean(), nullable=True),
        sa.Column("ai_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_wardrobe_items_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_wardrobe_items"),
    )

    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=False)
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=False)
    op.create_index("ix_wardrobe_items_user_id", "wardrobe_items", ["user_id"], unique=False)
    op.create_index(
        "ix_wardrobe_items_user_created_at",
        "wardrobe_items",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_wardrobe_items_user_deleted_at",
        "wardrobe_items",
        ["user_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_wardrobe_items_user_deleted_at", table_name="wardrobe_items")
    op.drop_index("ix_wardrobe_items_user_created_at", table_name="wardrobe_items")
    op.drop_index("ix_wardrobe_items_user_id", table_name="wardrobe_items")
    op.drop_table("wardrobe_items")
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")
