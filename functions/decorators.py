from pyrogram import Client
from pyrogram.types import CallbackQuery
from pyrogram.errors import MessageNotModified

from utypes import BClient


__all__ = ('came_from', 'ignore_message_not_modified')


def came_from(f):
    """
    Decorator that tracks from what function we came from and stores it in `BClient`.
    """
    def decorator(func):
        async def inner(client: BClient, callback_query: CallbackQuery, *args, **kwargs):
            client.came_from = f
            await func(client, callback_query, *args, **kwargs)

        return inner

    return decorator


def ignore_message_not_modified(func):
    """Decorator to ignore annoying `pyrogram.errors.MessageNotModified`."""

    async def inner(client: Client, callback_query: CallbackQuery, *args, **kwargs):
        try:
            await func(client, callback_query, *args, **kwargs)
        except MessageNotModified:
            pass

    return inner



