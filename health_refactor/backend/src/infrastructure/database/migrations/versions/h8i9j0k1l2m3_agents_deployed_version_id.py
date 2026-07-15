"""agents deployed_version_id tracks live snapshot

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-06-04 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, Sequence[str], None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("deployed_version_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_agents_deployed_version_id_agent_versions",
        "agents",
        "agent_versions",
        ["deployed_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        sa.text(
            """
            UPDATE agents AS a
            SET deployed_version_id = latest.id
            FROM (
                SELECT DISTINCT ON (agent_id) id, agent_id
                FROM agent_versions
                ORDER BY agent_id, version_number DESC
            ) AS latest
            WHERE a.id = latest.agent_id
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_agents_deployed_version_id_agent_versions",
        "agents",
        type_="foreignkey",
    )
    op.drop_column("agents", "deployed_version_id")
