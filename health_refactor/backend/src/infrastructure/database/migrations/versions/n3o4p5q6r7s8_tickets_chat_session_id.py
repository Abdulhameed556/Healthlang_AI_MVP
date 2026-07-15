"""tickets.chat_session_id linkage to chat_sessions

Revision ID: n3o4p5q6r7s8
Revises: m2n3o4p5q6r7
Create Date: 2026-06-18 09:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "n3o4p5q6r7s8"
down_revision: Union[str, Sequence[str], None] = "m2n3o4p5q6r7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("chat_session_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tickets_chat_session_id_chat_sessions",
        "tickets",
        "chat_sessions",
        ["chat_session_id"],
        ["id"],
    )
    op.create_index(
        "ix_tickets_chat_session_id",
        "tickets",
        ["chat_session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tickets_chat_session_id", table_name="tickets")
    op.drop_constraint(
        "fk_tickets_chat_session_id_chat_sessions",
        "tickets",
        type_="foreignkey",
    )
    op.drop_column("tickets", "chat_session_id")
