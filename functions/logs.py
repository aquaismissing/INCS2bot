import asyncio
import datetime as dt

from pyrogram.types import CallbackQuery, InlineQuery, Message

import config
from utypes import BClient, UserSession


__all__ = ('log', 'log_message', 'log_callback', 'log_inline')


async def log(client: BClient, text: str, no_log_in_test: bool = False, disable_notification: bool = True):
    """Sends log to the log channel."""

    asyncio.create_task(_log(client, text, no_log_in_test, disable_notification))


async def log_message(client: BClient, session: UserSession, message: Message):
    """Sends message log to the log channel."""

    asyncio.create_task(_log_message(client, session, message))


async def log_callback(client: BClient, session: UserSession, callback_query: CallbackQuery):
    """Sends callback log to the log channel."""

    asyncio.create_task(_log_callback(client, session, callback_query))


async def log_inline(client: BClient, session: UserSession, inline_query: InlineQuery):
    """Sends an inline query to the log channel."""

    asyncio.create_task(_log_inline(client, session, inline_query))


async def _log(client: BClient, text: str, no_log_in_test: bool, disable_notification: bool):
    if no_log_in_test and config.TEST_MODE:
        return

    if not client.can_log:
        seconds = client.can_log_after_time.seconds
        client.latest_log_dt = dt.datetime.now()  # to ensure that we won't get two logs at the same time
        await asyncio.sleep(seconds)
    client.latest_log_dt = dt.datetime.now()

    await client.send_message(config.LOGCHANNEL, text, disable_notification=disable_notification)


async def _log_message(client: BClient, session: UserSession, message: Message):
    if config.TEST_MODE:
        return

    if not client.can_log:
        seconds = client.can_log_after_time.seconds
        client.latest_log_dt = dt.datetime.now()  # to ensure that we won't get two logs at the same time and fail order
        await asyncio.sleep(seconds)
    client.latest_log_dt = dt.datetime.now()

    username = message.from_user.username
    display_name = f'@{username}' if username is not None else f'{message.from_user.mention} (username hidden)'

    text = (
        f"✍️ User: {display_name}\n"
        f"ID: {message.from_user.id}\n"
        f"Telegram language: {message.from_user.language_code}\n"
        f"Chosen language: {session.locale.lang_code}\n"
        f"Private message: {message.text!r}"
    )
    await client.send_message(config.LOGCHANNEL, text, disable_notification=True)


async def _log_callback(client: BClient, session: UserSession, callback_query: CallbackQuery):
    if config.TEST_MODE:
        return

    if not client.can_log:
        seconds = client.can_log_after_time.seconds
        client.latest_log_dt = dt.datetime.now()  # to ensure that we won't get two logs at the same time and fail order
        await asyncio.sleep(seconds)
    client.latest_log_dt = dt.datetime.now()

    username = callback_query.from_user.username
    display_name = f'@{username}' if username is not None else f'{callback_query.from_user.mention} (username hidden)'

    text = (
        f"🔀 User: {display_name}\n"
        f"ID: {callback_query.from_user.id}\n"
        f"Telegram language: {callback_query.from_user.language_code}\n"
        f"Chosen language: {session.locale.lang_code}\n"
        f"Callback query: {callback_query.data}"
    )
    await client.send_message(config.LOGCHANNEL, text, disable_notification=True)


async def _log_inline(client: BClient, session: UserSession, inline_query: InlineQuery):
    if config.TEST_MODE:
        return

    if not client.can_log:
        seconds = client.can_log_after_time.seconds
        client.latest_log_dt = dt.datetime.now()  # to ensure that we won't get two logs at the same time and fail order
        await asyncio.sleep(seconds)
    client.latest_log_dt = dt.datetime.now()

    username = inline_query.from_user.username
    display_name = f'@{username}' if username is not None else f'{inline_query.from_user.mention} (username hidden)'

    text = (
        f"🛰 User: {display_name}\n"
        f"ID: {inline_query.from_user.id}\n"
        f"Telegram language: {inline_query.from_user.language_code}\n"
        f"Chosen language: {session.locale.lang_code}\n"
        f"Inline query: {inline_query.query!r}"
    )
    await client.send_message(config.LOGCHANNEL, text, disable_notification=True)
