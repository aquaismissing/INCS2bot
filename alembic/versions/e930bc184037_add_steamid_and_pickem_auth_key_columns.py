"""Add steamid and pickem_auth_key columns

Revision ID: e930bc184037
Revises: b57e50910191
Create Date: 2024-02-19 16:54:19.166895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e930bc184037'
down_revision: Union[str, None] = 'b57e50910191'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('steamid', sa.Integer))
    op.add_column('users', sa.Column('pickem_auth_key', sa.String(length=15)))


def downgrade() -> None:
    op.drop_column('users', 'steamid')
    op.drop_column('users', 'pickem_auth_key')
