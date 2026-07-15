"""rules and scenarios title and description columns

Revision ID: d4e5f6a7b8c9
Revises: a1b2c3d4e5f6
Create Date: 2026-06-04 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scenarios", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("scenarios", sa.Column("description", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE scenarios SET title = name, description = '' WHERE title IS NULL"
        )
    )
    op.alter_column("scenarios", "title", nullable=False)
    op.alter_column("scenarios", "description", nullable=False)
    op.drop_column("scenarios", "flow_definition")
    op.drop_column("scenarios", "name")

    op.add_column("rules", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("rules", sa.Column("description", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE rules
            SET title = LEFT(rule_body, 255),
                description = rule_body
            WHERE title IS NULL
            """
        )
    )
    op.alter_column("rules", "title", nullable=False)
    op.alter_column("rules", "description", nullable=False)
    op.drop_column("rules", "rule_body")


def downgrade() -> None:
    op.add_column("rules", sa.Column("rule_body", sa.Text(), nullable=True))
    op.execute(
        sa.text("UPDATE rules SET rule_body = description WHERE rule_body IS NULL")
    )
    op.alter_column("rules", "rule_body", nullable=False)
    op.drop_column("rules", "description")
    op.drop_column("rules", "title")

    op.add_column("scenarios", sa.Column("name", sa.String(length=255), nullable=True))
    op.add_column(
        "scenarios",
        sa.Column("flow_definition", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE scenarios SET name = title, flow_definition = '{}'::jsonb WHERE name IS NULL"
        )
    )
    op.alter_column("scenarios", "name", nullable=False)
    op.alter_column("scenarios", "flow_definition", nullable=False)
    op.drop_column("scenarios", "description")
    op.drop_column("scenarios", "title")
