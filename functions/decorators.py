from functools import wraps

from pyrogram.errors import MessageNotModified


__all__ = ['ignore_message_not_modified']


def ignore_message_not_modified(func):
    @wraps(func)
    async def inner(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except MessageNotModified:
            pass

    return inner
