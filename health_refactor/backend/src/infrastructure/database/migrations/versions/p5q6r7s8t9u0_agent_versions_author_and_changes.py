"""agent_versions.created_by, changes_applied, change_note

Revision ID: p5q6r7s8t9u0
Revises: o4p5q6r7s8t9
Create Date: 2026-06-19 22:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "p5q6r7s8t9u0"
down_revision: Union[str, Sequence[str], None] = "o4p5q6r7s8t9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agent_versions",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_agent_versions_created_by_users",
        "agent_versions",
        "users",
        ["created_by"],
        ["id"],
    )
    op.add_column(
        "agent_versions",
        sa.Column(
            "changes_applied",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "agent_versions",
        sa.Column("change_note", sa.Text(), nullable=True),
    )

    # Backfill author from the agent's creator for existing snapshots.
    op.execute(
        sa.text(
            "UPDATE agent_versions av "
            "SET created_by = a.created_by "
            "FROM agents a "
            "WHERE av.agent_id = a.id AND av.created_by IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("agent_versions", "change_note")
    op.drop_column("agent_versions", "changes_applied")
    op.drop_constraint(
        "fk_agent_versions_created_by_users", "agent_versions", type_="foreignkey"
    )
    op.drop_column("agent_versions", "created_by")
