import datetime as dt
from functools import wraps
import logging

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (CallbackQuery, Message, MessageEntity,
                            InlineKeyboardMarkup, ReplyKeyboardMarkup,
                            ReplyKeyboardRemove, ForceReply, User)
# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!
from sqlalchemy.future import select

from db import db_session
from db.users import User as DBUser
from keyboards import ExtendedIKM


__all__ = ('BClient', 'UserSession')


class UserSession:
    __slots__ = ('dbuser_id', 'timestamp', 'came_from_id', 'lang_code', 'locale')

    def __init__(self, dbuser: DBUser, *, force_lang: str = None):
        from functions import locale

        self.dbuser_id = dbuser.id
        self.timestamp = dt.datetime.now().timestamp()
        self.came_from_id = dbuser.came_from_id
        self.lang_code = force_lang or dbuser.language
        self.locale = locale(self.lang_code)

    async def sync_with_db(self):
        async with db_session.create_session() as db_sess:
            # noinspection PyTypeChecker
            query = select(DBUser).where(DBUser.id == self.dbuser_id)
            # noinspection PyUnresolvedReferences
            dbuser = (await db_sess.execute(query)).scalar()
            dbuser.came_from_id = self.came_from_id
            dbuser.language = self.lang_code

            logging.info(f'UserSession synced with db! {dbuser.came_from_id=}, {dbuser.language=}')
            await db_sess.commit()

    def update_lang(self, lang_code: str):
        from functions import locale

        self.lang_code = lang_code
        self.locale = locale(self.lang_code)


class UserSessions(dict[int, UserSession]):
    def __getitem__(self, key):
        item = super().__getitem__(key)
        item.timestamp = dt.datetime.now().timestamp()
        return item

    async def sync_with_db(self):
        async with db_session.create_session() as db_sess:
            for session in self.values():
                # noinspection PyTypeChecker
                query = select(DBUser).where(DBUser.id == session.dbuser_id)
                # noinspection PyUnresolvedReferences
                dbuser = (await db_sess.execute(query)).scalar()
                dbuser.came_from_id = session.came_from_id
                dbuser.language = session.lang_code

            logging.info(f'UserSessions synced with db! {len(self)} sessions were synced.')
            # noinspection PyUnresolvedReferences
            await db_sess.commit()


class BClient(Client):
    """
    Custom pyrogram.Client class to add custom properties and methods and stop Pycharm annoy me.
    """
    LOGS_TIMEOUT = dt.timedelta(seconds=4)  # define how often logs should be sent

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._sessions: UserSessions = UserSessions()

        self._available_commands: dict[str, callable] = {}
        self._available_functions: dict[str, callable] = {}

        self._came_from_functions: dict[int, callable] = {}
        self.sessions_timeout = dt.timedelta(hours=1)
        self.latest_log_dt = dt.datetime.now()  # todo: implement logs functions in BClient?

    @property
    def sessions(self) -> UserSessions:
        return self._sessions

    @property
    def can_log(self) -> bool:
        return (dt.datetime.now() - self.latest_log_dt) >= self.LOGS_TIMEOUT

    @property
    def can_log_after_time(self) -> dt.timedelta:
        return self.LOGS_TIMEOUT - (dt.datetime.now() - self.latest_log_dt)

    async def register_session(self, user: User, *, force_lang: str = None) -> UserSession:
        logging.info(f'Registering session with user {user.id=}, {user.username=}, {user.language_code=}')

        async with db_session.create_session() as db_sess:
            query = select(DBUser).where(DBUser.userid == user.id)
            # noinspection PyUnresolvedReferences
            dbuser = (await db_sess.execute(query)).scalar()
            if dbuser is None:
                dbuser = DBUser(userid=user.id,
                                language=user.language_code)
                db_sess.add(dbuser)
                # noinspection PyUnresolvedReferences
                await db_sess.commit()
                logging.info(f'New record in db! {dbuser=}')
            else:
                logging.info(f'Got existing record in db. {dbuser=}')

        self._sessions[user.id] = UserSession(dbuser, force_lang=force_lang)
        return self._sessions[user.id]

    async def clear_timeout_sessions(self):
        """
        Clear all sessions that exceed given timeout.
        """

        now = dt.datetime.now()

        for _id in self._sessions:
            session_time = dt.datetime.fromtimestamp(self._sessions[_id].timestamp)
            if (now - session_time) > self.sessions_timeout:
                await self._sessions[_id].sync_with_db()
                del self._sessions[_id]

    async def dump_sessions(self):
        await self.clear_timeout_sessions()
        await self._sessions.sync_with_db()

    def clear_sessions(self):
        self._sessions.clear()

    def on_command(self, command: str, *args, **kwargs):
        def decorator(func):
            self._available_commands['/' + command] = (func, args, kwargs)
            return func

        return decorator

    def on_callback_request(self, query: str, *args, **kwargs):
        def decorator(func):
            self._available_functions[query] = (func, args, kwargs)
            return func

        return decorator

    async def get_func_by_command(self, session: UserSession, message: Message):
        try:
            func, args, kwargs = self._available_commands[message.text]
        except KeyError:
            if '_' not in self._available_commands:
                return
            func, args, kwargs = self._available_commands['_']
        return await func(self, session, message, *args, **kwargs)

    async def get_func_by_callback(self, session: UserSession, callback_query: CallbackQuery):
        try:
            func, args, kwargs = self._available_functions[callback_query.data]
        except KeyError:
            if '_' not in self._available_functions:
                return
            func, args, kwargs = self._available_functions['_']
        return await func(self, session, callback_query, *args, **kwargs)

    def came_from(self, f: callable, _id: int = None):
        """
        Decorator to track from what functions we came from. Accepts explicit id as arg.
        """

        if f not in self._came_from_functions.values():
            i = _id or len(self._came_from_functions)  # getting id for new function
            self._came_from_functions[i] = f

        def decorator(func: callable):
            @wraps(func)
            async def inner(_, session: UserSession, callback_query: CallbackQuery, *args, **kwargs):
                session.came_from_id = [k for k, v in self._came_from_functions.items() if v is f][0]
                await func(self, session, callback_query, *args, **kwargs)

            return inner

        return decorator

    async def go_back(self, session: UserSession, callback_query: CallbackQuery):
        if session.came_from_id is None:
            if '_' not in self._available_functions:
                return
            func, args, kwargs = self._available_functions['_']
            return await func(self, session, callback_query, *args, **kwargs)

        came_from = self._came_from_functions[session.came_from_id]
        await came_from(self, session, callback_query)

    # noinspection PyUnresolvedReferences
    async def listen_message(self,
                             chat_id: int,
                             filters=None,
                             timeout: int = None) -> Message:
        return await super().listen_message(chat_id, filters, timeout)

    # noinspection PyUnresolvedReferences
    async def ask_message(self,
                          chat_id: int,
                          text: str,
                          filters=None,
                          timeout: int = None,
                          parse_mode: ParseMode = None,
                          entities: list[MessageEntity] = None,
                          disable_web_page_preview: bool = None,
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          schedule_date: dt.datetime = None,
                          protect_content: bool = None,
                          reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup |
                          ReplyKeyboardRemove | ForceReply = None) -> Message:
        return await super().ask_message(chat_id,
                                         text,
                                         filters,
                                         timeout,
                                         parse_mode,
                                         entities,
                                         disable_web_page_preview,
                                         disable_notification,
                                         reply_to_message_id,
                                         schedule_date,
                                         protect_content,
                                         reply_markup)

    # noinspection PyUnresolvedReferences
    async def listen_callback(self,
                              chat_id: int = None,
                              message_id: int = None,
                              inline_message_id: str = None,
                              filters=None,
                              timeout: int = None) -> CallbackQuery:
        return await super().listen_callback(chat_id,
                                             message_id,
                                             inline_message_id,
                                             filters,
                                             timeout)

    async def ask_message_silently(self, callback_query: CallbackQuery,
                                   text: str, *args, reply_markup: ExtendedIKM = None, **kwargs) -> Message:
        """Asks for a message in the same message."""

        await callback_query.edit_message_text(text, *args, reply_markup=reply_markup, **kwargs)
        return await self.listen_message(callback_query.message.chat.id)

    async def ask_callback_silently(self, callback_query: CallbackQuery,
                                    text: str, *args, reply_markup: ExtendedIKM = None, **kwargs) -> CallbackQuery:
        """Asks for a callback query in the same message."""

        await callback_query.edit_message_text(text, *args, reply_markup=reply_markup, **kwargs)
        return await self.listen_callback(callback_query.message.chat.id, callback_query.message.id)
