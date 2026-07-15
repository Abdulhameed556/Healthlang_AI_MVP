"""users email unique per department

Revision ID: t0u1v2w3x4y5
Revises: s8t9u0v1w2x3
Create Date: 2026-06-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "t0u1v2w3x4y5"
down_revision: Union[str, Sequence[str], None] = "s8t9u0v1w2x3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    insp = inspect(op.get_bind())
    unique_names = {c["name"] for c in insp.get_unique_constraints("users")}

    # Fresh DBs still have users_email_key from fb34dc650e06; dev DBs that ran the
    # retired admin b2 migration may already have uq_users_email_department_id.
    if "users_email_key" in unique_names:
        op.drop_constraint("users_email_key", "users", type_="unique")
    if "uq_users_email_department_id" not in unique_names:
        op.create_unique_constraint(
            "uq_users_email_department_id",
            "users",
            ["email", "department_id"],
        )


def downgrade() -> None:
    insp = inspect(op.get_bind())
    unique_names = {c["name"] for c in insp.get_unique_constraints("users")}

    if "uq_users_email_department_id" in unique_names:
        op.drop_constraint("uq_users_email_department_id", "users", type_="unique")
    if "users_email_key" not in unique_names:
        op.create_unique_constraint("users_email_key", "users", ["email"])
