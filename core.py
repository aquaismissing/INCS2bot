import datetime as dt
import json
import logging
import platform
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pandas as pd
from pyrogram import Client
if platform.system() == 'Linux':
    # noinspection PyPackageRequirements
    import uvloop

    uvloop.install()

import config
from functions import utime
from l10n import locale
from utypes import (ExchangeRate, DatacenterAtlas, Datacenter,
                    DatacenterRegion, DatacenterGroup, GameServers,
                    LeaderboardStats, State, SteamWebAPI,
                    LEADERBOARD_API_REGIONS)


DATACENTER_API_FIELDS = {
    ('south_africa', 'johannesburg'): 'South Africa',
    ('australia', 'sydney'): 'Australia',
    ('sweden', 'stockholm'): 'EU Sweden',
    ('germany', 'frankfurt'): 'EU Germany',
    ('finland', 'helsinki'): 'EU Finland',
    ('spain', 'madrid'): 'EU Spain',
    ('netherlands', 'amsterdam'): 'EU Holland',
    ('austria', 'vienna'): 'EU Austria',
    ('poland', 'warsaw'): 'EU Poland',
    ('us_east', 'chicago'): 'US Chicago',
    ('us_east', 'sterling'): 'US Virginia',
    ('us_east', 'new_york'): 'US NewYork',
    ('us_east', 'atlanta'): 'US Atlanta',
    ('us_west', 'seattle'): 'US Seattle',
    ('us_west', 'los_angeles'): 'US California',
    ('brazil', 'sao_paulo'): 'Brazil',
    ('chile', 'santiago'): 'Chile',
    ('peru', 'lima'): 'Peru',
    ('argentina', 'buenos_aires'): 'Argentina',
    'hongkong': 'Hong Kong',
    ('india', 'mumbai'): 'India Mumbai',
    ('india', 'chennai'): 'India Chennai',
    ('india', 'bombay'): 'India Bombay',
    ('india', 'madras'): 'India Madras',
    ('china', 'shanghai'): 'China Shanghai',
    ('china', 'tianjin'): 'China Tianjin',
    ('china', 'guangzhou'): 'China Guangzhou',
    ('china', 'chengdu'): 'China Chengdu',
    ('south_korea', 'seoul'): 'South Korea',
    'singapore': 'Singapore',
    ('emirates', 'dubai'): 'Emirates',
    ('japan', 'tokyo'): 'Japan',
}


UNUSED_FIELDS = ['csgo_client_version',
                 'csgo_server_version',
                 'csgo_patch_version',
                 'csgo_version_timestamp',
                 'sdk_build_id',
                 'ds_build_id',
                 'valve_ds_changenumber',
                 'webapi',
                 'sessions_logon',
                 'steam_community',
                 'matchmaking_scheduler',
                 'game_coordinator']


execution_start_dt = dt.datetime.now()

execution_cron_hour = execution_start_dt.hour
execution_cron_minute = execution_start_dt.minute + 1
if execution_cron_minute >= 60:
    execution_cron_hour += 1
    execution_cron_minute %= 60

loc = locale('ru')

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

scheduler = AsyncIOScheduler()
bot = Client(config.BOT_CORE_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN,
             no_updates=True,
             workdir=config.SESS_FOLDER)
steam_webapi = SteamWebAPI(config.STEAM_API_KEY, headers=config.REQUESTS_HEADERS)


def clear_from_unused_fields(cache: dict):
    for field in UNUSED_FIELDS:
        if cache.get(field):
            del cache[field]


def remap_dc(info: dict, dc: Datacenter):
    api_info_field = DATACENTER_API_FIELDS[dc.id]
    return info[api_info_field]


def remap_dc_region(info: dict, region: DatacenterRegion):
    result = {}
    for dc in region.datacenters:
        api_info_field = DATACENTER_API_FIELDS[region.id, dc.id]
        result[dc.id] = info[api_info_field]

    return result


def remap_dc_group(info: dict, group: DatacenterGroup):
    result = {}
    for region in group.regions:
        result[region.id] = {}
        for dc in region.datacenters:
            api_info_field = DATACENTER_API_FIELDS[group.id, region.id, dc.id]
            result[region.id][dc.id] = info[api_info_field]

    return result


def remap_datacenters_info(info: dict) -> dict:
    dcs = DatacenterAtlas.available_dcs()
    
    remapped_info = {}
    for _obj in dcs:
        match _obj:
            case Datacenter(id=_id):
                remapped_info[_id] = remap_dc(info, _obj)

            case DatacenterRegion(id=_id):
                remapped_info[_id] = remap_dc_region(info, _obj)

            case DatacenterGroup(id=_id):
                remapped_info[_id] = remap_dc_group(info, _obj)

    return remapped_info


@scheduler.scheduled_job('interval', seconds=40)
async def update_cache_info():
    # noinspection PyBroadException
    try:
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        clear_from_unused_fields(cache)

        overall_data = GameServers.request(steam_webapi)

        for key, value in overall_data.asdict().items():
            if key == 'datacenters':
                continue
            if isinstance(value, State):
                value = value.literal
            cache[key] = value

        cache['datacenters'] = remap_datacenters_info(overall_data.datacenters)

        if cache['online_players'] > cache.get('player_alltime_peak', 0):
            if scheduler.get_job('players_peak') is None:
                scheduler.add_job(update_players_peak, id='players_peak',  # to collect new peak for 15 minutes and then post the highest one
                                  next_run_time=dt.datetime.now() + dt.timedelta(minutes=15), coalesce=True)
            cache['player_alltime_peak'] = cache['online_players']

        df = pd.read_csv(config.PLAYER_CHART_FILE_PATH, parse_dates=['DateTime'])
        now = utime.utcnow()
        end_date = f'{now:%Y-%m-%d %H:%M:%S}'
        start_date = f'{(now - dt.timedelta(days=1)):%Y-%m-%d %H:%M:%S}'
        mask = (df['DateTime'] > start_date) & (df['DateTime'] <= end_date)
        player_24h_peak = int(df.loc[mask]['Players'].max())

        if player_24h_peak != cache.get('player_24h_peak', 0):
            cache['player_24h_peak'] = player_24h_peak

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception:
        logging.exception('Caught exception in the main thread!')

        
@scheduler.scheduled_job('cron', hour=execution_cron_hour, minute=execution_cron_minute)
async def unique_monthly():
    # noinspection PyBroadException
    try:
        data = steam_webapi.csgo_get_monthly_player_count()

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        if cache.get('monthly_unique_players') is None:
            cache['monthly_unique_players'] = data

        if data != cache.get('monthly_unique_players'):
            await send_alert('monthly_unique_players',
                             (cache['monthly_unique_players'], data))
            cache['monthly_unique_players'] = data

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception:
        logging.exception('Caught exception while gathering monthly players!')
        time.sleep(45)
        return await unique_monthly()


@scheduler.scheduled_job('cron', hour=execution_cron_hour, minute=execution_cron_minute)
async def check_currency():
    # noinspection PyBroadException
    try:
        new_prices = ExchangeRate.request(steam_webapi).asdict()

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        if new_prices != cache.get('key_price'):
            cache['key_price'] = new_prices

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception:
        logging.exception('Caught exception while gathering key price!')
        time.sleep(45)
        return await check_currency()


@scheduler.scheduled_job('cron', hour=execution_cron_hour, minute=execution_cron_minute, second=30)
async def fetch_leaderboard():
    # noinspection PyBroadException
    try:
        world_leaderboard_stats = LeaderboardStats.request_world(steam_webapi.session)

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        if world_leaderboard_stats != cache.get('world_leaderboard_stats'):
            cache['world_leaderboard_stats'] = world_leaderboard_stats

        for region in LEADERBOARD_API_REGIONS:
            regional_leaderboard_stats = LeaderboardStats.request_regional(steam_webapi.session, region)

            if regional_leaderboard_stats != cache.get(f'regional_leaderboard_stats_{region}'):
                cache[f'regional_leaderboard_stats_{region}'] = regional_leaderboard_stats

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception:
        logging.exception('Caught exception fetching leaderboards!')
        time.sleep(45)
        return await fetch_leaderboard()


async def update_players_peak():
    # noinspection PyBroadException
    try:
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        await send_alert('online_players', cache['player_alltime_peak'])
    except Exception:
        logging.exception('Caught exception while alerting players peak!')
        time.sleep(45)
        return await update_players_peak()


async def send_alert(key, new_value):
    if key == 'online_players':
        text = loc.notifs_new_playerspeak.format(new_value)
    elif key == 'monthly_unique_players':
        text = loc.notifs_new_monthlyunique.format(*new_value)
    else:
        logging.warning(f'Got wrong key to send alert: {key}')
        return

    if config.TEST_MODE:
        chat_list = [config.AQ]
    else:
        chat_list = [config.INCS2CHAT, config.CSTRACKER]

    for chat_id in chat_list:
        msg = await bot.send_message(chat_id, text)
        if chat_id == config.INCS2CHAT:
            await msg.pin(disable_notification=True)


def main():
    try:
        scheduler.start()
        bot.run()
    except TypeError:  # catching TypeError because Pyrogram propogates it at stop for some reason
        logging.info('Shutting down the bot...')
    finally:
        steam_webapi.close()


if __name__ == '__main__':
    main()
