"""create a phone number for user table column

Revision ID: 832d1000b9ff
Revises: 
Create Date: 2024-10-04 11:54:47.776732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '832d1000b9ff'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))


def downgrade() -> None:
    pass
    # op.drop_column('users', 'phone_number')  # type: ignore
