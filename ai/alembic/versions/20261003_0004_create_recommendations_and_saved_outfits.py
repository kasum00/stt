"""create recommendation ownership and saved outfit tables

Revision ID: 20261003_0004
Revises: 20261003_0003
Create Date: 2026-10-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261003_0004"
down_revision: Union[str, None] = "20261003_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
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
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_recommendations_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_recommendations"),
        sa.UniqueConstraint(
            "recommendation_id",
            name="uq_recommendations_recommendation_id",
        ),
    )

    op.create_table(
        "saved_outfits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "saved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
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
            name="fk_saved_outfits_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"],
            ["recommendations.recommendation_id"],
            name="fk_saved_outfits_recommendation_id_recommendations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_saved_outfits"),
        sa.UniqueConstraint(
            "user_id",
            "recommendation_id",
            name="uq_saved_outfits_user_recommendation",
        ),
    )

    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"], unique=False)
    op.create_index(
        "ix_recommendations_user_created_at",
        "recommendations",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_saved_outfits_user_id", "saved_outfits", ["user_id"], unique=False)
    op.create_index(
        "ix_saved_outfits_user_saved_at",
        "saved_outfits",
        ["user_id", "saved_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_saved_outfits_user_saved_at", table_name="saved_outfits")
    op.drop_index("ix_saved_outfits_user_id", table_name="saved_outfits")
    op.drop_table("saved_outfits")
    op.drop_index("ix_recommendations_user_created_at", table_name="recommendations")
    op.drop_index("ix_recommendations_user_id", table_name="recommendations")
    op.drop_table("recommendations")
