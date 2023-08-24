import datetime as dt
from pathlib import Path
import pickle

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (CallbackQuery, Message, MessageEntity,
                            InlineKeyboardMarkup, ReplyKeyboardMarkup,
                            ReplyKeyboardRemove, ForceReply, User)
# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!

from keyboards import ExtendedIKM


__all__ = ('BClient', 'UserSession')


class UserSession:
    __slots__ = ('user', 'timestamp', 'came_from', 'lang_code', 'locale')

    def __init__(self, user: User, *, force_lang: str = None):
        from functions import locale

        self.user = user
        self.timestamp = dt.datetime.now().timestamp()
        self.came_from: callable = None
        if force_lang:
            self.lang_code = force_lang
        else:
            self.lang_code = user.language_code
        self.locale = locale(self.lang_code)


class UserSessions(dict[int, UserSession]):
    def __getitem__(self, key):
        item = super().__getitem__(key)
        item.timestamp = dt.datetime.now().timestamp()
        return item


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

    def register_session(self, user: User, *, force_lang: str = None) -> UserSession:
        self._sessions[user.id] = UserSession(user, force_lang=force_lang)
        return self._sessions[user.id]

    def clear_timeout_sessions(self):
        """
        Clear all sessions that exceed given timeout.
        """

        now = dt.datetime.now()

        for _id in self._sessions:
            session_time = dt.datetime.fromtimestamp(self._sessions[_id].timestamp)
            if (now - session_time) > self.sessions_timeout:
                del self._sessions[_id]

    def load_sessions(self, path: Path):
        from functions import locale

        if not path.exists():
            self._sessions = UserSessions()
            return

        with open(path, 'rb') as f:
            self._sessions = pickle.load(f)

        self.clear_timeout_sessions()

        for session in self._sessions:
            # Update locale for loaded sessions
            session.locale = locale(self.lang_code)

    def dump_sessions(self, path: Path):
        self.clear_timeout_sessions()

        with open(path, 'wb') as f:
            pickle.dump(self._sessions, f)

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
