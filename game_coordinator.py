import asyncio
import datetime as dt
import logging
import platform
import sys
import time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.gevent import GeventScheduler
from csgo.client import CSGOClient
import gevent
from pyrogram import Client
import requests
from steam.client import SteamClient
from steam.enums import EResult

if platform.system() == 'Linux':
    # noinspection PyPackageRequirements
    import uvloop

    uvloop.install()

import config
from functions import caching, locale, utime
from utypes import GameVersion, States, GameVersionData

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
             test_mode=config.TEST_MODE,
             no_updates=True,
             workdir=config.SESS_FOLDER)
client = SteamClient()
client.set_credential_location(config.STEAM_CREDS_PATH)
cs = CSGOClient(client)
gevent_scheduler = GeventScheduler()
async_scheduler = AsyncIOScheduler()

going_to_shutdown = False  # can be used in jobs to safely call sys.exit() afterwards


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
    game_coordinator_state = statuses.get(status, States.UNKNOWN).literal

    caching.dump_cache_changes(config.GC_CACHE_FILE_PATH, {'game_coordinator_state': game_coordinator_state})

    logging.info(f'Successfully dumped game coordinator status: {game_coordinator_state}')


@async_scheduler.scheduled_job('interval', seconds=45)
async def update_depots():
    global going_to_shutdown

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
    except gevent.Timeout:  # just crash and restart the entire thing
        going_to_shutdown = True
        logging.exception('Caught gevent.Timeout, we\'re going to shutdown...')
        return

    cache = caching.load_cache(config.GC_CACHE_FILE_PATH)

    new_data = {'cs2_app_changenumber': cs2_app_change_number,
                'cs2_server_changenumber': cs2_server_change_number,
                'dprp_build_id': dprp_build_id,
                'dpr_build_id': dpr_build_id,
                'public_build_id': public_build_id}

    old_public_build_id = cache.get('public_build_id')

    for build_id, new_value in new_data.items():
        old_value = cache.get(build_id)
        if old_value is None or old_value == new_value:
            if build_id == 'public_build_id':
                game_version_data = await get_game_version_loop(cache.get('cs2_client_version'))
                cache.update(game_version_data.asdict())
            continue

        if build_id == 'dpr_build_id' and new_value == old_public_build_id:
            await send_alert('dpr_build_sync_id', new_value)
            continue
        if build_id == 'dprp_build_id' and new_value == old_public_build_id:
            await send_alert('dprp_build_sync_id', new_value)
            continue
        if build_id == 'public_build_id':
            game_version_data = await get_game_version_loop(cache.get('cs2_client_version'))
            cache.update(game_version_data.asdict())
        await send_alert(build_id, new_value)

    cache.update(new_data)

    caching.dump_cache(config.GC_CACHE_FILE_PATH, cache)

    logging.info('Successfully dumped game version data.')


async def get_game_version_loop(cs2_client_version: int) -> GameVersionData:
    timeout = 30 * 60
    timeout_start = time.time()
    with requests.Session() as session:
        while time.time() < timeout_start + timeout:
            data = await get_game_version(session, cs2_client_version)
            if data:
                return data

            await asyncio.sleep(45)
    # xPaw: Zzz...
    # because of this, we retry in an hour
    await asyncio.sleep(60 * 60)
    await get_game_version_loop(cs2_client_version)


async def get_game_version(session: requests.Session, cs2_client_version: int) -> GameVersionData | None:
    # noinspection PyBroadException
    try:
        data = GameVersion.request(session)

        if cs2_client_version is None:  # *somehow* don't have anything cached
            logging.info('Successfully pulled the game version data.')
            return data

        # Ensure that the data is up-to-date, so we check datetime
        new_data_datetime = (dt.datetime.fromtimestamp(data.cs2_version_timestamp)
                             .replace(tzinfo=VALVE_TIMEZONE).astimezone(dt.UTC))
        is_up_to_date = (utime.utcnow() - new_data_datetime < dt.timedelta(hours=12))

        if is_up_to_date and data.cs2_client_version != cs2_client_version:
            logging.info('Successfully pulled the game version data.')
            return data
    except Exception:
        logging.exception('Caught an exception while trying to get new version!')


@gevent_scheduler.scheduled_job('interval', seconds=45)
def online_players():
    player_count = client.get_player_count(730)

    caching.dump_cache_changes(config.GC_CACHE_FILE_PATH, {'online_players': player_count})

    logging.info(f'Successfully dumped player count: {player_count}')


async def send_alert(key: str, new_value: int):
    logging.info(f'Found new change: {key}, sending alert...')

    alert_sample = available_alerts.get(key)

    if alert_sample is None:
        logging.warning(f'Got wrong key to send alert: {key}')
        return

    text = alert_sample.format(new_value)

    if bot.test_mode:
        chat_list = [config.AQ]
    else:
        chat_list = [config.INCS2CHAT, config.CSTRACKER]

    for chat_id in chat_list:
        msg = await bot.send_message(chat_id, text, disable_web_page_preview=True)
        if chat_id == config.INCS2CHAT:
            await msg.pin(disable_notification=True)


async def mainloop():
    # ESSENTIALS FOR MAINLOOP
    import signal
    from signal import signal as signal_fn, SIGINT, SIGTERM, SIGABRT

    signals = {k: v for v, k in signal.__dict__.items()
               if v.startswith('SIG') and not v.startswith('SIG_')}
    task = None

    def signal_handler(signum, __):
        logging.info(f'Stop signal received ({signals[signum]}). Exiting...')
        task.cancel()

    for s in (SIGINT, SIGTERM, SIGABRT):
        signal_fn(s, signal_handler)
    # ESSENTIALS FOR MAINLOOP END

    while True:
        task = asyncio.create_task(asyncio.sleep(10))
        try:
            await task
            if going_to_shutdown:
                sys.exit()
        except asyncio.CancelledError:
            break


async def main():
    try:
        logging.info('Logging in...')
        result = client.login(username=config.STEAM_USERNAME, password=config.STEAM_PASS)

        if result != EResult.OK:
            logging.error(f"Failed to login: {result!r}")
            sys.exit(1)

        logging.info('Logged in successfully.')
        await bot.start()
        await mainloop()
    except KeyboardInterrupt:
        if client.connected:
            logging.info('Logout...')
            client.logout()
        raise


if __name__ == '__main__':
    asyncio.run(main())
