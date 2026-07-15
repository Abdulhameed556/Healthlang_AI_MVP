"""api_tools headers JSONB list of key/value objects

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-09 16:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE api_tools
        SET headers = '[]'::jsonb
        WHERE jsonb_typeof(headers) = 'object'
        """
    )
    op.alter_column(
        "api_tools",
        "headers",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=sa.text("'[]'::jsonb"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE api_tools
        SET headers = '{}'::jsonb
        WHERE jsonb_typeof(headers) = 'array'
        """
    )
    op.alter_column(
        "api_tools",
        "headers",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        server_default=sa.text("'{}'::jsonb"),
        existing_nullable=False,
    )
