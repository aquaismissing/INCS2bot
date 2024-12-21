from __future__ import annotations

import datetime as dt
import logging

from pyrogram.types import Message, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import db_session, User as DBUser


__all__ = ('UserSession', 'UserSessions')


logger = logging.getLogger('INCS2bot.sessions')


class UserSession:
    __slots__ = ('dbuser_id', 'timestamp', 'current_menu_id',
                 'previous_menu_id', 'lang_code', 'last_bot_pm_id',
                 'locale')

    def __init__(self, dbuser: DBUser):
        from functions import locale

        self.dbuser_id = dbuser.id
        self.timestamp = dt.datetime.now().timestamp()
        self.current_menu_id = dbuser.current_menu_id
        self.previous_menu_id = dbuser.previous_menu_id
        self.lang_code = dbuser.language
        self.last_bot_pm_id = dbuser.last_bot_pm_id
        self.locale = locale(self.lang_code)

    async def sync_with_db_session(self, db_sess: AsyncSession):
        """Don't forget to call ``await db_sess.commit()`` to save changes!!!"""

        # noinspection PyTypeChecker
        query = select(DBUser).where(DBUser.id == self.dbuser_id)
        dbuser = (await db_sess.execute(query)).scalar()
        dbuser.current_menu_id = self.current_menu_id
        dbuser.previous_menu_id = self.previous_menu_id
        dbuser.language = self.lang_code
        dbuser.last_bot_pm_id = self.last_bot_pm_id
        return dbuser

    async def sync_with_db(self):
        async with db_session.create_session() as db_sess:
            dbuser = await self.sync_with_db_session(db_sess)
            logger.info(f'UserSession synced with db! {dbuser=}')
            await db_sess.commit()

    def update_lang(self, lang_code: str):
        from functions import locale

        self.lang_code = lang_code
        self.locale = locale(self.lang_code)


class UserSessions(dict[int, UserSession]):
    SESSIONS_LIFETIME = dt.timedelta(hours=1)

    def __getitem__(self, key: int):
        item = super().__getitem__(key)
        item.timestamp = dt.datetime.now().timestamp()
        return item

    async def sync_with_db(self):
        async with db_session.create_session() as db_sess:
            for session in self.values():
                await session.sync_with_db_session(db_sess)

            logger.info(f'UserSessions synced with db! {len(self)} sessions were synced.')
            await db_sess.commit()

    async def register_session(self, user: User, message: Message) -> UserSession:
        if user.id in self:
            return self[user.id]

        logger.info(f'Registering session with user {user.id=}, {user.username=}, {user.language_code=}')

        async with db_session.create_session() as db_sess:
            query = select(DBUser).where(DBUser.userid == user.id)
            dbuser = (await db_sess.execute(query)).scalar()
            if dbuser is None:
                dbuser = DBUser(userid=user.id,
                                language=user.language_code,
                                last_bot_pm_id=message.id if message else None)
                db_sess.add(dbuser)
                await db_sess.commit()
                logger.info(f'New record in db! {dbuser=}')
            else:
                logger.info(f'Got existing record in db. {dbuser=}')

        self[user.id] = UserSession(dbuser)

        return self[user.id]

    async def clear_timeout_sessions(self):
        """Clear all sessions that exceed given timeout."""

        now = dt.datetime.now()

        sessions_timed_out = 0
        async with db_session.create_session() as db_sess:
            for _id, session in self.copy().items():
                session_time = dt.datetime.fromtimestamp(session.timestamp)
                if (now - session_time) > self.SESSIONS_LIFETIME:
                    await session.sync_with_db_session(db_sess)
                    del self[_id]
                    sessions_timed_out += 1

            await db_sess.commit()

        if sessions_timed_out != 0:
            logger.info(f'Cleared {sessions_timed_out} timed-out sessions.')
