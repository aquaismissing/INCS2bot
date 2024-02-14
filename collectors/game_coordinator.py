import asyncio
import datetime as dt
import json
import logging
from pathlib import Path
import platform
import time
from zoneinfo import ZoneInfo

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
from functions import utime
from utypes import GameVersion, States

VALVE_TIMEZONE = ZoneInfo('America/Los_Angeles')

logging.basicConfig(format='%(asctime)s | %(name)s: %(message)s',
                    datefmt='%H:%M:%S — %d/%m/%Y',
                    force=True)

logger = logging.getLogger(f'{config.BOT_NAME}.GCCollector')  # f'{config.BOT_NAME}.GCCollector'
logger.setLevel(logging.INFO)


class GCCollector(Client):
    APPS_TO_FETCH = App(id=730), App(id=2275500), App(id=2275530)  # the last two apps don't get fetched

    cache: dict[str, ...]

    def __init__(self, cache_file_path: Path, **kwargs):
        super().__init__(**kwargs)

        self.cache_file_path = cache_file_path
        self.load_cache()

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.update_depots, 'interval', seconds=45)
        # self.scheduler.add_job(self.update_players_count, 'interval', seconds=45) # currently doesn't work

    async def login(self, *args, **kwargs):
        logger.info('Logging in...')
        await super().login(*args, **kwargs)

    async def on_ready(self):
        logger.info('Logged in successfully.')

    async def on_disconnect(self):
        logger.info('Disconnected.')
        self.scheduler.pause()

        logger.info('Reconnecting...')
        await self.login(refresh_token=config.STEAM_REFRESH_TOKEN)
        result = self.is_ready()

        logger.info('Reconnected successfully.' if result else 'Failed to reconnect.')
        if result:
            self.scheduler.resume()

    async def on_gc_ready(self):
        logger.info('CS launched.')
        self.scheduler.start()

    async def on_gc_status_change(self, status: GcConnectionStatus):  # currently doesn't get called
        logger.info(f'{status.name!r} (on_gc_status_change)')

        statuses = {0: States.NORMAL, 1: States.INTERNAL_SERVER_ERROR, 2: States.OFFLINE,
                    3: States.RELOADING, 4: States.INTERNAL_STEAM_ERROR}
        game_coordinator = statuses.get(status.value, States.UNKNOWN)

        if game_coordinator != self.cache.get('game_coordinator'):
            self.update_cache({'game_coordinator': game_coordinator.literal})

        logger.info(f'Successfully dumped game coordinator status: {game_coordinator.literal}')

    async def update_depots(self):
        try:
            data = await self.fetch_product_info(apps=self.APPS_TO_FETCH)
            data = {int(app.id): app for app in data}
            logging.info(data)

            main_data = data[730]
            public_build_id = main_data.public_branch.build_id
            dpr_build_id = main_data.get_branch('dpr').build_id
            dprp_build_id = main_data.get_branch('dprp').build_id

            # currently can't track  todo: investigate, is it steam.py's issue or valve's
            # cs2_app_change_number = data[2275500].change_number
            # cs2_server_change_number = data[2275530].change_number
        except Exception:
            logger.exception('Caught an exception while trying to fetch depots!')
            return

        if public_build_id != self.cache.get('public_build_id'):
            t = asyncio.create_task(self.update_game_version())

        self.update_cache({
            'public_build_id': public_build_id,
            'dpr_build_id': dpr_build_id,
            'dprp_build_id': dprp_build_id,
            # 'cs2_app_changenumber': cs2_app_change_number,
            # 'cs2_server_changenumber': cs2_server_change_number
        })

        logger.info('Successfully dumped game build IDs.')

    async def update_game_version(self):
        timeout = 30 * 60
        timeout_start = time.time()
        while time.time() < timeout_start + timeout:
            try:
                data = GameVersion.request()

                # Made to ensure we will grab the latest public data if we *somehow* don't have anything cached
                no_cached_data = (self.cache.get('cs2_client_version') is None)

                # We also want to ensure that the data is up to date, so we check datetime
                new_data_datetime = (dt.datetime.fromisoformat(data.cs2_version_timestamp)
                                     .replace(tzinfo=VALVE_TIMEZONE).astimezone(dt.UTC))
                is_up_to_date = utime.utcnow() - new_data_datetime < dt.timedelta(hours=12)

                if no_cached_data or (is_up_to_date and data.cs2_client_version != self.cache.get('cs2_client_version')):
                    self.update_cache(data.asdict())
                    return
            except Exception:
                logging.exception('Caught an exception while trying to get new version!')
            await asyncio.sleep(45)

        # sometimes steamdb updates the info much later (xPaw: Zzz...)
        # because of this, we retry in an hour
        await asyncio.sleep(60 * 60)
        await self.update_game_version()

    # async def update_players_count(self):  # currently doesn't work
    #     value = await self.get_app(730).player_count()  # freezes the function entirely
    #     self.update_cache({'online_players': value})
    #
    #     logger.info(f'Successfully dumped player count: {value}')

    def load_cache(self):
        """Loads cache into ``self.cache``."""

        with open(self.cache_file_path, encoding='utf-8') as f:
            self.cache = json.load(f)

    def dump_cache(self):
        """Dumps ``self.cache`` to the cache file."""

        with open(self.cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=4)

    def update_cache(self, new_info: dict[str, ...]):
        """Loads the cache into ``self.cache``, updates it with new info and dumps back to the cache file."""

        self.load_cache()

        for k, v in new_info.items():
            self.cache[k] = v

        self.dump_cache()


def main():
    collector = GCCollector(cache_file_path=config.CACHE_FILE_PATH)
    collector.run(refresh_token=config.STEAM_REFRESH_TOKEN, debug=True)


if __name__ == '__main__':
    main()
