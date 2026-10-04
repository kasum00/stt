"""track the last time a wardrobe item was used for styling

Revision ID: 20261004_0005
Revises: 20261003_0004
Create Date: 2026-10-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261004_0005"
down_revision: Union[str, None] = "20261003_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "wardrobe_items",
        sa.Column("last_styled_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("wardrobe_items", "last_styled_at")
