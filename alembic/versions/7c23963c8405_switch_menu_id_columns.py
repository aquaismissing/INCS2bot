"""switch menu id columns

Revision ID: 7c23963c8405
Revises: ed349c808787
Create Date: 2023-10-26 19:25:32.730880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c23963c8405'
down_revision: Union[str, None] = 'ed349c808787'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'current_menu_id', new_column_name='temp')
    op.alter_column('users', 'previous_menu_id', new_column_name='current_menu_id')
    op.alter_column('users', 'temp', new_column_name='previous_menu_id')


def downgrade() -> None:
    op.alter_column('users', 'current_menu_id', new_column_name='temp')
    op.alter_column('users', 'previous_menu_id', new_column_name='current_menu_id')
    op.alter_column('users', 'temp', new_column_name='previous_menu_id')
