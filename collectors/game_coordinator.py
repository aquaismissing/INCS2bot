import gevent.monkey

gevent.monkey.patch_all()

import asyncio
import json
import logging
import platform
import sys
from threading import Thread
import time

from csgo.client import CSGOClient
from steam.client import SteamClient
from steam.enums import EResult

from steam.ext.csgo import Client

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


class GCCollector(Client):
    async def on_connect(self):
        logging.info('Connected to Steam.')

    async def on_gc_connect(self):
        logging.info('CS launched.')

    async def on_gc_ready(self, status):
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


# client = SteamClient()
# client.set_credential_location(str(config.STEAM_CREDS_PATH))
# cs = CSGOClient(client)


# @client.on("error")
# def handle_error(result):
#     logging.info(f'Logon result: {result!r}')


# @client.on('channel_secured')
# def send_login():
#     if client.relogin_available:
#         client.relogin()


@client.on('connected')
def handle_connected():
    logging.info(f'Connected to {client.current_server_addr}')


@client.on('reconnect')
def handle_reconnect(delay):
    logging.info(f'Reconnect in {delay}s...')


@client.on('disconnected')
def handle_disconnect():
    cs.exit()
    logging.info('Disconnected.')

    logging.info('Reconnecting...')
    result = client.reconnect(maxdelay=30, retry=3)

    logging.info('Reconnected successfully.' if result else 'Failed to reconnect.')
    if result:
        logging.info(f'{client.logged_on=}')
        cs.emit('reload')


@cs.on('connection_status')
def gc_ready(status):
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


@cs.on('ready')
def cs_launched():
    logging.info(f'CS launched.')


@cs.on('reload')
def cs_exit():
    logging.info(f'Reloading CS...')
    cs.launch()


@client.on('logged_on')
def handle_after_logon():
    cs.launch()
    Thread(target=depots_prepare).start()
    Thread(target=online_players).start()


def depots_prepare():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(depots())
    loop.close()


async def depots():
    while True:
        try:
            data = client.get_product_info(apps=[740, 741, 2275500, 2275530, 745, 730],
                                           timeout=15)['apps']
            main_data = data[730]

            ds_build_id = int(data[740]['depots']['branches']['public']['buildid'])
            valve_ds_change_number = data[741]['_change_number']
            cs2_app_change_number = data[2275500]['_change_number']
            cs2_server_change_number = data[2275530]['_change_number']
            sdk_build_id = int(data[745]['depots']['branches']['public']['buildid'])
            dpr_build_id = int(main_data['depots']['branches']['dpr']['buildid'])
            dprp_build_id = int(main_data['depots']['branches']['dprp']['buildid'])
            public_build_id = int(main_data['depots']['branches']['public']['buildid'])
        except Exception:
            logging.exception('Caught an exception while trying to fetch depots!')
            time.sleep(45)
            continue

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
        time.sleep(45)


def gv_updater():
    timeout = 1800
    timeout_start = time.time()
    while time.time() < timeout_start + timeout:
        try:
            data = GameVersionData.request()

            with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
                cache = json.load(f)

            if data.csgo_client_version != cache.get('csgo_client_version') \
                    or data.cs2_client_version != cache.get('cs2_client_version'):
                for key, value in data.asdict().items():
                    cache[key] = value

            with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=4)
        except Exception:
            logging.exception('Caught an exception while trying to get new version!')
            time.sleep(45)
            continue
        time.sleep(45)
    sys.exit()


def online_players():
    while True:
        value = client.get_player_count(730)

        with open(config.CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        if value != cache.get('online_players'):
            cache['online_players'] = value

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)

        logging.info(f'Successfully dumped player count: {value}')
        time.sleep(45)


@client.on('new_login_key')
def lol():
    logging.info(f'{client.login_key=}')


def main():
    try:
        logging.info('Logging in...')
        result = client.login(username=config.STEAM_USERNAME, password=config.STEAM_PASS)
        logging.info(f'{client.login_key=}')

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
