import datetime as dt

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import (CallbackQuery, Message, MessageEntity,
                            InlineKeyboardMarkup, ReplyKeyboardMarkup,
                            ReplyKeyboardRemove, ForceReply, User)
# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!

from l10n import Locale


class UserSession:  # todo: sessions caching so we can restore them after reload
    def __init__(self, user: User):
        from functions import locale

        self.user = user
        self.timestamp = dt.datetime.now().timestamp()
        self.came_from: callable = None
        self.lang_code: str = user.language_code
        self.locale: Locale | None = locale(user.language_code)


class BClient(Client):
    """
    Custom pyrogram.Client class to add custom properties and methods and stop Pycharm annoy me.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._sessions: dict[int, UserSession] = {}
        self.current_session: UserSession | None = None

    @property
    def came_from(self):
        return self.current_session.came_from

    @property
    def session_lang_code(self):
        return self.current_session.lang_code

    @property
    def locale(self):
        return self.current_session.locale

    @property
    def sessions(self) -> dict[int, UserSession]:
        return self._sessions

    def register_session(self, user: User):
        self._sessions[user.id] = UserSession(user)

    def clear_timeout_sessions(self, *, hours: int = 1, minutes: int = 0, seconds: int = 0):
        now = dt.datetime.now()
        timeout_duration = dt.timedelta(hours=hours, minutes=minutes, seconds=seconds)

        for _id in self._sessions:
            session_time = dt.datetime.fromtimestamp(self._sessions[_id].timestamp)
            if now - session_time > timeout_duration:
                del self._sessions[_id]

    def clear_sessions(self):
        self._sessions.clear()

    async def listen_message(self,
                             chat_id: int,
                             filters=None,
                             timeout: int = None) -> Message:
        return await super().listen_message(chat_id, filters, timeout)

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
