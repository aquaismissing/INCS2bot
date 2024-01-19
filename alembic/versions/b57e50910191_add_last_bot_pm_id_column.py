"""Add 'last_bot_pm_id' column

Revision ID: b57e50910191
Revises: efe0fa4149f5
Create Date: 2023-12-10 20:11:52.220633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b57e50910191'
down_revision: Union[str, None] = 'efe0fa4149f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_bot_pm_id', sa.Integer))


def downgrade() -> None:
    op.drop_column('users', 'last_bot_pm_id')
