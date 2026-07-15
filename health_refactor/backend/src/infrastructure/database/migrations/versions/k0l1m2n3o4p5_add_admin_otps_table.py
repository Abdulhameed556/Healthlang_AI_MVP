"""add admin_otps table for login OTP storage

Revision ID: k0l1m2n3o4p5
Revises: h8i9j0k1l2m3
Create Date: 2026-06-12 17:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "k0l1m2n3o4p5"
down_revision: Union[str, Sequence[str], None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_otps",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("otp", sa.String(length=6), nullable=False),
        sa.Column(
            "expires_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_otps_email", "admin_otps", ["email"])


def downgrade() -> None:
    op.drop_index("ix_admin_otps_email", table_name="admin_otps")
    op.drop_table("admin_otps")
