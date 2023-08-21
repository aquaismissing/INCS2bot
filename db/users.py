import sqlalchemy
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    userid = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    came_from_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    language = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return f'<User(id={self.id}, userid={self.userid}, language={self.language})>'
