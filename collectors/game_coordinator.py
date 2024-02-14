import asyncio
import json
import logging
import platform
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from steam import App
from steam.ext.csgo import Client
from steam.ext.csgo.protobufs.sdk import GcConnectionStatus


if platform.system() == 'Linux':
    # noinspection PyPackageRequirements
    import uvloop

    uvloop.install()

# noinspection PyUnresolvedReferences
import env
import config
from utypes import GameVersionData, States

logging.basicConfig(format='%(asctime)s | %(name)s: %(message)s',
                    datefmt='%H:%M:%S — %d/%m/%Y',
                    force=True)

logger = logging.getLogger('root')  # f'{config.BOT_NAME}.GCCollector'
logging.getLogger('steam').setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)


class GCCollector(Client):
    APPS_TO_FETCH = App(id=730), App(id=2275500), App(id=2275530)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.update_depots, 'interval', seconds=45)
        # self.scheduler.add_job(self.update_players_count, 'interval', seconds=45)

    async def login(self, *args, **kwargs):
        logger.info('Logging in...')
        await super().login(*args, **kwargs)

    async def on_ready(self):
        logger.info('Logged in successfully.')

    async def on_disconnect(self):
        logger.info('Disconnected.')
        self.scheduler.pause()

        logger.info('Reconnecting...')
        await self.login(config.STEAM_USERNAME, config.STEAM_PASS)
        result = self.is_ready()

        logger.info('Reconnected successfully.' if result else 'Failed to reconnect.')
        if result:
            self.scheduler.resume()

    async def on_gc_ready(self):
        logger.info('CS launched.')
        self.scheduler.start()

    async def on_gc_status_change(self, status: GcConnectionStatus):
        logger.info(f'{status.name!r} (on_gc_status_change)')

        statuses = {0: States.NORMAL, 1: States.INTERNAL_SERVER_ERROR, 2: States.OFFLINE,
                    3: States.RELOADING, 4: States.INTERNAL_STEAM_ERROR}
        game_coordinator = statuses.get(status.value, States.UNKNOWN)
        #
        # with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        #     cache = json.load(f)
        #
        # if game_coordinator != cache.get('game_coordinator'):
        #     cache['game_coordinator'] = game_coordinator.literal
        #
        # with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        #     json.dump(cache, f, indent=4)
        #
        logger.info(f'Successfully dumped game coordinator status: {game_coordinator.literal}')

    async def update_depots(self):
        try:
            data = await self.fetch_product_info(apps=self.APPS_TO_FETCH)
            logging.info(await self.fetch_product_info(apps=[App(id=2275500)]))

            data = {int(app.id): app for app in data}
            logging.info(data)
            main_data = data[730]

            public_build_id = main_data.public_branch.build_id
            dpr_build_id = main_data.get_branch('dpr').build_id
            dprp_build_id = main_data.get_branch('dprp').build_id

            # currently can't track
            # cs2_app_change_number = data[2275500].change_number
            # cs2_server_change_number = data[2275530].change_number
        except Exception:
            logger.exception('Caught an exception while trying to fetch depots!')
            return

        # with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        #     cache = json.load(f)
        #
        # cache['cs2_app_changenumber'] = cs2_app_change_number
        # cache['cs2_server_changenumber'] = cs2_server_change_number
        # cache['dprp_build_id'] = dprp_build_id
        # cache['dpr_build_id'] = dpr_build_id
        #
        # if public_build_id != cache.get('public_build_id'):
        #     cache['public_build_id'] = public_build_id
        #     task = asyncio.create_task(some_coro(param=i))
        #
        # with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
        #     json.dump(cache, f, indent=4)

        logger.info('Successfully dumped game build IDs.')

    async def update_game_version(self):
        timeout = 30 * 60
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
                    return
            except Exception:
                logging.exception('Caught an exception while trying to get new version!')
            await asyncio.sleep(45)

        # sometimes steamdb updates the info much later (xPaw: Zzz...)
        # because of this, we retry in an hour
        await asyncio.sleep(60 * 60)
        await self.update_game_version()

    async def update_players_count(self):
        value = await self.get_app(730).player_count()  # freezes function entirely

        with open(config.CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        cache['online_players'] = value

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)

        logger.info(f'Successfully dumped player count: {value}')


# @client.on("error")
# def handle_error(result):
#     logging.info(f'Logon result: {result!r}')

# @client.on('channel_secured')
# def send_login():
#     if client.relogin_available:
#         client.relogin()

# @client.on('connected')
# def handle_connected():
#     logging.info(f'Connected to {client.current_server_addr}')

# @client.on('reconnect')
# def handle_reconnect(delay):
#     logging.info(f'Reconnect in {delay}s...')

# @client.on('disconnected')
# def handle_disconnect():
#     cs.exit()
#     logging.info('Disconnected.')
#
#     logging.info('Reconnecting...')
#     result = client.reconnect(maxdelay=30, retry=3)
#
#     logging.info('Reconnected successfully.' if result else 'Failed to reconnect.')
#     if result:
#         logging.info(f'{client.logged_on=}')
#         cs.emit('reload')

# @cs.on('connection_status')
# def gc_ready(status):
#     statuses = {0: States.NORMAL, 1: States.INTERNAL_SERVER_ERROR, 2: States.OFFLINE,
#                 3: States.RELOADING, 4: States.INTERNAL_STEAM_ERROR}
#     game_coordinator = statuses.get(status, States.UNKNOWN)
#
#     with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
#         cache = json.load(f)
#
#     if game_coordinator != cache.get('game_coordinator'):
#         cache['game_coordinator'] = game_coordinator.literal
#
#     with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
#         json.dump(cache, f, indent=4)
#
#     logging.info(f'Successfully dumped game coordinator status: {game_coordinator.literal}')

# @cs.on('reload')
# def cs_exit():
#     logging.info(f'Reloading CS...')
#     cs.launch()

# @client.on('logged_on')
# def handle_after_logon():
#     cs.launch()
#     Thread(target=depots_prepare).start()
#     Thread(target=online_players).start()

# def depots_prepare():
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#
#     loop.run_until_complete(depots())
#     loop.close()

# @client.on('new_login_key')
# def lol():
#     logging.info(f'{client.login_key=}')


def main():
    collector = GCCollector()
    collector.run(refresh_token=config.STEAM_REFRESH_TOKEN, debug=True)


if __name__ == '__main__':
    main()
