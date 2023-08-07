from pyrogram.types import CallbackQuery, Message

from keyboards import ExtendedIKM
from utypes import BClient


__all__ = ('ask_message_silently', 'ask_callback_silently')


async def ask_message_silently(client: BClient, callback_query: CallbackQuery,
                               text: str, *args, reply_markup: ExtendedIKM = None, **kwargs) -> Message:
    """Asks for a message in the same message."""

    await callback_query.edit_message_text(text, *args, reply_markup=reply_markup, **kwargs)
    return await client.listen_message(callback_query.message.chat.id)


async def ask_callback_silently(client: BClient, callback_query: CallbackQuery,
                                text: str, *args, reply_markup: ExtendedIKM = None, **kwargs) -> CallbackQuery:
    """Asks for a callback in the same message."""

    await callback_query.edit_message_text(text, *args, reply_markup=reply_markup, **kwargs)
    return await client.listen_callback(callback_query.message.chat.id, callback_query.message.id)
