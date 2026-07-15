"""chat_sessions table and conversation_logs session linkage

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-06-04 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, Sequence[str], None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("department_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.UUID(), nullable=False),
        sa.Column("agent_version_id", sa.UUID(), nullable=True),
        sa.Column("widget_id", sa.UUID(), nullable=True),
        sa.Column("ticket_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "conversation_state",
            sa.String(length=40),
            server_default="in_progress",
            nullable=False,
        ),
        sa.Column("close_reason", sa.String(length=50), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["agent_version_id"], ["agent_versions.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["widget_id"], ["widgets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_sessions_department_id",
        "chat_sessions",
        ["department_id"],
    )
    op.create_index(
        "ix_chat_sessions_ticket_id",
        "chat_sessions",
        ["ticket_id"],
    )

    op.add_column(
        "conversation_logs",
        sa.Column("chat_session_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "conversation_logs",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.alter_column(
        "conversation_logs",
        "ticket_id",
        existing_type=sa.UUID(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_conversation_logs_chat_session_id_chat_sessions",
        "conversation_logs",
        "chat_sessions",
        ["chat_session_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_conversation_logs_chat_session_id",
        "conversation_logs",
        ["chat_session_id"],
    )
    op.create_check_constraint(
        "ck_conversation_logs_session_or_ticket",
        "conversation_logs",
        "chat_session_id IS NOT NULL OR ticket_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_conversation_logs_session_or_ticket",
        "conversation_logs",
        type_="check",
    )
    op.drop_index(
        "ix_conversation_logs_chat_session_id",
        table_name="conversation_logs",
    )
    op.drop_constraint(
        "fk_conversation_logs_chat_session_id_chat_sessions",
        "conversation_logs",
        type_="foreignkey",
    )
    op.alter_column(
        "conversation_logs",
        "ticket_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_column("conversation_logs", "metadata")
    op.drop_column("conversation_logs", "chat_session_id")

    op.drop_index("ix_chat_sessions_ticket_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_department_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
