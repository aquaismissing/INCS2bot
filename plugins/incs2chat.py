import asyncio

from pyrogram import Client, filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.types import Message

# noinspection PyUnresolvedReferences
import env
import config


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
        await og_msg.reply_animation(config.MEDIA_PATH / 'warn.gif.mp4')
    await message.delete()


@Client.on_message(filters.chat(config.INCS2CHAT) & filters.command("echo"))
async def echo(client: Client, message: Message):  # todo: more attachments?
    chat = await client.get_chat(config.INCS2CHAT)
    admins = chat.get_members(filter=ChatMembersFilter.ADMINISTRATORS)
    admins = {admin.user.id async for admin in admins}

    await message.delete()
    if message.from_user.id not in admins:
        return

    reply_to = message
    should_reply = False
    if message.reply_to_message:
        reply_to = message.reply_to_message
        should_reply = True

    if message.animation:
        animation = message.animation.file_id
        caption = message.caption.removeprefix('/echo').strip()
        return await reply_to.reply_animation(animation, quote=should_reply, caption=caption)

    if message.audio:
        audio = message.audio.file_id
        caption = message.caption.removeprefix('/echo').strip()
        return await reply_to.reply_audio(audio, quote=should_reply, caption=caption)

    if message.photo:
        photo = message.photo.file_id
        caption = message.caption.removeprefix('/echo').strip()
        return await reply_to.reply_photo(photo, quote=should_reply, caption=caption)

    if message.text:
        text = message.text.removeprefix('/echo').strip()
        if not text:
            msg = await message.reply("Пустой текст.", quote=False)
            await asyncio.sleep(5)
            await msg.delete()
            return

        return await reply_to.reply(text, quote=should_reply)

    if message.video:
        video = message.video.file_id
        caption = message.caption.removeprefix('/echo').strip()
        return await reply_to.reply_video(video, quote=should_reply, caption=caption)


@Client.on_message(filters.linked_channel & filters.chat(config.INCS2CHAT))
async def cs_l10n_update(_, message: Message):
    if (message.sender_chat
            and message.sender_chat.id == config.INCS2CHANNEL
            and message.forward_from_chat.id == config.INCS2CHANNEL
            and "Обновлены файлы локализации" in message.text):
        await message.reply_sticker("CAACAgIAAxkBAAID-l_9tlLJhZQSgqsMUAvLv0r8qhxSAAIKAwAC-p_xGJ-m4XRqvoOzHgQ")
