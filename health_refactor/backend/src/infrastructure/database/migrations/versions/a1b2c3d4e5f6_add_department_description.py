"""add department description

Revision ID: a1b2c3d4e5f6
Revises: fb34dc650e06
Create Date: 2026-06-04 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "fb34dc650e06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("departments", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("departments", "description")
