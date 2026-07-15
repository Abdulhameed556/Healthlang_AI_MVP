"""scenarios short_description and prompt columns

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-09 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scenarios", sa.Column("short_description", sa.Text(), nullable=True))
    op.add_column("scenarios", sa.Column("prompt", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE scenarios SET short_description = '', prompt = description "
            "WHERE short_description IS NULL"
        )
    )
    op.alter_column("scenarios", "short_description", nullable=False)
    op.alter_column("scenarios", "prompt", nullable=False)
    op.drop_column("scenarios", "description")


def downgrade() -> None:
    op.add_column("scenarios", sa.Column("description", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE scenarios SET description = prompt WHERE description IS NULL"
        )
    )
    op.alter_column("scenarios", "description", nullable=False)
    op.drop_column("scenarios", "prompt")
    op.drop_column("scenarios", "short_description")
