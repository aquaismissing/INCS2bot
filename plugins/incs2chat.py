import asyncio
import json
import logging
import random

from pyrogram import Client, filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.types import Chat, Message, MessageEntity, User

import config


MESSAGE_FILTERS_FILE = config.DATA_FOLDER / 'filtered.json'

if not MESSAGE_FILTERS_FILE.exists():
    with open(MESSAGE_FILTERS_FILE, 'w', encoding='utf-8') as _f:
        json.dump({'text': [], 'forwards': {}}, _f)


def load_message_filters() -> dict[str, list | dict[str, str]]:
    with open(MESSAGE_FILTERS_FILE, encoding='utf-8') as f:
        return json.load(f)


def dump_message_filters(_filters: dict[str, list | dict[str, str]]):
    with open(MESSAGE_FILTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(_filters, f, indent=4, ensure_ascii=False)


filtered_stuff = load_message_filters()  # {'text': [str], 'forwards': {id: username}}
if not filtered_stuff.get('text'):
    filtered_stuff = {'text': [], 'forwards': filtered_stuff.copy()}
    dump_message_filters(filtered_stuff)


logger = logging.getLogger('INCS2bot')


async def send_temp_reply(message: Message, text: str, timeout: int = 5, delete_original_before: bool = False):
    msg = await message.reply(text)
    if delete_original_before:
        await message.delete()
    await asyncio.sleep(timeout)
    if not delete_original_before:
        await message.delete()
    await msg.delete()
    return


async def is_administrator(chat: Chat, user: User) -> bool:
    admins = {admin.user.id async for admin in chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS)}

    return user.id in admins


def correct_message_entities(entities: list[MessageEntity] | None,
                             original_text: str, new_text: str) -> list[MessageEntity] | None:
    """Correct message entities (a.k.a. Markdown formatting) for edited text."""

    if entities is None:
        return

    length_diff = len(original_text) - len(new_text)

    entities_i_to_remove = []
    for i, entity in enumerate(entities):
        entity.offset -= length_diff

        if entity.offset < 0:
            entities_i_to_remove.append(i)

    for i in reversed(entities_i_to_remove):
        entities.pop(i)

    return entities


async def cs_l10n_update(message: Message):
    has_the_l10n_line = ((message.text and "Обновлены файлы локализации" in message.text)
                         or (message.caption and "Обновлены файлы локализации" in message.caption))

    if has_the_l10n_line:
        await message.reply_sticker('CAACAgIAAxkBAAID-l_9tlLJhZQSgqsMUAvLv0r8qhxSAAIKAwAC-p_xGJ-m4XRqvoOzHgQ')


async def filter_message(message: Message):
    senders_ids = set()

    if message.via_bot:
        senders_ids.add(message.via_bot.id)
    if message.forward_from:
        senders_ids.add(message.forward_from.id)
    if message.forward_from_chat:
        senders_ids.add(message.forward_from_chat.id)

    if (senders_ids & filtered_stuff['forwards'].keys()
            or (message.dice and message.dice.emoji in filtered_stuff['text'])
            or message.text in filtered_stuff['text']):  # todo: check for text *inclusion*, not equality?
        await message.delete()


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("addfilter"))
async def addfilter(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    if not await is_administrator(chat, message.from_user):
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    if message.command[1] == 'text':
        text = message.text.removeprefix('/addfilter text').strip(' "')
        return await addfilter_text(message, text)
    if message.command[1] == 'forward':
        return await addfilter_forward(message)

    msg = await message.reply('Укажите правильный тип фильтрации (`text`, `forward`).')
    await asyncio.sleep(5)
    await message.delete()
    await msg.delete()


async def addfilter_forward(message: Message):
    global filtered_stuff

    source_msg = message.reply_to_message
    if not source_msg:
        await send_temp_reply(message,
                              'Укажите ответом пересланное сообщение из канала, который вы хотите фильтровать.')
        return

    things_to_filter = {}
    for source in [source_msg.via_bot, source_msg.forward_from, source_msg.forward_from_chat]:
        if source:
            things_to_filter[source.id] = source.username

    if not things_to_filter:
        await send_temp_reply(message, 'Не удалось найти параметры, по которым можно применить фильтр.')
        return

    filtered_stuff['forwards'] |= things_to_filter
    dump_message_filters(filtered_stuff)
    await source_msg.delete()
    await send_temp_reply(message, 'Фильтр был успешно обновлён.', delete_original_before=True)


async def addfilter_text(message: Message, input_text: str = None):
    global filtered_stuff

    source_msg = message.reply_to_message

    if not (source_msg or input_text):
        await send_temp_reply(message, 'Укажите ответом сообщение или напишите текст в кавычках, '
                                       'по которому будет применятся фильтр.')
        return
    if source_msg and input_text:
        await send_temp_reply(message, 'Определитесь, к чему вы хотите применить фильтр: к тексту сообщения, '
                                       'на которое вы отвечаете, или же к тексту в самой команде.')
        return

    if source_msg:
        text_to_filter = source_msg.dice.emoji if source_msg.dice \
            else source_msg.text if source_msg.text \
            else source_msg.caption

        await source_msg.delete()
        message.reply_to_message = None
        return await addfilter_text(message, text_to_filter)

    if not input_text:
        await send_temp_reply(message, 'Пустой текст.')
        return

    filtered_stuff['text'].append(input_text)
    dump_message_filters(filtered_stuff)
    await send_temp_reply(message, 'Фильтр был успешно обновлён.', delete_original_before=True)


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("ban"))
async def ban(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    if not await is_administrator(chat, message.from_user):
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    original_msg = message.reply_to_message
    if original_msg:
        who_to_ban = original_msg.from_user or original_msg.sender_chat

        # if not chat.get_member(user_to_ban.id):  # probably already banned, untested
        #     return await message.reply(f"{user_to_ban.first_name} не находится в этом чате."
        #                                f" Возможно, он(а) уже получил(а) VAC бан.")

        await chat.ban_member(who_to_ban.id)
        await message.reply(f"{who_to_ban.first_name} получил(а) VAC бан.")


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("unban"))
async def unban(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    if not await is_administrator(chat, message.from_user):
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    if message.reply_to_message:
        original_msg = message.reply_to_message
        await chat.unban_member(original_msg.from_user.id)
        await message.reply(f"VAC бан у {original_msg.from_user.first_name} был удалён.")


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("warn"))
async def warn(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    if not await is_administrator(chat, message.from_user):
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    msg = message.reply_to_message
    if msg:
        await msg.reply_animation('CgACAgQAAx0CTFFE8AABCAWQZhBlULJVdtDBZfHrfrDasDc3TgEAApsDAALuLsxTbHEvGmmxl6geBA')
    await message.delete()


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command('echo'))
async def echo(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    await message.delete()
    if not await is_administrator(chat, message.from_user):
        return

    if message.reply_to_message:
        reply_to = message.reply_to_message
        should_reply = True
    else:
        reply_to = message
        should_reply = False

    if message.text:
        text = message.text.removeprefix('/echo').strip()

        if not text:
            msg = await message.reply('Пустой текст.', quote=False)
            await asyncio.sleep(5)
            await msg.delete()
            return

        entities = correct_message_entities(message.entities, message.text, text)
        return await reply_to.reply(text, entities=entities, quote=should_reply, disable_web_page_preview=True)

    caption = message.caption.removeprefix('/echo').strip()
    entities = correct_message_entities(message.entities, message.caption, caption)

    if message.animation:
        animation = message.animation.file_id
        return await reply_to.reply_animation(animation, quote=should_reply, caption=caption, caption_entities=entities)

    if message.audio:
        audio = message.audio.file_id
        return await reply_to.reply_audio(audio, quote=should_reply, caption=caption, caption_entities=entities)

    if message.document:
        document = message.document.file_id
        return await reply_to.reply_document(document, quote=should_reply, caption=caption, caption_entities=entities)

    if message.photo:
        photo = message.photo.file_id
        return await reply_to.reply_photo(photo, quote=should_reply, caption=caption, caption_entities=entities)

    if message.video:
        video = message.video.file_id
        return await reply_to.reply_video(video, quote=should_reply, caption=caption, caption_entities=entities)

    if message.voice:
        voice = message.voice.file_id
        return await reply_to.reply_voice(voice, quote=should_reply, caption=caption, caption_entities=entities)


@Client.on_message(filters.linked_channel & filters.chat(config.INCS2CHAT))
async def handle_new_post(_: Client, message: Message):
    is_sent_by_correct_chat = (message.sender_chat and message.sender_chat.id == config.INCS2CHANNEL)
    is_forwarded_from_correct_chat = (message.forward_from_chat and message.forward_from_chat.id == config.INCS2CHANNEL)

    if is_sent_by_correct_chat and is_forwarded_from_correct_chat:
        await cs_l10n_update(message)


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.dice)
async def filter_dices(_, message: Message):
    await filter_message(message)


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.text)
async def filter_text(_, message: Message):
    await filter_message(message)


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.forwarded)
async def filter_forwards(_, message: Message):
    await filter_message(message)


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.via_bot)
async def filter_via_bot(_, message: Message):
    await filter_message(message)


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.sticker)
async def meow_meow_meow_meow(_, message: Message):
    chance = random.random()

    if message.sticker.file_unique_id == 'AgADtD0AAu4r4Ug':
        if chance < 0.025:
            await message.reply('гав гав гав гав')
        elif chance < 0.075:
            await message.reply('мяу мяу мяу мяу')
