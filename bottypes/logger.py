from __future__ import annotations

from abc import ABC, abstractmethod
import typing

if typing.TYPE_CHECKING:
    from pyrogram.enums import ParseMode

    from pyrogram.types import (CallbackQuery, InlineQuery, InlineKeyboardMarkup, Message, User)

    from .botclient import BotClient
    from .sessions import UserSession


def limit_message_length(text: str, limit: int = 4000) -> str:
    warning_message = ('\n\n'
                       '&lt;The original log message is too long to display fully.&gt;\n'
                       '&lt;Syb: looks like some shit really hit the fan&gt;')

    if len(text) <= limit:
        return text

    return text[:limit - len(warning_message) - 3] + '...' + warning_message


class SystemLogPayload(typing.NamedTuple):
    client: BotClient
    text: str
    disable_notification: bool
    reply_markup: InlineKeyboardMarkup
    parse_mode: ParseMode


class EventLogPayload(typing.NamedTuple):
    client: BotClient
    user: User
    session: UserSession
    result_text: str


SYSTEM = 'system'


class BotLogger(ABC):
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
        """If the queue is not empty, takes the first request from it, deserialize it and send as a log."""

        if self.is_queue_empty():
            return

        userid = tuple(self._logs_queue)[0]
        logged_events = self._logs_queue[userid]

        if userid == SYSTEM:  # invoked by system, not user
            payload = logged_events.pop(0)

            if not logged_events:  # if empty after popping
                del self._logs_queue[userid]

            return await self.send_system_log(payload)

        del self._logs_queue[userid]
        return await self.send_event_log(logged_events)

    async def schedule_system_log(self, client: BotClient, text: str,
                                  disable_notification: bool = True,
                                  reply_markup: InlineKeyboardMarkup = None,
                                  parse_mode: ParseMode = None):
        """Put sending a system log into the queue."""

        self.put_into_queue(SYSTEM, SystemLogPayload(client, text, disable_notification, reply_markup, parse_mode))

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

    async def send_log(self, client: BotClient, text: str,
                       disable_notification: bool = True,
                       reply_markup: InlineKeyboardMarkup = None,
                       parse_mode: ParseMode = None):
        """Sends log to the log channel immediately, avoiding the queue."""

        await client.send_message(self.log_channel_id, limit_message_length(text),
                                  disable_notification=disable_notification,
                                  reply_markup=reply_markup,
                                  parse_mode=parse_mode)

    @abstractmethod
    async def send_system_log(self, payload: SystemLogPayload):
        """Sends log to the log channel immediately, avoiding the queue."""

        raise NotImplementedError

    @abstractmethod
    async def send_event_log(self, payload: list[EventLogPayload],
                             reply_markup: InlineKeyboardMarkup = None):
        """Sends log to the log channel immediately, avoiding the queue."""

        raise NotImplementedError


class PlainBotLogger(BotLogger):
    """Made to work in a pair with BotClient handling logging stuff."""

    async def send_system_log(self, payload: SystemLogPayload):
        """Sends log to the log channel immediately, avoiding the queue."""

        return await self.send_log(payload.client,
                                   payload.text,
                                   payload.disable_notification,
                                   payload.reply_markup,
                                   payload.parse_mode)

    async def send_event_log(self, payloads: list[EventLogPayload],
                             reply_markup: InlineKeyboardMarkup = None):
        """Sends log to the log channel immediately, avoiding the queue."""
        client = payloads[-1].client
        user = payloads[-1].user
        session = payloads[-1].session
        display_name = f'@{user.username}' if user.username is not None else f'{user.mention} (username hidden)'

        text = [f'👤: {display_name}',
                f'ℹ️: {user.id}',
                f'✈️: {user.language_code}',
                f'⚙️: {session.locale.lang_code}',
                f'━━━━━━━━━━━━━━━━━━━━━━━'] + [event.result_text for event in payloads]

        return await self.send_log(client, '\n'.join(text),
                                   reply_markup=reply_markup)


class ReplyBackBotLogger(BotLogger):
    def __init__(self, log_channel_id: int,
                 event_reply_markup_builder: typing.Callable[[User], InlineKeyboardMarkup] = lambda _: None):
        super().__init__(log_channel_id)

        self.event_reply_markup_builder = event_reply_markup_builder

    async def send_system_log(self, payload: SystemLogPayload):
        """Sends log to the log channel immediately, avoiding the queue."""

        return await self.send_log(payload.client,
                                   payload.text,
                                   payload.disable_notification,
                                   payload.reply_markup,
                                   payload.parse_mode)

    async def send_event_log(self, payloads: list[EventLogPayload],
                             reply_markup: InlineKeyboardMarkup = None):
        """Sends log to the log channel immediately, avoiding the queue."""
        client = payloads[-1].client
        user = payloads[-1].user
        session = payloads[-1].session
        display_name = f'@{user.username}' if user.username is not None else f'{user.mention} (username hidden)'

        text = [f'👤: {display_name}',
                f'ℹ️: {user.id}',
                f'✈️: {user.language_code}',
                f'⚙️: {session.locale.lang_code}',
                f'━━━━━━━━━━━━━━━━━━━━━━━'] + [event.result_text for event in payloads]

        return await self.send_log(client, '\n'.join(text),
                                   reply_markup=self.event_reply_markup_builder(user))
