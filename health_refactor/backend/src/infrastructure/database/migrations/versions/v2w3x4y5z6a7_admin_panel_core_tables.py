"""admin panel core tables (admin_users, admin_sessions, admin_invitations)

Revision ID: v2w3x4y5z6a7
Revises: u1v2w3x4y5z6
Create Date: 2026-06-27 12:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "v2w3x4y5z6a7"
down_revision: Union[str, Sequence[str], None] = "u1v2w3x4y5z6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = inspect(op.get_bind())

    if not insp.has_table("admin_users"):
        op.create_table(
            "admin_users",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("first_name", sa.String(length=100), nullable=False),
            sa.Column("last_name", sa.String(length=100), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column(
                "google_linked", sa.Boolean(), nullable=False, server_default=sa.text("false")
            ),
            sa.Column(
                "must_change_password",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "failed_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")
            ),
            sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
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
            sa.ForeignKeyConstraint(["invited_by"], ["admin_users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_admin_users_email", "admin_users", ["email"])

    if not insp.has_table("admin_sessions"):
        op.create_table(
            "admin_sessions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("token", sa.String(length=512), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["admin_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )
        op.create_index("ix_admin_sessions_token", "admin_sessions", ["token"])

    if not insp.has_table("admin_invitations"):
        op.create_table(
            "admin_invitations",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),
            sa.Column("token", sa.String(length=255), nullable=False),
            sa.Column("invited_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["invited_by"], ["admin_users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )
        op.create_index("ix_admin_invitations_email", "admin_invitations", ["email"])
        op.create_index("ix_admin_invitations_token", "admin_invitations", ["token"])


def downgrade() -> None:
    insp = inspect(op.get_bind())

    if insp.has_table("admin_invitations"):
        op.drop_index("ix_admin_invitations_token", table_name="admin_invitations")
        op.drop_index("ix_admin_invitations_email", table_name="admin_invitations")
        op.drop_table("admin_invitations")
    if insp.has_table("admin_sessions"):
        op.drop_index("ix_admin_sessions_token", table_name="admin_sessions")
        op.drop_table("admin_sessions")
    if insp.has_table("admin_users"):
        op.drop_index("ix_admin_users_email", table_name="admin_users")
        op.drop_table("admin_users")
