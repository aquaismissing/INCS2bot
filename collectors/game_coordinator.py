import gevent.monkey

gevent.monkey.patch_all()

import datetime as dt
import json
import logging
import platform
import sys
from threading import Thread
import time

from apscheduler.schedulers.gevent import GeventScheduler
from csgo.client import CSGOClient
from steam.client import SteamClient
from steam.enums import EResult
if platform.system() == 'Linux':
    # noinspection PyPackageRequirements
    import uvloop

    uvloop.install()

# noinspection PyUnresolvedReferences
import env
import config
from utypes import GameVersionData, States

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | GC: %(message)s',
                    datefmt='%H:%M:%S — %d/%m/%Y')

client = SteamClient()
client.set_credential_location(config.STEAM_CREDS_PATH)
cs = CSGOClient(client)
scheduler = GeventScheduler()


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

    # if client.relogin_available:          # currently broken in steam 1.4.4
    #     logging.info('Reconnecting...')   # https://github.com/ValvePython/steam/issues/439
    #     client.reconnect(maxdelay=30)

    sys.exit()  # a temporary solution - just stop the script and reboot it from another script


@cs.on('connection_status')
def gc_status_change(status):
    statuses = {0: States.NORMAL, 1: States.INTERNAL_SERVER_ERROR, 2: States.OFFLINE,
                3: States.RELOADING, 4: States.INTERNAL_STEAM_ERROR}
    game_coordinator = statuses.get(status, States.UNKNOWN)
    
    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache = json.load(f)

    if game_coordinator != cache.get('game_coordinator'):
        cache['game_coordinator'] = game_coordinator.literal

    with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4)

    logging.info(f'Successfully dumped game coordinator status: {game_coordinator.literal}')


@client.on('logged_on')
def handle_after_logon():
    cs.launch()
    scheduler.start()


@scheduler.scheduled_job('interval', seconds=45)
def depots():
    # noinspection PyBroadException
    try:
        data = client.get_product_info(apps=[730, 740, 741, 745, 2275500, 2275530],
                                       timeout=15)['apps']
        main_data = data[730]

        public_build_id = int(main_data['depots']['branches']['public']['buildid'])
        dpr_build_id = int(main_data['depots']['branches']['dpr']['buildid'])
        dprp_build_id = int(main_data['depots']['branches']['dprp']['buildid'])

        ds_build_id = int(data[740]['depots']['branches']['public']['buildid'])
        valve_ds_change_number = data[741]['_change_number']
        sdk_build_id = int(data[745]['depots']['branches']['public']['buildid'])

        cs2_app_change_number = data[2275500]['_change_number']
        cs2_server_change_number = data[2275530]['_change_number']
    except Exception:
        logging.exception('Caught an exception while trying to fetch depots!')
        return

    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache = json.load(f)

    cache['sdk_build_id'] = sdk_build_id
    cache['ds_build_id'] = ds_build_id
    cache['valve_ds_changenumber'] = valve_ds_change_number
    cache['cs2_app_changenumber'] = cs2_app_change_number
    cache['cs2_server_changenumber'] = cs2_server_change_number
    cache['dprp_build_id'] = dprp_build_id
    cache['dpr_build_id'] = dpr_build_id

    if public_build_id != cache.get('public_build_id'):
        cache['public_build_id'] = public_build_id
        Thread(target=gv_updater).start()

    with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4)

    logging.info('Successfully dumped game build IDs.')


def gv_updater():
    timeout = 30 * 60
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        # noinspection PyBroadException
        try:
            data = GameVersionData.request()

            with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
                cache = json.load(f)

            # We want to ensure that the data is up to date so we check datetime
            new_data_datetime = dt.datetime.fromisoformat(data.cs2_version_timestamp)  # no need to convert timezones
            cached_data_datetime = dt.datetime.fromisoformat(cache.get('cs2_client_version'))  # since they are the same
            is_up_to_date = new_data_datetime > cached_data_datetime

            if is_up_to_date and data.cs2_client_version != cache.get('cs2_client_version'):
                for key, value in data.asdict().items():
                    cache[key] = value

                with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=4)
                sys.exit()
        except Exception:
            logging.exception('Caught an exception while trying to get new version!')
            time.sleep(45)
            continue
        time.sleep(45)
    # xPaw: Zzz...
    # because of this, we retry in an hour
    time.sleep(60 * 60)
    gv_updater()


@scheduler.scheduled_job('interval', seconds=45)
def online_players():
    value = client.get_player_count(730)

    with open(config.CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    if value != cache.get('online_players'):
        cache['online_players'] = value

    with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4)

    logging.info(f'Successfully dumped player count: {value}')


def main():
    try:
        logging.info('Logging in...')
        result = client.login(username=config.STEAM_USERNAME, password=config.STEAM_PASS)

        if result != EResult.OK:
            logging.error(f"Failed to login: {result!r}")
            sys.exit(1)

        logging.info('Logged in successfully.')
        client.run_forever()
    except KeyboardInterrupt:
        if client.connected:
            logging.info('Logout...')
            client.logout()


if __name__ == '__main__':
    main()
