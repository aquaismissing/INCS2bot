import asyncio
import json
import logging
import random
import re
from io import BytesIO

from pyrogram import Client, filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.types import Chat, Message, MessageEntity, User
import requests
from tgentity import to_md

import config


DISCORD_MESSAGE_LENGTH_LIMIT = 2000
MESSAGE_FILTERS_FILE = config.DATA_FOLDER / 'filtered.json'

if not MESSAGE_FILTERS_FILE.exists():
    with open(MESSAGE_FILTERS_FILE, 'w', encoding='utf-8') as _f:
        json.dump({'text': [], 'forwards': {}}, _f)


def load_message_filters() -> dict[str, list | dict[str, str]]:
    with open(MESSAGE_FILTERS_FILE, encoding='utf-8') as f:
        return json.load(f)


def dump_message_filters(_filters: dict[str, list | dict[str, str]]):
    with open(MESSAGE_FILTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(_filters, f, indent=4)


filtered_stuff = load_message_filters()  # {'text': [str], 'forwards': {id: username}}
if filtered_stuff.get('text') is None:
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


def to_discord_markdown(message: Message) -> str:
    text = (to_md(message)
            .replace(r'\.', '.')
            .replace(r'\(', '(')  # god bless this feels awful
            .replace(r'\)', ')'))
    text = re.sub(r'~([^~]+)~', r'~~\1~~', text)

    return text


def wrap_text(text: str, max_length: int) -> list[str]:
    """
    Wraps the given text into multiple sections with a length <= ``max_length``.

    Prioritises wrapping by newlines, then spaces.
    """

    if len(text) <= max_length:
        return [text]

    text_parts = []
    while len(text) > max_length:
        longest_possible_part = text[:max_length]
        last_char_index = longest_possible_part.rfind('\n')
        if last_char_index == -1:
            last_char_index = longest_possible_part.rfind(' ')
        if last_char_index == -1:
            last_char_index = max_length

        new_part = text[:last_char_index]
        text_parts.append(new_part)
        if text[last_char_index].isspace():
            last_char_index += 1
        text = text[last_char_index:]

    text_parts.append(text)

    return text_parts


def process_discord_text(message: Message) -> list[str]:
    text = (to_discord_markdown(message) if message.entities
            else message.caption if message.caption
            else message.text if message.text
            else '')

    # fixme: can break formatting if wrapping happens in the middle of formatted section
    # fixme: (e.g. "**some [split] wise words**")
    # fixme severity: low
    return wrap_text(text, DISCORD_MESSAGE_LENGTH_LIMIT)


def translate_text(text: str, source_lang: str = 'RU', target_lang: str = 'EN') -> str | None:
    headers = {'Authorization': f'DeepL-Auth-Key {config.DEEPL_TOKEN}', 'Content-Type': 'application/json'}
    data = {'text': [text], 'source_lang': source_lang, 'target_lang': target_lang}

    r = requests.post('https://api-free.deepl.com/v2/translate', headers=headers, json=data)
    if r.status_code == 200:
        return r.json()['translations'][0]['text']

    logger.error('Failed to translate text.')
    logger.error(f'{text=}')
    logger.error(f'{r.status_code=}, {r.reason=}')


def post_to_discord_webhook(url: str, text: str, attachment: BytesIO = None):
    payload = {'content': text}

    if attachment:
        payload = {'payload_json': (None, json.dumps(payload)), 'files[0]': (attachment.name, attachment.getbuffer())}
        r = requests.post(url, files=payload)
    else:
        headers = {'Content-Type': 'application/json'}
        r = requests.post(url, json=payload, headers=headers)

    if r.status_code not in [200, 204]:  # Discord uses 204 as a success code (yikes)
        logger.error('Failed to post to Discord webhook.')
        logger.error(f'{payload=}')
        logger.error(f'{r.status_code=}, {r.reason=}, {r.text=}')


async def forward_to_discord(client: Client, message: Message):
    texts = process_discord_text(message)

    attachment: BytesIO | None
    try:
        # fixme: for every attachment this ^ function will be called multiple times
        # fixme: this could be fixed if we keep track of media groups but too lazy to implement it properly
        attachment = await client.download_media(message, in_memory=True)
    except ValueError:
        attachment = None

    for text in texts:
        if attachment:
            post_to_discord_webhook(config.DS_WEBHOOK_URL, text, attachment)
            post_to_discord_webhook(config.DS_WEBHOOK_URL_EN, translate_text(text, 'RU', 'EN'), attachment)
            attachment = None
        else:
            post_to_discord_webhook(config.DS_WEBHOOK_URL, text)
            post_to_discord_webhook(config.DS_WEBHOOK_URL_EN, translate_text(text, 'RU', 'EN'))


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
            or message.text in filtered_stuff['text']):  # todo: check for text *inclusion*, not equality?
        await message.delete()


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("addfilter"))
async def addfilter(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    if not await is_administrator(chat, message.from_user):
        return await message.reply("Эта команда недоступна, Вы не являетесь разработчиком Valve.")

    if message.command[1] == 'text':
        return await addfilter_text(message)
    if message.command[1] == 'forward':
        return await addfilter_forward(message)

    msg = await message.reply('Укажите правильный тип фильтрации (`forward`).')
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

    if things_to_filter:
        filtered_stuff['forwards'] |= things_to_filter
        dump_message_filters(filtered_stuff)
        await source_msg.delete()
        await send_temp_reply(message, 'Фильтр был успешно обновлён.', delete_original_before=True)
    else:
        await send_temp_reply(message,
                              'Не удалось найти параметры, по которым можно применить фильтр.')


async def addfilter_text(message: Message):
    global filtered_stuff

    source_msg = message.reply_to_message

    if not source_msg and len(message.command) < 3:
        await send_temp_reply(message, 'Укажите ответом сообщение или напишите текст в кавычках, '
                                       'по которому будет применятся фильтр.')
        return
    if source_msg and len(message.command) >= 3:
        await send_temp_reply(message, 'Определитесь, к чему вы хотите применить фильтр: к тексту сообщения, '
                                       'на которое вы отвечаете, или же к тексту в самой команде.')
        return

    if source_msg:
        text_to_filter = source_msg.text if source_msg.text else source_msg.caption
        if not text_to_filter:
            await send_temp_reply(message, 'Пустой текст.')
            return
        filtered_stuff['text'].append(text_to_filter)
        dump_message_filters(filtered_stuff)
        await source_msg.delete()
        await send_temp_reply(message, 'Фильтр был успешно обновлён.', delete_original_before=True)
        return

    if len(message.command) != 3:
        await send_temp_reply(message, 'Укажите только один текст, в кавычках.')
        return

    text_to_filter = message.command[2]
    if not text_to_filter:
        await send_temp_reply(message, 'Пустой текст.')
        return

    filtered_stuff['text'].append(text_to_filter)
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


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("check"))
async def check(client: Client, message: Message):
    chat = await client.get_chat(config.INCS2CHAT)

    await message.delete()
    if not await is_administrator(chat, message.from_user):
        return

    original_message = message.reply_to_message
    receipt = message.from_user
    await client.send_message(receipt.id, f'```\n{original_message}\n```')


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
async def handle_new_post(client: Client, message: Message):
    is_sent_by_correct_chat = (message.sender_chat and message.sender_chat.id == config.INCS2CHANNEL)
    is_forwarded_from_correct_chat = (message.forward_from_chat and message.forward_from_chat.id == config.INCS2CHANNEL)

    if is_sent_by_correct_chat and is_forwarded_from_correct_chat:
        await cs_l10n_update(message)
        await forward_to_discord(client, message)


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

    replies = {
        "AgADtD0AAu4r4Ug": {
            "rare": "мяу мяу мяу мяу",
            "epic": "гав гав гав гав"
        },
        "AQADQ1wAAvi0sEty": {
            "rare": "урм урм урм урм",
            "epic": "уям уям уям уям"
        },
        "AQADJ2QAAoTrqEhy": {
            "rare": "Как же я сука ненавижу cs2, вы бля не представляете, это сука самая ущербная игра в мире в которую играют одни пидорасы ебанные, как же мне не хватает слов что бы кратко описать насколько они ебанаты тупые вы бля просто не представляете, сука уже 2025 год наступил, а у нас валв с лета забросили игру, да и хуй с ней да, но сука у нас операции все еще нет, они там че совсем пидорасы ахуели при чем щас эти яйцеголовые делали артифакт блять которые поиграют сумарно за месяц дай боже население села ебанного, сука да даже их продукты хуйней стали, стим и так был говном ебанным, как же блять горит на этих людей которые там сидят, я бы нахуй фокус покус минус крокус бы там сделал бы нахуй, пускай в чате геи появятся, пускай там будут войсеры-трансгендеры, мне похуй это обозначит что донка забанят и будет тотальная гойда для всего земного шара, а пока всему чату желаю всегл наилучшего, что бы хуй стоял и что бы деньги были",
            "epic": "Согласен."
        }
    }

    if chance < 0.025:
        chance = "epic"
    elif chance < 0.075:
        chance = "rare"
    reply = replies.get(message.sticker.file_unique_id, None)
    if reply is not None:
        await message.reply(reply[chance])
