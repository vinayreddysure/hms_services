"""reset active bookings

Revision ID: 99c2015reset
Revises: 76c2015add12
Create Date: 2026-01-18 03:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '99c2015reset'
down_revision: Union[str, None] = '76c2015add12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Mark all Active bookings as Completed
    op.execute("UPDATE bookings SET status = 'Completed', actual_check_out_at = NOW() WHERE status = 'Active'")
    
    # 2. Mark all Occupied rooms as Available
    op.execute("UPDATE rooms SET status = 'A' WHERE status = 'O'")


def downgrade() -> None:
    # Cannot easily reverse a bulk update without backing up data.
    # We will assume this is a one-way cleanup operation.
    pass
