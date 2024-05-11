from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyrogram.enums import ParseMode

    from pyrogram.types import (CallbackQuery, InlineQuery, Message,
                                ReplyKeyboardMarkup, User)

    from .botclient import BotClient
    from .sessions import UserSession


class SystemLogPayload(typing.NamedTuple):
    client: BotClient
    text: str
    disable_notification: bool
    reply_markup: ReplyKeyboardMarkup
    parse_mode: ParseMode


class EventLogPayload(typing.NamedTuple):
    client: BotClient
    user: User
    session: UserSession
    result_text: str


SYSTEM = 'system'


class BotLogger:
    """Made to work in a pair with BotClient handling logging stuff."""

    def __init__(self, log_channel_id: int):
        self.log_channel_id = log_channel_id
        self._logs_queue: dict[str, list[SystemLogPayload | EventLogPayload]] = {}

    def is_queue_empty(self):
        return not bool(self._logs_queue)

    def put_into_queue(self, _id: str, payload: SystemLogPayload | EventLogPayload):
        if self._logs_queue.get(_id) is None:
            self._logs_queue[_id] = []

        self._logs_queue[_id].append(payload)

    async def process_queue(self):
        if not self.is_queue_empty():
            userid = tuple(self._logs_queue)[0]
            logged_events = self._logs_queue[userid]

            if userid == SYSTEM:  # invoked by system, not user
                system_log = logged_events.pop(0)
                return await self.send_log(system_log.client,
                                           system_log.text,
                                           system_log.disable_notification,
                                           system_log.reply_markup,
                                           system_log.parse_mode)

            del self._logs_queue[userid]
            client = logged_events[-1].client
            user = logged_events[-1].user
            session = logged_events[-1].session
            display_name = f'@{user.username}' if user.username is not None else f'{user.mention} (username hidden)'

            text = [f'👤: {display_name}',
                    f'ℹ️: {userid}',
                    f'✈️: {user.language_code}',
                    f'⚙️: {session.locale.lang_code}',
                    f'━━━━━━━━━━━━━━━━━━━━━━━━'] + [event.result_text for event in logged_events]
            return await self.send_log(client, '\n'.join(text), disable_notification=True)

    async def schedule_system_log(self, client: BotClient, text: str,
                                  disable_notification: bool = True,
                                  reply_markup: ReplyKeyboardMarkup = None,
                                  parse_mode: ParseMode = None):
        """Put sending a system log into the queue."""

        self.put_into_queue(SYSTEM, SystemLogPayload(client, text, disable_notification, reply_markup, parse_mode))

    async def send_log(self, client: BotClient, text: str,
                       disable_notification: bool = True,
                       reply_markup: ReplyKeyboardMarkup = None,
                       parse_mode: ParseMode = None):
        """Sends log to the log channel immediately, avoiding the queue."""

        await client.send_message(self.log_channel_id, text,
                                  disable_notification=disable_notification,
                                  reply_markup=reply_markup,
                                  parse_mode=parse_mode)

    async def schedule_message_log(self, client: BotClient, session: UserSession, message: Message):
        """Put sending a message log into the queue."""

        user = message.from_user
        message_text = message.text if message.text is not None else ""

        self.put_into_queue(str(message.from_user.id), EventLogPayload(client, user, session, f'✍️: "{message_text}"'))

    async def schedule_callback_log(self, client: BotClient, session: UserSession, callback_query: CallbackQuery):
        """Put sending a callback query log into the queue"""

        user = callback_query.from_user

        self.put_into_queue(str(user.id), EventLogPayload(client, user, session, f'🔀: {callback_query.data}'))

    async def schedule_inline_log(self, client: BotClient, session: UserSession, inline_query: InlineQuery):
        """Put sending an inline query log into the queue."""

        user = inline_query.from_user

        self.put_into_queue(str(user.id), EventLogPayload(client, user, session, f'🛰: "{inline_query.query}"'))
