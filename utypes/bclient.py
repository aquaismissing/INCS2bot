import datetime as dt

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, Message, MessageEntity, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove, ForceReply

# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!

from l10n import Locale


class BClient(Client):
    """
    Custom pyrogram.Client class to add custom properties and methods and stop Pycharm annoy me.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.came_from: callable = None
        self.locale: Locale | None = None

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
