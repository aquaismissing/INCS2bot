from functools import wraps

from pyrogram import Client
from pyrogram.errors import MessageNotModified, UserIsBlocked
from pyrogram.types import CallbackQuery

from utypes import BClient, UserSession


__all__ = ('came_from', 'ignore_blocking', 'ignore_message_not_modified')


def came_from(f):
    """
    Decorator that tracks from what function we came from and stores it in `UserSession`.
    """

    def decorator(func):
        @wraps(func)
        async def inner(client: BClient, session: UserSession, callback_query: CallbackQuery, *args, **kwargs):
            session.came_from = f
            await func(client, session, callback_query, *args, **kwargs)

        return inner

    return decorator


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
    async def inner(client: Client, session: UserSession, callback_query: CallbackQuery, *args, **kwargs):
        try:
            await func(client, session, callback_query, *args, **kwargs)
        except UserIsBlocked:
            pass

    return inner
