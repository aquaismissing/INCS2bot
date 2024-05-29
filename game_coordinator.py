import asyncio
import datetime as dt
import json
import logging
import platform
import sys
import time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.gevent import GeventScheduler
from csgo.client import CSGOClient
from pyrogram import Client, idle
import requests
from steam.client import SteamClient
from steam.enums import EResult

if platform.system() == 'Linux':
    # noinspection PyPackageRequirements
    import uvloop

    uvloop.install()

import config
from functions import locale, utime
from utypes import GameVersion, States

VALVE_TIMEZONE = ZoneInfo('America/Los_Angeles')
loc = locale('ru')

available_alerts = {'public_build_id': loc.notifs_build_public,
                    'dpr_build_id': loc.notifs_build_dpr,
                    'dprp_build_id': loc.notifs_build_dprp,
                    'dpr_build_sync_id': f'{loc.notifs_build_dpr} 🔃',
                    'dprp_build_sync_id': f'{loc.notifs_build_dprp} 🔃',
                    'cs2_app_changenumber': loc.notifs_build_cs2_client,
                    'cs2_server_changenumber': loc.notifs_build_cs2_server}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | GC: %(message)s',
                    datefmt='%H:%M:%S — %d/%m/%Y')

bot = Client(config.BOT_GC_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN,
             no_updates=True,
             workdir=config.SESS_FOLDER)
client = SteamClient()
client.set_credential_location(config.STEAM_CREDS_PATH)
cs = CSGOClient(client)
gevent_scheduler = GeventScheduler()
async_scheduler = AsyncIOScheduler()


@client.on('error')
def handle_error(result):
    logging.info(f'Logon result: {result!r}')


@client.on('channel_secured')
def send_relogin():
    if client.relogin_available:
        client.relogin()


@client.on('connected')
def log_connect():
    logging.info(f'Connected to {client.current_server_addr}')


@client.on('reconnect')
def handle_reconnect(delay):
    logging.info(f'Reconnect in {delay}s...')


@client.on('disconnected')
def handle_disconnect():
    logging.info('Disconnected.')

    # if client.relogin_available:
    #     logging.info('Reconnecting...')
    #     client.reconnect(maxdelay=30)    # todo: could be broken - needs to be tested somehow

    sys.exit()


@client.on('logged_on')
def handle_after_logon():
    cs.launch()
    async_scheduler.start()
    gevent_scheduler.start()


@cs.on('ready')
def cs_launched():
    logging.info('CS launched.')


@cs.on('connection_status')
def update_gc_status(status):
    statuses = {0: States.NORMAL, 1: States.INTERNAL_SERVER_ERROR, 2: States.OFFLINE,
                3: States.RELOADING, 4: States.INTERNAL_STEAM_ERROR}
    game_coordinator = statuses.get(status, States.UNKNOWN)

    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache = json.load(f)

    if game_coordinator != cache.get('game_coordinator_state'):
        cache['game_coordinator_state'] = game_coordinator.literal

    with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

    logging.info(f'Successfully dumped game coordinator status: {game_coordinator.literal}')


@async_scheduler.scheduled_job('interval', seconds=45)
async def update_depots():
    # noinspection PyBroadException
    try:
        data = client.get_product_info(apps=[730, 2275500, 2275530], timeout=15)['apps']
        main_data = data[730]

        public_build_id = int(main_data['depots']['branches']['public']['buildid'])
        dpr_build_id = int(main_data['depots']['branches']['dpr']['buildid'])
        dprp_build_id = int(main_data['depots']['branches']['dprp']['buildid'])

        cs2_app_change_number = data[2275500]['_change_number']
        cs2_server_change_number = data[2275530]['_change_number']
    except Exception:
        logging.exception('Caught an exception while trying to fetch depots!')
        return

    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache = json.load(f)

    new_data = {'cs2_app_changenumber': cs2_app_change_number,
                'cs2_server_changenumber': cs2_server_change_number,
                'dprp_build_id': dprp_build_id,
                'dpr_build_id': dpr_build_id,
                'public_build_id': public_build_id}

    for _id, new_value in new_data.items():
        if cache.get(_id) != new_value:
            cache[_id] = new_value
            if _id == 'dpr_build_id' and new_value == cache['public_build_id']:
                await send_alert('dpr_build_sync_id', new_value)
                continue
            if _id == 'dprp_build_id' and new_value == cache['public_build_id']:
                await send_alert('dprp_build_sync_id', new_value)
                continue
            if _id == 'public_build_id':
                _ = asyncio.create_task(update_game_version())
            await send_alert(_id, new_value)

    with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

    logging.info('Successfully dumped game build IDs.')


async def update_game_version():
    timeout = 30 * 60
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        # noinspection PyBroadException
        try:
            with requests.Session() as session:
                data = GameVersion.request(session)

            with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
                cache = json.load(f)

            # Made to ensure we will grab the latest public data if we *somehow* don't have anything cached
            no_cached_data = (cache.get('cs2_client_version') is None)

            # We also want to ensure that the data is up-to-date, so we check datetime
            new_data_datetime = (dt.datetime.fromtimestamp(data.cs2_version_timestamp)
                                 .replace(tzinfo=VALVE_TIMEZONE).astimezone(dt.UTC))
            is_up_to_date = utime.utcnow() - new_data_datetime < dt.timedelta(hours=12)

            if no_cached_data or (is_up_to_date and data.cs2_client_version != cache.get('cs2_client_version')):
                for key, value in data.asdict().items():
                    cache[key] = value

                with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=4, ensure_ascii=False)
                sys.exit()
        except Exception:
            logging.exception('Caught an exception while trying to get new version!')
            await asyncio.sleep(45)
            continue
        await asyncio.sleep(45)
    # xPaw: Zzz...
    # because of this, we retry in an hour
    await asyncio.sleep(60 * 60)
    await update_game_version()


@gevent_scheduler.scheduled_job('interval', seconds=45)
def online_players():
    value = client.get_player_count(730)

    with open(config.CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    if value != cache.get('online_players'):
        cache['online_players'] = value

    with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

    logging.info(f'Successfully dumped player count: {value}')


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


async def main():
    try:
        logging.info('Logging in...')
        result = client.login(username=config.STEAM_USERNAME, password=config.STEAM_PASS)

        if result != EResult.OK:
            logging.error(f"Failed to login: {result!r}")
            sys.exit(1)

        logging.info('Logged in successfully.')
        await bot.start()
        await idle()
    except KeyboardInterrupt:
        if client.connected:
            logging.info('Logout...')
            client.logout()


if __name__ == '__main__':
    asyncio.run(main())
