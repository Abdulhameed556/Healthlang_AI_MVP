"""api_tools auth_key_hash -> auth_key_encrypted

Revision ID: i9j0k1l2m3n4
Revises: k0l1m2n3o4p5
Create Date: 2026-06-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, Sequence[str], None] = "k0l1m2n3o4p5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "api_tools",
        "auth_key_hash",
        new_column_name="auth_key_encrypted",
    )
    # Legacy bcrypt hashes cannot be decrypted; admins must re-enter bearer tokens.
    op.execute(
        """
        UPDATE api_tools
        SET auth_key_encrypted = NULL
        WHERE auth_key_encrypted LIKE '$2b$%'
           OR auth_key_encrypted LIKE '$2a$%'
        """
    )


def downgrade() -> None:
    op.alter_column(
        "api_tools",
        "auth_key_encrypted",
        new_column_name="auth_key_hash",
    )
