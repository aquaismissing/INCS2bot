from __future__ import annotations

import asyncio
import typing

if typing.TYPE_CHECKING:
    from typing import Coroutine
    from pyrogram.enums import ParseMode

    from pyrogram.types import (CallbackQuery, InlineQuery, Message,
                                ReplyKeyboardMarkup)

    from .botclient import BotClient
    from .sessions import UserSession


class BotLogger:
    """Made to work in a pair with BotClient handling logging stuff."""

    def __init__(self, log_channel_id: int, ):
        self.log_channel_id = log_channel_id
        self._logs_queue = asyncio.Queue()

    def is_queue_empty(self):
        return self._logs_queue.empty()

    async def put_into_queue(self, coroutine: Coroutine):
        await self._logs_queue.put(coroutine)

    async def process_queue(self):
        if not self.is_queue_empty():
            coroutine = await self._logs_queue.get()
            await coroutine

    async def log(self, client: BotClient, text: str,
                  disable_notification: bool = True,
                  reply_markup: ReplyKeyboardMarkup = None,
                  parse_mode: ParseMode = None):
        """Put sending a log into the queue."""

        await self._logs_queue.put(self.log_instantly(client, text,
                                                      disable_notification,
                                                      reply_markup,
                                                      parse_mode))

    async def log_instantly(self, client: BotClient, text: str,
                            disable_notification: bool = True,
                            reply_markup: ReplyKeyboardMarkup = None,
                            parse_mode: ParseMode = None):
        """Sends log to the log channel instantly."""

        await client.send_message(self.log_channel_id, text,
                                  disable_notification=disable_notification,
                                  reply_markup=reply_markup,
                                  parse_mode=parse_mode)

    async def log_message(self, client: BotClient, session: UserSession, message: Message):
        """Put sending a message log into the queue."""

        username = message.from_user.username
        display_name = f'@{username}' if username is not None else f'{message.from_user.mention} (username hidden)'

        text = (f'✍️ User: {display_name}\n'
                f'ID: {message.from_user.id}\n'
                f'Telegram language: {message.from_user.language_code}\n'
                f'Chosen language: {session.locale.lang_code}\n'
                f'Private message: "{message.text if message.text is not None else ""}"')
        await self._logs_queue.put(client.send_message(self.log_channel_id, text, disable_notification=True))

    async def log_callback(self, client: BotClient, session: UserSession, callback_query: CallbackQuery):
        """Put sending a callback query log into the queue"""

        username = callback_query.from_user.username
        display_name = f'@{username}' if username is not None \
            else f'{callback_query.from_user.mention} (username hidden)'

        text = (f'🔀 User: {display_name}\n'
                f'ID: {callback_query.from_user.id}\n'
                f'Telegram language: {callback_query.from_user.language_code}\n'
                f'Chosen language: {session.locale.lang_code}\n'
                f'Callback query: {callback_query.data}')
        await self._logs_queue.put(client.send_message(self.log_channel_id, text, disable_notification=True))

    async def log_inline(self, client: BotClient, session: UserSession, inline_query: InlineQuery):
        """Put sending an inline query log into the queue."""

        username = inline_query.from_user.username
        display_name = f'@{username}' if username is not None else f'{inline_query.from_user.mention} (username hidden)'

        text = (f'🛰 User: {display_name}\n'
                f'ID: {inline_query.from_user.id}\n'
                f'Telegram language: {inline_query.from_user.language_code}\n'
                f'Chosen language: {session.locale.lang_code}\n'
                f'Inline query: "{inline_query.query}"')
        await self._logs_queue.put(client.send_message(self.log_channel_id, text, disable_notification=True))
