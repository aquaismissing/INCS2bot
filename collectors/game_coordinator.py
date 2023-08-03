import gevent.monkey

gevent.monkey.patch_all()

import asyncio
import json
import logging
import sys
from threading import Thread
import time

from csgo.client import CSGOClient
from steam.client import SteamClient
from steam.enums import EResult

# noinspection PyUnresolvedReferences
import env
import config
from utypes import GameVersionData, States

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(threadName)s | %(name)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

client = SteamClient()
client.set_credential_location(config.STEAM_CREDS_PATH)
cs = CSGOClient(client)


@client.on("error")
def handle_error(result):
    logging.info(f"GC: Logon result: {result!r}")


@client.on("channel_secured")
def send_login():
    if client.relogin_available:
        client.relogin()


@client.on("connected")
def handle_connected():
    logging.info(f"GC: Connected to {client.current_server_addr}")


@client.on("reconnect")
def handle_reconnect(delay):
    logging.info(f"GC: Reconnect in {delay} s...")


@client.on("disconnected")
def handle_disconnect():
    logging.info("GC: Disconnected.")

    if client.relogin_available:
        logging.info("GC: Reconnecting...")
        client.reconnect(maxdelay=30)


@cs.on("connection_status")
def gc_ready(status):
    statuses = {0: States.NORMAL, 1: States.INTERNAL_SERVER_ERROR, 2: States.OFFLINE,
                3: States.RELOADING, 4: States.INTERNAL_STEAM_ERROR}
    game_coordinator = statuses.get(status, States.UNKNOWN)
    
    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache = json.load(f)

    if game_coordinator != cache.get("game_coordinator"):
        cache['game_coordinator'] = game_coordinator.literal

    with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4)

    logging.info(f'GC: Successfully dumped game coordinator status: {game_coordinator.literal}')


@client.on("logged_on")
def handle_after_logon():
    Thread(target=depots_prepare).start()
    Thread(target=gc).start()
    Thread(target=online_players).start()


def depots_prepare():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(depots())
    loop.close()


async def depots():
    while True:
        try:
            for values in client.get_product_info(apps=[740], timeout=15).values():
                for v in values.values():
                    ds_build_id = int(v["depots"]["branches"]["public"]["buildid"])

            for values in client.get_product_info(apps=[741], timeout=15).values():
                for v in values.values():
                    valve_ds_change_number = v["_change_number"]

            for values in client.get_product_info(apps=[2275500], timeout=15).values():
                for v in values.values():
                    cs2_app_change_number = v["_change_number"]

            for values in client.get_product_info(apps=[2275530], timeout=15).values():
                for v in values.values():
                    cs2_server_change_number = v["_change_number"]

            for values in client.get_product_info(apps=[745], timeout=15).values():
                for v in values.values():
                    sdk_build_id = int(v["depots"]["branches"]["public"]["buildid"])

            for values in client.get_product_info(apps=[730], timeout=15).values():
                for v in values.values():
                    dpr_build_id = int(v["depots"]["branches"]["dpr"]["buildid"])
                    dprp_build_id = int(v["depots"]["branches"]["dprp"]["buildid"])
                    public_build_id = int(v["depots"]["branches"]["public"]["buildid"])

        except Exception:
            logging.exception(f"GC: Caught an exception while trying to fetch depots!")
            time.sleep(45)
            continue

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        if sdk_build_id != cache.get('sdk_build_id'):
            cache['sdk_build_id'] = sdk_build_id

        if ds_build_id != cache.get('ds_build_id'):
            cache['ds_build_id'] = ds_build_id

        if valve_ds_change_number != cache.get('valve_ds_changenumber'):
            cache['valve_ds_changenumber'] = valve_ds_change_number

        if cs2_app_change_number != cache.get('cs2_app_changenumber'):
            cache['cs2_app_changenumber'] = cs2_app_change_number

        if cs2_server_change_number != cache.get('cs2_server_changenumber'):
            cache['cs2_server_changenumber'] = cs2_server_change_number

        if dprp_build_id != cache.get('dprp_build_id'):
            cache['dprp_build_id'] = dprp_build_id

        if dpr_build_id != cache.get('dpr_build_id'):
            cache['dpr_build_id'] = dpr_build_id

        if public_build_id != cache.get('public_build_id'):
            cache['public_build_id'] = public_build_id
            Thread(target=gv_updater).start()

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)

        logging.info('GC: Successfully dumped game build IDs.')

        time.sleep(45)


def gc():
    cs.launch()


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
            logging.exception("GC: Caught an exception while trying to get new version!")
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

        logging.info(f'GC: Successfully dumped player count: {value}')
        time.sleep(45)


def main():
    try:
        logging.error(f"GC: Logging in...")
        result = client.login(username=config.STEAM_USERNAME, password=config.STEAM_PASS)

        if result != EResult.OK:
            logging.error(f"GC: Failed to login: {result!r}")
            sys.exit(1)

        logging.error(f"GC: Logged in successfully.")
        client.run_forever()
    except KeyboardInterrupt:
        if client.connected:
            logging.info("GC: Logout...")
            client.logout()


if __name__ == '__main__':
    main()


