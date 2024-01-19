import sqlalchemy as sa
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    userid = sa.Column(sa.Integer, unique=True)
    current_menu_id = sa.Column(sa.String)
    previous_menu_id = sa.Column(sa.String)
    language = sa.Column(sa.String)
    last_bot_pm_id = sa.Column(sa.Integer)

    def __repr__(self):
        return f'<User(id={self.id}, userid={self.userid}, language={self.language})>'
