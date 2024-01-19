"""new columns in users table

Revision ID: ed349c808787
Revises: 
Create Date: 2023-10-26 18:37:56.584585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed349c808787'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('current_menu_id', sa.Integer))
    op.alter_column('users', 'came_from_id', new_column_name='previous_menu_id')


def downgrade() -> None:
    op.drop_column('users', 'current_menu_id')
    op.alter_column('users', 'previous_menu_id', new_column_name='came_from_id')
