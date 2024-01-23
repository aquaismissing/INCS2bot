import json
import logging
import platform

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client
if platform.system() == 'Linux':
    # noinspection PyPackageRequirements
    import uvloop

    uvloop.install()

# noinspection PyUnresolvedReferences
import env
import config
from functions import locale

loc = locale('ru')

MONITORING_IDS = ('cs2_app_changenumber', 'cs2_server_changenumber',
                  'dprp_build_id', 'dpr_build_id', 'public_build_id')

available_alerts = {'public_build_id': loc.notifs_build_public,
                    'dpr_build_id': loc.notifs_build_dpr,
                    'dprp_build_id': loc.notifs_build_dprp,
                    'dpr_build_sync_id': f'{loc.notifs_build_dpr} 🔃',
                    'cs2_app_changenumber': loc.notifs_build_cs2_client,
                    'cs2_server_changenumber': loc.notifs_build_cs2_server}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

scheduler = AsyncIOScheduler()
bot = Client(config.BOT_GC_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN,
             no_updates=True,
             workdir=config.SESS_FOLDER)


@scheduler.scheduled_job('interval', seconds=45)
async def scan_for_gc_update():
    # noinspection PyBroadException
    try:
        with open(config.GC_PREV_CACHE_FILE_PATH, encoding='utf-8') as f:
            prev_cache = json.load(f)
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        for _id in MONITORING_IDS:
            if prev_cache.get(_id) != cache[_id]:
                prev_cache[_id] = cache[_id]
                if _id == 'dpr_build_id':
                    if cache['dpr_build_id'] == cache['public_build_id']:
                        await send_alert('dpr_build_sync_id', cache['dpr_build_id'])
                    else:
                        await send_alert('dpr_build_id', cache['dpr_build_id'])
                    continue

                await send_alert(_id, cache[_id])

        with open(config.GC_PREV_CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(prev_cache, f, indent=4)
    except Exception:
        logging.exception('Caught an exception while scanning GC info!')


async def send_alert(key: str, new_value: int):
    logging.info(f'Found new change: {key}, sending alert...')

    alert_sample = available_alerts.get(key)

    if alert_sample is None:
        logging.warning(f'Got wrong key to send alert: {key}')
        return

    text = alert_sample.format(new_value)

    if not config.TEST_MODE:
        chat_list = [config.INCS2CHAT, config.CSTRACKER]
    else:
        chat_list = [config.AQ]

    for chat_id in chat_list:
        msg = await bot.send_message(chat_id, text, disable_web_page_preview=True)
        if chat_id == config.INCS2CHAT:
            await msg.pin(disable_notification=True)


def main():
    try:
        scheduler.start()
        bot.run()
    except TypeError:  # catching TypeError because Pyrogram propogates it at stop for some reason
        logging.info('Shutting down the bot...')


if __name__ == '__main__':
    main()
