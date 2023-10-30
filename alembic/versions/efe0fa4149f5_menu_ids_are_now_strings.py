"""menu ids are now strings

Revision ID: efe0fa4149f5
Revises: 7c23963c8405
Create Date: 2023-10-29 11:30:03.039443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efe0fa4149f5'
down_revision: Union[str, None] = '7c23963c8405'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We must drop columns while upgrade or downgrade... that's unfortunate
    op.drop_column('users', 'current_menu_id')
    op.drop_column('users', 'previous_menu_id')
    op.add_column('users', sa.Column('current_menu_id', sa.String))
    op.add_column('users', sa.Column('previous_menu_id', sa.String))


def downgrade() -> None:
    op.drop_column('users', 'current_menu_id')
    op.drop_column('users', 'previous_menu_id')
    op.add_column('users', sa.Column('current_menu_id', sa.Integer))
    op.add_column('users', sa.Column('previous_menu_id', sa.Integer))
