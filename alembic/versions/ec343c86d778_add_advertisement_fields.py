"""add advertisement fields

Revision ID: ec343c86d778
Revises: c614a2d68120
Create Date: 2026-10-19 01:08:47.979404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec343c86d778'
down_revision: Union[str, Sequence[str], None] = 'c614a2d68120'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('advertisements', sa.Column('reference_id', sa.String(length=50), nullable=True))
    op.add_column('advertisements', sa.Column('bedrooms', sa.Integer(), nullable=True))
    op.add_column('advertisements', sa.Column('property_type', sa.String(length=100), nullable=True))
    op.add_column('advertisements', sa.Column('transaction_type', sa.String(length=50), nullable=True))
    op.add_column('advertisements', sa.Column('phone_numbers', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('advertisements', 'phone_numbers')
    op.drop_column('advertisements', 'transaction_type')
    op.drop_column('advertisements', 'property_type')
    op.drop_column('advertisements', 'bedrooms')
    op.drop_column('advertisements', 'reference_id')
