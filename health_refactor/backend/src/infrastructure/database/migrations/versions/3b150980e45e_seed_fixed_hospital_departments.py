"""seed fixed hospital departments

Revision ID: 3b150980e45e
Revises: fbb49dd809b0
Create Date: 2026-07-07 23:06:22.194781

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '3b150980e45e'
down_revision: Union[str, Sequence[str], None] = 'fbb49dd809b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

departments_table = sa.table(
    "departments",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("name", sa.String),
    sa.column("description", sa.Text),
    sa.column("status", sa.String),
    sa.column("created_at", sa.DateTime(timezone=True)),
)

SEED_DEPARTMENTS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "Emergency Department",
        "description": "Triage and treatment for acute, life-threatening conditions.",
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "General Ward",
        "description": "Inpatient care for admitted, non-critical patients.",
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "Laboratory",
        "description": "Diagnostic testing and lab result reporting.",
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "name": "Radiology",
        "description": "Imaging services (X-ray, CT, ultrasound).",
    },
    {
        "id": "00000000-0000-0000-0000-000000000005",
        "name": "Pharmacy",
        "description": "Medication dispensing and inventory management.",
    },
]


def upgrade() -> None:
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        departments_table,
        [
            {
                "id": dept["id"],
                "name": dept["name"],
                "description": dept["description"],
                "status": "active",
                "created_at": now,
            }
            for dept in SEED_DEPARTMENTS
        ],
    )


def downgrade() -> None:
    ids = tuple(dept["id"] for dept in SEED_DEPARTMENTS)
    op.get_bind().execute(
        sa.text("DELETE FROM departments WHERE id IN :ids").bindparams(
            sa.bindparam("ids", expanding=True)
        ),
        {"ids": ids},
    )
