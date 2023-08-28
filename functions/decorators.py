from functools import wraps

from pyrogram import Client
from pyrogram.errors import MessageNotModified, UserIsBlocked
from pyrogram.types import CallbackQuery

from utypes import UserSession


__all__ = ('ignore_blocking', 'ignore_message_not_modified')


def ignore_message_not_modified(func):
    """Decorator to ignore annoying `pyrogram.errors.MessageNotModified`."""

    @wraps(func)
    async def inner(client: Client, session: UserSession, callback_query: CallbackQuery, *args, **kwargs):
        try:
            await func(client, session, callback_query, *args, **kwargs)
        except MessageNotModified:
            pass

    return inner


def ignore_blocking(func):
    """Decorator to ignore `pyrogram.errors.UserIsBlocked`."""

    @wraps(func)
    async def inner(client: Client, *args, **kwargs):
        try:
            await func(client, *args, **kwargs)
        except UserIsBlocked:
            pass

    return inner
