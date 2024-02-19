from steam import ID as SteamID
import sqlalchemy as sa
from sqlalchemy.orm import validates
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
    steamid = sa.Column(sa.Integer)
    pickem_auth_key = sa.Column(sa.String(length=15))

    def __repr__(self):
        return f'<User(userid={self.userid}, language={self.language})>'

    @validates('steamid')
    def validate_steamid(self, _, value):
        if not SteamID(value).is_valid():
            raise ValueError(f'Invalid SteamID: {value}')
        return value

    @validates('pickem_auth_key')
    def validate_pickem_auth_key(self, _, value):
        valid = (value[4] == value[10] == '-' and value.count('-') == 2)
        if not valid:
            raise ValueError(f'Invalid Pick\'Em auth key: {value}')
        return value
