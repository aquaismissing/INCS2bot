import asyncio
import datetime as dt
import platform
from functools import wraps

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pandas as pd
# noinspection PyPackageRequirements
from pyrogram import Client
if platform.system() == 'Linux':
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import uvloop

    uvloop.install()

import config
from dcatlas import DatacenterAtlas
from functions import caching, utime
from functions.ulogging import get_logger
from l10n import locale
from utypes import ExchangeRate, GameServers, State, SteamWebAPI
from utypes import LeaderboardStats, LEADERBOARD_API_REGIONS

execution_start_dt = dt.datetime.now()
execution_cron = (execution_start_dt + dt.timedelta(minutes=2)).replace(second=0)

CURRENT_PREMIER_SEASON = 3
UPDATE_CACHE_INTERVAL = 40

loc = locale('ru')

logger = get_logger('core', config.LOGS_FOLDER, config.LOGS_CONFIG_FILE_PATH)

scheduler = AsyncIOScheduler()
bot = Client(config.BOT_CORE_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN,
             test_mode=config.TEST_MODE,
             no_updates=True,
             workdir=config.SESS_FOLDER)
steam_webapi = SteamWebAPI(config.STEAM_API_KEY, headers=config.REQUESTS_HEADERS)


def exception_handler(*, message: str, retry: bool = False, timeout: int = 45):
    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            # noinspection PyBroadException
            try:
                await func(*args, **kwargs)
            except Exception:
                logger.exception(message)
                if retry:
                    await asyncio.sleep(timeout)
                    return await inner(*args, **kwargs)

        return inner
    return decorator


def remap_datacenters_info(info: dict[str, dict[str, str]]):
    return {dc.id: dc.remap(info) for dc in DatacenterAtlas.available_dcs()}


def get_player_24h_peak(df: pd.DataFrame):
    now = utime.utcnow()
    end_date = f'{now:%Y-%m-%d %H:%M:%S}'
    start_date = f'{(now - dt.timedelta(days=1)):%Y-%m-%d %H:%M:%S}'
    mask = (df['DateTime'] > start_date) & (df['DateTime'] <= end_date)

    player_24h_peak = df.loc[mask]['Players'].max()
    return int(player_24h_peak) if pd.notna(player_24h_peak) else 0


@scheduler.scheduled_job('interval', seconds=UPDATE_CACHE_INTERVAL)
@exception_handler(message='Caught exception while updating the cache!')
async def update_cache_info():
    cache = caching.load_cache(config.CORE_CACHE_FILE_PATH)
    gc_cache = caching.load_cache(config.GC_CACHE_FILE_PATH)

    game_servers_data = GameServers.request(steam_webapi)

    for key, value in game_servers_data.asdict().items():
        if key == 'datacenters':
            continue
        if isinstance(value, State):
            value = value.literal
        cache[key] = value

    cache['datacenters'] = remap_datacenters_info(game_servers_data.datacenters)

    if gc_cache.get('online_players', 0) > cache.get('player_alltime_peak', 1):
        if scheduler.get_job('players_peak') is None:
            # to collect new peak for 15 minutes and then post the highest one
            delay = dt.datetime.now() + dt.timedelta(minutes=15)
            scheduler.add_job(alert_players_peak, id='players_peak', next_run_time=delay, coalesce=True)
        cache['player_alltime_peak'] = gc_cache['online_players']

    df = pd.read_csv(config.PLAYER_CHART_FILE_PATH, parse_dates=['DateTime'])
    cache['player_24h_peak'] = get_player_24h_peak(df)

    caching.dump_cache(config.CORE_CACHE_FILE_PATH, cache)

        
@scheduler.scheduled_job('cron',
                         hour=execution_cron.hour, minute=execution_cron.minute, second=0)
@exception_handler(message='Caught exception while gathering monthly players!', retry=True)
async def unique_monthly():
    new_player_count = steam_webapi.cs2_get_monthly_player_count()

    cache = caching.load_cache(config.CORE_CACHE_FILE_PATH)

    if cache.get('monthly_unique_players') is None:
        cache['monthly_unique_players'] = new_player_count

    if new_player_count != cache['monthly_unique_players']:
        await send_alert('monthly_unique_players',
                         (cache['monthly_unique_players'], new_player_count))
        cache['monthly_unique_players'] = new_player_count

    caching.dump_cache(config.CORE_CACHE_FILE_PATH, cache)


@scheduler.scheduled_job('cron',
                         hour=execution_cron.hour, minute=execution_cron.minute, second=0)
@exception_handler(message='Caught exception while gathering key price!', retry=True)
async def check_currency():
    new_prices = ExchangeRate.request(steam_webapi).asdict()

    caching.dump_cache_changes(config.CORE_CACHE_FILE_PATH, {'key_price': new_prices})


@scheduler.scheduled_job('cron',
                         hour=execution_cron.hour, minute=execution_cron.minute, second=0)
async def fetch_leaderboard():
    # noinspection PyBroadException
    try:
        world_leaderboard_stats = LeaderboardStats.request_world(steam_webapi, season=CURRENT_PREMIER_SEASON)

        new_data = {'world_leaderboard_stats': world_leaderboard_stats}

        for region in LEADERBOARD_API_REGIONS:
            regional_leaderboard_stats = LeaderboardStats.request_regional(steam_webapi,
                                                                           season=CURRENT_PREMIER_SEASON, region=region)
            new_data[f'regional_leaderboard_stats_{region}'] = regional_leaderboard_stats

        caching.dump_cache_changes(config.LEADERBOARD_SEASON3_CACHE_FILE_PATH, new_data)
    except requests.exceptions.JSONDecodeError:  # leaderboards closed?
        pass
    except Exception:
        logger.exception('Caught exception fetching leaderboards!')
        await asyncio.sleep(45)
        return await fetch_leaderboard()


@exception_handler(message='Caught exception while gathering key price!', retry=True)
async def alert_players_peak():
    cache = caching.load_cache(config.CORE_CACHE_FILE_PATH)

    await send_alert('online_players', cache['player_alltime_peak'])


async def send_alert(key, new_value):
    if key == 'online_players':
        text = loc.notifs_new_playerspeak.format(new_value)
    elif key == 'monthly_unique_players':
        text = loc.notifs_new_monthlyunique.format(*new_value)
    else:
        logger.warning(f'Got wrong key to send alert: {key}')
        return

    if bot.test_mode:
        chat_list = [config.AQ]
    else:
        chat_list = [config.INCS2CHAT, config.CSTRACKER]

    for chat_id in chat_list:
        msg = await bot.send_message(chat_id, text)
        if chat_id == config.INCS2CHAT:
            await msg.pin(disable_notification=True)


def main():
    logger.info('Started.')
    try:
        scheduler.start()
        bot.run()
    except TypeError:  # catching TypeError because Pyrogram propagates it at stop for some reason
        logger.info('Shutting down the bot...')
    finally:
        scheduler.shutdown()
        steam_webapi.close()
        logger.info('Terminated.')


if __name__ == '__main__':
    main()
