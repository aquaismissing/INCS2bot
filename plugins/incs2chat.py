import asyncio
import logging
import random

import requests
from pyrogram import Client, filters
from pyrogram.enums import ChatMembersFilter, MessageEntityType
from pyrogram.types import Message, MessageEntity

# noinspection PyUnresolvedReferences
import env
import config


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


def convert_message_to_markdown_text(message: Message) -> str:
    """Convert Telegram formatting to Markdown (primarily for Discord)."""

    entity_type_to_markdown = {  # only includes simple closing entities
        MessageEntityType.BOLD:      '**',
        MessageEntityType.ITALIC:    '*',
        MessageEntityType.UNDERLINE: '__',
        MessageEntityType.STRIKETHROUGH: '~~',
        MessageEntityType.SPOILER: '||',
        MessageEntityType.CODE: '`'
    }

    text = message.text or message.caption or ''

    if message.entities is None:
        return text

    text = list(text)
    text_shift = 0
    for entity in message.entities:
        # special cases first
        if entity.type is MessageEntityType.TEXT_LINK:
            text.insert(entity.offset + text_shift, '[')
            text.insert(entity.offset + entity.length + text_shift + 1, f']({entity.url})')
            text_shift += 2
        if entity.type is MessageEntityType.PRE:
            text.insert(entity.offset + text_shift, f'```{entity.language}\n')
            text.insert(entity.offset + entity.length + text_shift + 1, f'\n```')
            text_shift += 2
        if entity.type is MessageEntityType.BLOCKQUOTE:
            text.insert(entity.offset + text_shift, '> ')
            text_shift += 1

        symbol = entity_type_to_markdown.get(entity.type)
        if symbol:
            previous_symbol = text[entity.offset + text_shift - 2]
            if previous_symbol in entity_type_to_markdown.values():  # todo: still fails on 3+ styles in the same chunk
                text.insert(entity.offset + text_shift - 1, symbol)
                text.insert(entity.offset + entity.length + text_shift, symbol)
            else:
                text.insert(entity.offset + text_shift, symbol)
                text.insert(entity.offset + entity.length + text_shift + 1, symbol)
            text_shift += 2
    return ''.join(text)


def translate_text(text: str, source_lang: str = 'RU', target_lang: str = 'EN') -> str | None:
    headers = {'Authorization': f'DeepL-Auth-Key {config.DEEPL_TOKEN}', 'Content-Type': 'application/json'}
    data = {'text': [text], 'source_lang': source_lang, 'target_lang': target_lang}

    r = requests.post('https://api-free.deepl.com/v2/translate', headers=headers, json=data)
    if r.status_code == 200:
        return r.json()['translations'][0]['text']

    logging.error('Failed to translate text.')
    logging.error(f'{text=}')
    logging.error(f'{r.status_code=}, {r.reason=}')


def post_to_discord_webhook(url: str, text: str):  # todo: attachments support?
    headers = {'Content-Type': 'application/json'}
    payload = {'content': text}
    r = requests.post(url, json=payload, headers=headers)

    if r.status_code != 204:  # Discord uses 204 as a success code (yikes)
        logging.error('Failed to post to Discord webhook.')
        logging.error(f'{text=}')
        logging.error(f'{r.status_code=}, {r.reason=}')


def process_ds_text(message: Message) -> list[str] | None:
    logging.info(message)

    text_list = [convert_message_to_markdown_text(message)]

    # DS webhook limit 2000 symbols (ahui), hope tg limit is <4000 if more pls fix
    if text_list[0]:
        if len(text_list[0]) > 2000:
            # splitting message into 2 similar-sized messages to save structure and beauty
            last_newline_index = text_list[0][:len(text_list[0]) // 2].rfind('\n')
            if last_newline_index != -1:
                second_part = text_list[0][last_newline_index + 1:]
                text_list.append(second_part)
                text_list[0] = text_list[0][:last_newline_index]

        return text_list


def forward_to_discord(message: Message):
    texts = process_ds_text(message)
    logging.info(texts)

    if texts:
        for text in texts:
            post_to_discord_webhook(config.DS_WEBHOOK_URL, text)
            post_to_discord_webhook(config.DS_WEBHOOK_URL_EN, translate_text(text, 'RU', 'EN'))


async def cs_l10n_update(message: Message):
    has_the_l10n_line = ((message.text and "Обновлены файлы локализации" in message.text)
                         or (message.caption and "Обновлены файлы локализации" in message.caption))

    if has_the_l10n_line:
        await message.reply_sticker('CAACAgIAAxkBAAID-l_9tlLJhZQSgqsMUAvLv0r8qhxSAAIKAwAC-p_xGJ-m4XRqvoOzHgQ')


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("ban"))
async def ban(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    admins = chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS)
    admins = {admin.user.id async for admin in admins}

    if message.from_user.id not in admins:
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    if message.reply_to_message:
        og_msg = message.reply_to_message
        await chat.ban_member(og_msg.from_user.id)
        await message.reply(f"{og_msg.from_user.first_name} получил(а) VAC бан.")


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("unban"))
async def unban(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)
    admins = chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS)
    admins = {admin.user.id async for admin in admins}

    if message.from_user.id not in admins:
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    if message.reply_to_message:
        og_msg = message.reply_to_message
        await chat.unban_member(og_msg.from_user.id)
        await message.reply(f"VAC бан у {og_msg.from_user.first_name} был удалён.")


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("warn"))
async def warn(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)
    admins = chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS)
    admins = {admin.user.id async for admin in admins}

    if message.from_user.id not in admins:
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    if message.reply_to_message:
        og_msg = message.reply_to_message
        await og_msg.reply_animation('CgACAgQAAx0CTFFE8AABCAWQZhBlULJVdtDBZfHrfrDasDc3TgEAApsDAALuLsxTbHEvGmmxl6geBA')
    await message.delete()


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command('echo'))
async def echo(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)
    admins = chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS)
    admins = {admin.user.id async for admin in admins}

    await message.delete()
    if message.from_user.id not in admins:
        return

    if message.reply_to_message:
        reply_to = message.reply_to_message
        should_reply = True
    else:
        reply_to = message
        should_reply = False

    if message.text:
        text = message.text.removeprefix('/echo').strip()
        entities = correct_message_entities(message.entities, message.text, text)

        if not text:
            msg = await message.reply('Пустой текст.', quote=False)
            await asyncio.sleep(5)
            await msg.delete()
            return

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
async def handle_new_post(_, message: Message):
    is_sent_by_correct_chat = (message.sender_chat and message.sender_chat.id == config.INCS2CHANNEL)
    is_forwarded_from_correct_chat = (message.forward_from_chat and message.forward_from_chat.id == config.INCS2CHANNEL)

    if is_sent_by_correct_chat and is_forwarded_from_correct_chat:
        await cs_l10n_update(message)
        forward_to_discord(message)


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.forwarded)
async def filter_forwards(_, message: Message):
    if message.forward_from_chat and message.forward_from_chat.id in config.FILTER_FORWARDS:
        await message.delete()


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.sticker)
async def meow_meow_meow_meow(_, message: Message):
    chance = random.randint(0, 100)

    if message.sticker.file_unique_id == 'AgADtD0AAu4r4Ug' and chance < 5:
        await message.reply('мяу мяу мяу мяу')


# @Client.on_message(filters.chat(config.INCS2CHAT) & filters.animation)
# async def debugging_gifs(_, message: Message):
#     print(message.animation)
