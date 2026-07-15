"""tickets.reference and tickets.customer_details

Revision ID: o4p5q6r7s8t9
Revises: n3o4p5q6r7s8
Create Date: 2026-06-19 00:35:00.000000

"""
import secrets
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "o4p5q6r7s8t9"
down_revision: Union[str, Sequence[str], None] = "n3o4p5q6r7s8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_REFERENCE_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_REFERENCE_PREFIX = "TICK-"
_REFERENCE_BODY_LENGTH = 5


def _generate_reference(used: set[str]) -> str:
    while True:
        body = "".join(
            secrets.choice(_REFERENCE_ALPHABET) for _ in range(_REFERENCE_BODY_LENGTH)
        )
        reference = f"{_REFERENCE_PREFIX}{body}"
        if reference not in used:
            used.add(reference)
            return reference


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("reference", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "tickets",
        sa.Column("customer_details", sa.String(length=255), nullable=True),
    )

    connection = op.get_bind()
    existing = connection.execute(
        sa.text("SELECT reference FROM tickets WHERE reference IS NOT NULL")
    ).fetchall()
    used: set[str] = {row[0] for row in existing}

    rows = connection.execute(
        sa.text("SELECT id FROM tickets WHERE reference IS NULL")
    ).fetchall()
    for (ticket_id,) in rows:
        connection.execute(
            sa.text("UPDATE tickets SET reference = :ref WHERE id = :id"),
            {"ref": _generate_reference(used), "id": ticket_id},
        )

    op.alter_column(
        "tickets",
        "reference",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.create_unique_constraint("uq_tickets_reference", "tickets", ["reference"])


def downgrade() -> None:
    op.drop_constraint("uq_tickets_reference", "tickets", type_="unique")
    op.drop_column("tickets", "customer_details")
    op.drop_column("tickets", "reference")
