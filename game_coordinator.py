import asyncio
import datetime as dt
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
from functions.ulogging import get_logger
from utypes import GameVersion, States, GameVersionData

VALVE_TIMEZONE = ZoneInfo('America/Los_Angeles')
loc = locale('ru')

AVAILABLE_ALERTS = {'public_branch_updated': loc.notifs_build_public,
                    'cs2_app_changenumber': loc.notifs_build_cs2_client,
                    'cs2_server_changenumber': loc.notifs_build_cs2_server,
                    'backup_branch_created': loc.notifs_backup_branch_created,
                    'backup_branch_created_sync': f'{loc.notifs_backup_branch_created} 🔃',
                    'backup_branch_updated': loc.notifs_backup_branch_updated,
                    'backup_branch_updated_sync': f'{loc.notifs_backup_branch_created} 🔃',
                    'backup_branch_deleted': loc.notifs_backup_branch_deleted,
                    # 'private_branch_created': loc.notifs_private_branch_created,
                    # 'private_branch_updated': loc.notifs_private_branch_updated,
                    'misc_branch_created': loc.notifs_misc_branch_created,
                    'misc_branch_updated': loc.notifs_misc_branch_updated,
                    'branch_deleted': loc.notifs_branch_deleted}
MAIN_BRANCHES = {'public', '<null>'}  # <null> is for other important things

logger = get_logger('game_coordinator', config.LOGS_FOLDER, config.LOGS_CONFIG_FILE_PATH)


class PatchedSteamClient(SteamClient):
    """*Probably* fixes an infinite program blocking when unable to connect to CM."""

    def _pre_login(self):
        if self.logged_on:
            raise RuntimeError("Already logged on")

        if not self.connected and not self._connecting:
            if not self.connect(retry=10):
                return EResult.Fail

        if not self.channel_secured:
            resp = self.wait_event(self.EVENT_CHANNEL_SECURED, timeout=10)

            # some CMs will not send hello
            if resp is None:
                if self.connected:
                    self.wait_event(self.EVENT_DISCONNECTED)
                return EResult.TryAnotherCM

        return EResult.OK


bot = Client(config.BOT_GC_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN,
             test_mode=config.TEST_MODE,
             no_updates=True,
             workdir=config.SESS_FOLDER)
client = PatchedSteamClient()
client.set_credential_location(config.STEAM_CREDS_PATH)
cs = CSGOClient(client)
gevent_scheduler = GeventScheduler()
async_scheduler = AsyncIOScheduler()

going_to_shutdown = False  # can be used in jobs to safely call sys.exit() afterwards


def is_backup_branch(name: str) -> bool:
    return name.startswith('1.4') or name.startswith('1.3')


@client.on('error')
def handle_error(result):
    logger.error(f'Logon result: {result!r}')


@client.on('channel_secured')
def send_relogin():
    if client.relogin_available:
        client.relogin()


@client.on('connected')
def log_connect():
    logger.info(f'Connected to {client.current_server_addr}')


@client.on('reconnect')
def handle_reconnect(delay):
    logger.info(f'Reconnect in {delay}s...')


@client.on('disconnected')
def handle_disconnect():
    logger.warning('Disconnected.')

    # if client.relogin_available:
    #     logger.info('Reconnecting...')
    #     client.reconnect(maxdelay=30)    # todo: could be broken - needs to be tested somehow

    sys.exit()


@client.on('logged_on')
def handle_after_logon():
    cs.launch()
    async_scheduler.start()
    gevent_scheduler.start()


@cs.on('ready')
def cs_launched():
    logger.info('CS launched.')


@cs.on('connection_status')
def update_gc_status(status):
    statuses = {0: States.NORMAL, 1: States.INTERNAL_SERVER_ERROR, 2: States.OFFLINE,
                3: States.RELOADING, 4: States.INTERNAL_STEAM_ERROR}
    game_coordinator_state = statuses.get(status, States.UNKNOWN).literal

    caching.dump_cache_changes(config.GC_CACHE_FILE_PATH, {'game_coordinator_state': game_coordinator_state})

    logger.info(f'Successfully dumped game coordinator status: {game_coordinator_state}')


@async_scheduler.scheduled_job('interval', seconds=45)
async def update_depots():
    global going_to_shutdown

    # noinspection PyBroadException
    try:
        data = client.get_product_info(apps=[730, 2275500, 2275530], timeout=15)['apps']

        current_branches = data[730]['depots']['branches']
        cs2_app_change_number = data[2275500]['_change_number']
        cs2_server_change_number = data[2275530]['_change_number']
    except Exception:
        logger.exception('Caught an exception while trying to fetch depots!')
        return
    except gevent.Timeout:  # still no idea how to solve it so just crash and restart the entire thing
        going_to_shutdown = True
        logger.exception('Caught gevent.Timeout, we\'re going to shutdown...')
        return

    cache = caching.load_cache(config.GC_CACHE_FILE_PATH)

    new_data = {
        'cs2_app_changenumber': cs2_app_change_number,
        'cs2_server_changenumber': cs2_server_change_number,
        'branches': current_branches
    }

    for key, new_value in new_data.items():
        old_value = cache.get(key)
        if old_value is None or old_value == new_value:
            continue

        if key == 'branches':
            await check_for_new_branches(cache, old_value, new_value)
            await check_for_removed_branches(old_value, new_value)
            # mutates `cache` var in case of "public" branch update
            await check_for_branches_updates(cache, old_value, new_value)
        else:
            # I am an idiot but oh well
            await send_branch_alert('<null>', key, new_value)

    cache.update(new_data)

    caching.dump_cache(config.GC_CACHE_FILE_PATH, cache)

    logger.info('Successfully dumped game version data.')


async def check_for_new_branches(cache: dict, cached_branches: dict, current_branches: dict):
    cs2_patch_version = cache.get('cs2_patch_version')

    new_branches = current_branches.keys() - cached_branches.keys()
    if not new_branches:
        return

    for branch_name in new_branches:
        branch_data = current_branches[branch_name]

        if is_backup_branch(branch_name):
            event = 'backup_branch_created_sync' if branch_name == cs2_patch_version else 'backup_branch_created'
        else:
            event = 'misc_branch_created'
        await send_branch_alert(branch_name, event, branch_data['buildid'])


async def check_for_removed_branches(cached_branches: dict, current_branches: dict):
    removed_branches = cached_branches.keys() - current_branches.keys()
    if not removed_branches:
        return

    for branch_name in removed_branches:
        if is_backup_branch(branch_name):
            event = 'backup_branch_deleted'
        else:
            event = 'branch_deleted'
        await send_branch_alert(branch_name, event)


async def check_for_branches_updates(cache: dict, cached_branches: dict, current_branches: dict):
    cs2_patch_version = cache.get('cs2_patch_version')

    for branch_name, branch_data in current_branches.items():
        cached_branch_data = cached_branches.get(branch_name)

        if cached_branch_data is None:  # newly created, ignore
            continue
        old_buildid = cached_branch_data['buildid']
        new_buildid = branch_data['buildid']
        if old_buildid == new_buildid:
            continue

        if branch_name == 'public':
            game_version_data = await get_game_version_loop(cache.get('cs2_client_version'))
            cache.update(game_version_data.asdict())
            event = 'public_branch_updated'
        elif is_backup_branch(branch_name):
            event = 'backup_branch_updated_sync' if branch_name == cs2_patch_version else 'backup_branch_updated'
        else:
            event = 'misc_branch_updated'
        await send_branch_alert(branch_name, event, new_buildid)


async def get_game_version_loop(cs2_client_version: int | None) -> GameVersionData:
    timeout = 30 * 60
    timeout_start = time.time()
    with requests.Session() as session:
        while time.time() < timeout_start + timeout:
            data = await get_game_version(session, cs2_client_version)
            if data:
                return data
            logger.warning('Failed to pull the game version data, retry in 45 seconds...')
            await asyncio.sleep(45)
    # xPaw: Zzz...
    # because of this, we retry in an hour
    logger.warning('Reached a timeout while trying to pull the game version data, retry in an hour...')
    await asyncio.sleep(60 * 60)
    await get_game_version_loop(cs2_client_version)


async def get_game_version(session: requests.Session, cs2_client_version: int | None) -> GameVersionData | None:
    # noinspection PyBroadException
    try:
        data = GameVersion.request(session)

        if cs2_client_version is None:  # *somehow* don't have anything cached
            logger.info('Successfully pulled the game version data.')
            return data

        # Ensure that the data is up-to-date, so we check datetime
        new_data_datetime = (dt.datetime.fromtimestamp(data.cs2_version_timestamp)
                             .replace(tzinfo=VALVE_TIMEZONE).astimezone(dt.UTC))
        is_up_to_date = (utime.utcnow() - new_data_datetime < dt.timedelta(hours=12))

        if is_up_to_date and data.cs2_client_version != cs2_client_version:
            logger.info('Successfully pulled the game version data.')
            return data
    except Exception:
        logger.exception('Caught an exception while trying to get new version!')


@gevent_scheduler.scheduled_job('interval', seconds=45)
def online_players():
    player_count = client.get_player_count(730)

    caching.dump_cache_changes(config.GC_CACHE_FILE_PATH, {'online_players': player_count})

    logger.info(f'Successfully dumped player count: {player_count}')


async def send_branch_alert(branch: str, event: str, new_buildid: str = None):
    logger.info(f'Detected {branch} branch "{event}" event, sending alert...')

    alert_sample = AVAILABLE_ALERTS.get(event)

    if alert_sample is None:
        logger.warning(f'Got wrong event name to send alert: {event}')
        return

    if branch in MAIN_BRANCHES:
        text = alert_sample.format(new_buildid)
    else:
        text = alert_sample.format(branch, new_buildid)

    await send_text_alert(text)


async def send_text_alert(text: str):
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
        logger.info(f'Stop signal received ({signals[signum]}). Exiting...')
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
    logger.info('Started.')
    try:
        logger.info('Logging in...')
        result = client.login(username=config.STEAM_USERNAME, password=config.STEAM_PASS)

        if result != EResult.OK:
            logger.error(f"Failed to login: {result!r}")
            sys.exit(1)

        logger.info('Logged in successfully.')
        await bot.start()
        await mainloop()
    except KeyboardInterrupt:
        if client.connected:
            logger.info('Logout...')
            client.logout()
        logger.info('Terminated.')
        raise


if __name__ == '__main__':
    asyncio.run(main())
