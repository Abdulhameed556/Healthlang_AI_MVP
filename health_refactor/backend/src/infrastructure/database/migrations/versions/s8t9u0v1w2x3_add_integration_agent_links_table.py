"""add integration_agent_links table linking agents to integrations

Revision ID: s8t9u0v1w2x3
Revises: r7s8t9u0v1w2
Create Date: 2026-06-23 14:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "s8t9u0v1w2x3"
down_revision: Union[str, Sequence[str], None] = "r7s8t9u0v1w2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "integration_agent_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["integration_id"], ["integrations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "agent_id", name="uq_integration_agent_links_agent_id"
        ),
    )
    op.create_index(
        "ix_integration_agent_links_department_id",
        "integration_agent_links",
        ["department_id"],
    )
    op.create_index(
        "ix_integration_agent_links_integration_id",
        "integration_agent_links",
        ["integration_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_integration_agent_links_integration_id",
        table_name="integration_agent_links",
    )
    op.drop_index(
        "ix_integration_agent_links_department_id",
        table_name="integration_agent_links",
    )
    op.drop_table("integration_agent_links")
