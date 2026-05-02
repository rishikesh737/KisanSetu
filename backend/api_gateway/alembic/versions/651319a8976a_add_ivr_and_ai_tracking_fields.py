"""add_ivr_and_ai_tracking_fields

Revision ID: 651319a8976a
Revises: 8570d45bcea1
Create Date: 2026-05-02 19:20:04.849693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '651319a8976a'
down_revision: Union[str, Sequence[str], None] = '8570d45bcea1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
