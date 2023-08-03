import json
import logging
import time
from threading import Thread

import asyncio
from pyrogram import Client
from pyrogram.enums import ParseMode

import env
import config
from functions import locale

bot = Client(config.BOT_GC_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN)


def scan_prepare():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(scan_for_gc_update())
    loop.close()


async def scan_for_gc_update():
    while True:
        logging.info('GC Alerter: Syncing game build IDs with GC...')
        try:
            with open(config.GC_PREV_CACHE_FILE_PATH, encoding='utf-8') as f:
                prev_cache = json.load(f)
            with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
                cache = json.load(f)

            if prev_cache.get('sdk_build_id') != cache['sdk_build_id']:
                prev_cache['sdk_build_id'] = cache['sdk_build_id']
                await send_alert('sdk_build_id', cache['sdk_build_id'])

            if prev_cache.get('ds_build_id') != cache['ds_build_id']:
                prev_cache['ds_build_id'] = cache['ds_build_id']
                await send_alert('ds_build_id', cache['ds_build_id'])

            if prev_cache.get('valve_ds_changenumber') != cache['valve_ds_changenumber']:
                prev_cache['valve_ds_changenumber'] = cache['valve_ds_changenumber']
                await send_alert('valve_ds_changenumber', cache['valve_ds_changenumber'])

            if prev_cache.get('cs2_app_changenumber') != cache['cs2_app_changenumber']:
                prev_cache['cs2_app_changenumber'] = cache['cs2_app_changenumber']
                await send_alert('cs2_app_changenumber', cache['cs2_app_changenumber'])

            if prev_cache.get('cs2_server_changenumber') != cache['cs2_server_changenumber']:
                prev_cache['cs2_server_changenumber'] = cache['cs2_server_changenumber']
                await send_alert('cs2_server_changenumber', cache['cs2_server_changenumber'])

            if prev_cache.get('dprp_build_id') != cache['dprp_build_id']:
                prev_cache['dprp_build_id'] = cache['dprp_build_id']
                await send_alert('dprp_build_id', cache['dprp_build_id'])

            if prev_cache.get('dpr_build_id') != cache['dpr_build_id']:
                prev_cache['dpr_build_id'] = cache['dpr_build_id']
                if cache['dpr_build_id'] == cache['public_build_id']:
                    await send_alert('dpr_build_sync_id', cache['dpr_build_id'])
                else:
                    await send_alert('dpr_build_id', cache['dpr_build_id'])

            if prev_cache.get('public_build_id') != cache['public_build_id']:
                prev_cache['public_build_id'] = cache['public_build_id']
                await send_alert('public_build_id', cache['public_build_id'])

            with open(config.GC_PREV_CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(prev_cache, f, indent=4)

        except Exception:
            logging.exception(f"Caught an exception while scanning GC info!")
            time.sleep(45)
            continue

        logging.info('GC Alerter: Successfully synced game build IDs.')

        time.sleep(45)


async def send(chat_list, text):
    if not bot.is_connected:
        await asyncio.sleep(4)

    for chat_id in chat_list:
        msg = await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        if chat_id == config.INCS2CHAT:
            await msg.pin(disable_notification=True)


async def send_alert(key: str, new_value: int):
    logging.info(f'GC Alerter: Found new change: {key}, sending alert...')
    loc = locale('ru')

    if key == "public_build_id":
        text = loc.notifs_build_public.format(new_value)
    elif key == "dpr_build_id":
        text = loc.notifs_build_dpr.format(new_value)
    elif key == "dprp_build_id":
        text = loc.notifs_build_dprp.format(new_value)
    elif key == "dpr_build_sync_id":
        text = f"{loc.notifs_build_dpr.format(new_value)} 🔃"
    elif key == "sdk_build_id":
        text = loc.notifs_build_sdk.format(new_value)
    elif key == "ds_build_id":
        text = loc.notifs_build_ds.format(new_value)
    elif key == "valve_ds_changenumber":
        text = loc.notifs_build_valve_ds.format(new_value)
    elif key == "cs2_app_changenumber":
        text = loc.notifs_build_cs2_client.format(new_value)
    elif key == "cs2_server_changenumber":
        text = loc.notifs_build_cs2_server.format(new_value)
    else:
        logging.warning(f"GC Alerter: Got wrong key to send alert: {key}")
        return

    if not config.TEST_MODE:
        chat_list = [config.INCS2CHAT, config.CSTRACKER]
    else:
        chat_list = [config.AQ]

    await send(chat_list, text)


def main():
    t1 = Thread(target=scan_prepare)

    t1.start()

    bot.run()


if __name__ == '__main__':
    main()
