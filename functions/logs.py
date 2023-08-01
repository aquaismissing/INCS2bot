from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineQuery, Message

import config


__all__ = ('log', 'log_callback', 'log_inline')


async def log(client: Client, message: Message):
    """The bot sends log to log channel"""

    text = (
        f"✍️ User: <a href=\"tg://user?id={message.from_user.id}\">{message.from_user.first_name}</a>\n"
        f"ID: {message.from_user.id}\n"
        f"Language: {message.from_user.language_code}\n"
        f"Private message: {message.text}"
    )
    await client.send_message(config.LOGCHANNEL, text, disable_notification=True)


async def log_callback(client: Client, callback_query: CallbackQuery):
    """The bot sends log to log channel"""

    text = (
        f"✍️ User: <a href=\"tg://user?id={callback_query.from_user.id}\">{callback_query.from_user.first_name}</a>\n"
        f"ID: {callback_query.from_user.id}\n"
        f"Language: {callback_query.from_user.language_code}\n"
        f"Callback query: {callback_query.data}"
    )
    await client.send_message(config.LOGCHANNEL, text, disable_notification=True)


async def log_inline(client: Client, inline_query: InlineQuery):
    """The bot sends an inline query to the log channel"""

    text = (
        f"🛰 User: <a href=\"tg://user?id={inline_query.from_user.id}\">{inline_query.from_user.first_name}</a>\n"
        f"ID: {inline_query.from_user.id}\n"
        f"Language: {inline_query.from_user.language_code}\n"
        f"Inline query: {inline_query.query}"
    )
    await client.send_message(config.LOGCHANNEL, text, disable_notification=True)
