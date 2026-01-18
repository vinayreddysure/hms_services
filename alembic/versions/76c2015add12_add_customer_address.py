"""add customer address

Revision ID: 76c2015add12
Revises: bcc1e31d8240
Create Date: 2026-01-18 03:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '76c2015add12'
down_revision: Union[str, None] = 'bcc1e31d8240'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add address columns to customers table
    op.add_column('customers', sa.Column('address', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('city', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('state', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('zip_code', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove address columns
    op.drop_column('customers', 'zip_code')
    op.drop_column('customers', 'state')
    op.drop_column('customers', 'city')
    op.drop_column('customers', 'address')
