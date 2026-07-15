"""user_sessions refresh token columns

Revision ID: u1v2w3x4y5z6
Revises: t0u1v2w3x4y5
Create Date: 2026-06-27 12:05:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "u1v2w3x4y5z6"
down_revision: Union[str, Sequence[str], None] = "t0u1v2w3x4y5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = inspect(op.get_bind())
    column_names = {c["name"] for c in insp.get_columns("user_sessions")}
    unique_names = {c["name"] for c in insp.get_unique_constraints("user_sessions")}

    if "refresh_token" not in column_names:
        op.add_column(
            "user_sessions",
            sa.Column("refresh_token", sa.Text(), nullable=True),
        )
    if "refresh_expires_at" not in column_names:
        op.add_column(
            "user_sessions",
            sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "uq_user_sessions_refresh_token" not in unique_names:
        op.create_unique_constraint(
            "uq_user_sessions_refresh_token",
            "user_sessions",
            ["refresh_token"],
        )


def downgrade() -> None:
    insp = inspect(op.get_bind())
    column_names = {c["name"] for c in insp.get_columns("user_sessions")}
    unique_names = {c["name"] for c in insp.get_unique_constraints("user_sessions")}

    if "uq_user_sessions_refresh_token" in unique_names:
        op.drop_constraint("uq_user_sessions_refresh_token", "user_sessions", type_="unique")
    if "refresh_expires_at" in column_names:
        op.drop_column("user_sessions", "refresh_expires_at")
    if "refresh_token" in column_names:
        op.drop_column("user_sessions", "refresh_token")
