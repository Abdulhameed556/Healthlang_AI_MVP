"""redesign department schema for hospital departments

Revision ID: fbb49dd809b0
Revises: ad778436d69b
Create Date: 2026-07-07 22:52:51.507438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fbb49dd809b0'
down_revision: Union[str, Sequence[str], None] = 'ad778436d69b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('departments', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
    op.execute('UPDATE departments SET created_at = onboarded_at')
    op.alter_column('departments', 'created_at', nullable=False)
    op.drop_column('departments', 'industry')
    op.drop_column('departments', 'onboarded_by')
    op.drop_column('departments', 'onboarded_at')
    op.drop_column('departments', 'size')


def downgrade() -> None:
    op.add_column('departments', sa.Column('size', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('departments', sa.Column('onboarded_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('departments', sa.Column('onboarded_by', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('departments', sa.Column('industry', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.execute("UPDATE departments SET onboarded_at = created_at, industry = 'unknown'")
    op.alter_column('departments', 'onboarded_at', nullable=False)
    op.alter_column('departments', 'industry', nullable=False)
    op.drop_column('departments', 'created_at')
