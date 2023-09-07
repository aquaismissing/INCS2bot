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

# noinspection PyUnresolvedReferences
import env
import config
from l10n import locale
from utypes import (ExchangeRate, DatacenterAtlas, Datacenter,
                    DatacenterRegion, DatacenterGroup, GameServersData,
                    State, get_monthly_unique_players)

execution_start_dt = dt.datetime.now()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

scheduler = AsyncIOScheduler()
bot = Client(config.BOT_CORE_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN,
             no_updates=True)


# noinspection PyTypeChecker
def remap_dc_info(info: dict):
    dcs = DatacenterAtlas.available_dcs()
    
    remapped_info = {}
    for _obj in dcs:
        if isinstance(_obj, Datacenter):
            remapped_info[_obj.id] = {'capacity': 'unknown', 'load': 'unknown'}

        if isinstance(_obj, DatacenterRegion):
            remapped_info[_obj.id] = {}
            for dc in _obj.datacenters:
                remapped_info[_obj.id][dc.id] = {'capacity': 'unknown', 'load': 'unknown'}
        
        if isinstance(_obj, DatacenterGroup):
            remapped_info[_obj.id] = {}
            for region in _obj.regions:
                remapped_info[_obj.id][region.id] = {}
                for dc in region.datacenters:
                    remapped_info[_obj.id][region.id][dc.id] = {'capacity': 'unknown', 'load': 'unknown'}

    # ремапим вручную, потому что писать ещё костыли не хочется
    remapped_info['south_africa']['johannesburg'] = info['South Africa']

    remapped_info['australia']['sydney'] = info['Australia']

    remapped_info['eu_north']['sweden']['stockholm'] = info['EU North']

    remapped_info['eu_west']['germany']['frankfurt'] = info['EU West']
    remapped_info['eu_west']['spain']['madrid'] = info['Spain']

    remapped_info['eu_east']['austria']['vienna'] = info['EU East']
    remapped_info['eu_east']['poland']['warsaw'] = info['Poland']

    remapped_info['us_north']['northcentral']['chicago'] = info['US Northcentral']
    remapped_info['us_north']['northeast']['sterling'] = info['US Northeast']
    remapped_info['us_north']['northwest']['moses_lake'] = info['US Northwest']

    remapped_info['us_south']['southwest']['los_angeles'] = info['US Southeast']
    remapped_info['us_south']['southeast']['atlanta'] = info['US Southwest']

    remapped_info['south_america']['brazil']['sao_paulo'] = info['Brazil']
    remapped_info['south_america']['chile']['santiago'] = info['Chile']
    remapped_info['south_america']['peru']['lima'] = info['Peru']
    remapped_info['south_america']['argentina']['buenos_aires'] = info['Argentina']

    remapped_info['hongkong'] = info['Hong Kong']

    remapped_info['india']['mumbai'] = info['India']
    remapped_info['india']['chennai'] = info['India East']

    remapped_info['china']['shanghai'] = info['China Shanghai']
    remapped_info['china']['tianjin'] = info['China Tianjin']
    remapped_info['china']['guangzhou'] = info['China Guangzhou']

    remapped_info['south_korea']['seoul'] = info['South Korea']

    remapped_info['singapore'] = info['Singapore']

    remapped_info['emirates']['dubai'] = info['Emirates']

    remapped_info['japan']['tokyo'] = info['Japan']

    return remapped_info


@scheduler.scheduled_job('interval', seconds=40)
async def update_cache_info():
    # noinspection PyBroadException
    try:
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        overall_data = GameServersData.request()

        for key, value in overall_data.asdict().items():
            if key == 'datacenters':
                continue
            if isinstance(value, State):
                value = value.literal
            cache[key] = value

        cache['datacenters'] = remap_dc_info(overall_data.datacenters)

        if cache['online_players'] > cache.get('player_alltime_peak', 0):
            if scheduler.get_job('players_peak') is None:
                scheduler.add_job(update_players_peak,
                                  next_run_time=dt.datetime.now() + dt.timedelta(minutes=15), coalesce=True)
            cache['player_alltime_peak'] = cache['online_players']

        df = pd.read_csv(config.PLAYER_CHART_FILE_PATH, parse_dates=['DateTime'])
        now = dt.datetime.now(dt.UTC)
        end_date = f'{now:%Y-%m-%d %H:%M:%S}'
        start_date = f'{(now - dt.timedelta(days=1)):%Y-%m-%d %H:%M:%S}'
        mask = (df['DateTime'] > start_date) & (df['DateTime'] <= end_date)
        player_24h_peak = int(df.loc[mask]['Players'].max())

        if player_24h_peak != cache.get('player_24h_peak', 0):
            cache['player_24h_peak'] = player_24h_peak

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception:
        logging.exception('Caught exception in the main thread!')


@scheduler.scheduled_job('cron', hour=execution_start_dt.hour, minute=execution_start_dt.minute + 1)
async def unique_monthly():
    # noinspection PyBroadException
    try:
        data = get_monthly_unique_players()

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        if data != cache.get('monthly_unique_players'):
            cache['monthly_unique_players'] = data
            await send_alert('monthly_unique_players',
                             (cache['monthly_unique_players'], data))

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception:
        logging.exception('Caught exception while gathering monthly players!')
        time.sleep(45)
        return await unique_monthly()


@scheduler.scheduled_job('cron', hour=execution_start_dt.hour, minute=execution_start_dt.minute + 1)
async def check_currency():
    # noinspection PyBroadException
    try:
        new_prices = ExchangeRate.request()

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        if new_prices != cache.get('key_price'):
            cache['key_price'] = new_prices

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception:
        logging.exception('Caught exception while gathering key price!')
        time.sleep(45)
        return await check_currency()


async def update_players_peak():
    try:
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        await send_alert('online_players', cache['player_alltime_peak'])
    except Exception:
        logging.exception('Caught exception while alerting players peak!')
        time.sleep(45)
        return await update_players_peak()


async def send_alert(key, new_value):
    loc = locale('ru')
    
    if key == 'online_players':
        text = loc.notifs_new_playerspeak.format(new_value)
    elif key == 'monthly_unique_players':
        text = loc.notifs_new_monthlyunique.format(*new_value)
    else:
        logging.warning(f'Got wrong key to send alert: {key}')
        return

    if not config.TEST_MODE:
        chat_list = [config.INCS2CHAT, config.CSTRACKER]
    else:
        chat_list = [config.AQ]

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


if __name__ == '__main__':
    main()
