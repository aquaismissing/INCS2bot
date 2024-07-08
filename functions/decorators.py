from functools import wraps

from pyrogram import Client
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery

from bottypes import UserSession


__all__ = ['ignore_message_not_modified']


def ignore_message_not_modified(func):
    """Decorator to ignore annoying `pyrogram.errors.MessageNotModified`."""

    @wraps(func)
    async def inner(client: Client, session: UserSession, callback_query: CallbackQuery, *args, **kwargs):
        try:
            await func(client, session, callback_query, *args, **kwargs)
        except MessageNotModified:
            pass

    return inner
