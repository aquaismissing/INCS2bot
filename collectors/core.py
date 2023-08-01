import datetime as dt
import json
import logging
from threading import Thread
import time

import asyncio
import pandas as pd
from pyrogram import Client
from pyrogram.enums import ParseMode

import config
from utypes import (ExchangeRate, DatacenterAtlas, Datacenter,
                    DatacenterRegion, DatacenterGroup, GameServersData,
                    State, get_monthly_unique_players)
from l10n import locale

HOUR = 60 * 60

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(threadName)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")
bot = Client(config.BOT_CORE_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN)


# noinspection PyTypeChecker
def remap_dc_info(info: dict):
    dcs = DatacenterAtlas.available_dcs()
    
    remapped_info = {}
    for _obj in dcs:
        if isinstance(_obj, Datacenter):
            remapped_info[_obj.id] = {"capacity": "unknown", "load": "unknown"}

        if isinstance(_obj, DatacenterRegion):
            remapped_info[_obj.id] = {}
            for dc in _obj.datacenters:
                remapped_info[_obj.id][dc.id] = {"capacity": "unknown", "load": "unknown"}
        
        if isinstance(_obj, DatacenterGroup):
            remapped_info[_obj.id] = {}
            for region in _obj.regions:
                remapped_info[_obj.id][region.id] = {}
                for dc in region.datacenters:
                    remapped_info[_obj.id][region.id][dc.id] = {"capacity": "unknown", "load": "unknown"}

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

    remapped_info['us_south']['southeast']['los_angeles'] = info['US Southeast']
    remapped_info['us_south']['southwest']['atlanta'] = info['US Southwest']

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


def info_updater_prepare():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(info_updater())
    loop.close()


async def info_updater():
    while True:
        logging.info("New session started..")

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
                cache['player_alltime_peak'] = cache['online_players']
                await send_alert('online_players', cache['player_alltime_peak'])

            df = pd.read_csv(config.PLAYER_CHART_FILE_PATH, parse_dates=['DateTime'])
            end_date = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            start_date = (dt.datetime.utcnow() - dt.timedelta(days=1)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            mask = (df["DateTime"] > start_date) & (df["DateTime"] <= end_date)
            player_24h_peak = int(df.loc[mask]["Players"].max())

            if player_24h_peak != cache.get("player_24h_peak", 0):
                cache['player_24h_peak'] = player_24h_peak

            with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f)

            time.sleep(40)
        except Exception:
            logging.exception("Caught exception in the main thread!")
            time.sleep(40)


def unique_monthly_prepare():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(unique_monthly())
    loop.close()


async def unique_monthly():
    while True:
        logging.info("Checking monthly unique players..")

        try:
            data = get_monthly_unique_players()

            with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
                cache = json.load(f)

            if data != cache.get("monthly_unique_players"):
                cache['monthly_unique_players'] = data
                await send_alert("monthly_unique_players",
                                 (cache["monthly_unique_players"], data["monthly_unique_players"]))

            with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f)
        except Exception:
            logging.exception("Caught exception while gathering monthly players!")
            time.sleep(45)
            continue

        time.sleep(24 * HOUR)


def check_currency():
    while True:
        logging.info("Checking key price..")

        try:
            new_prices = ExchangeRate.request()

            with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
                cache = json.load(f)

            if new_prices != cache.get('key_price'):
                cache['key_price'] = new_prices

            with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f)
        except Exception:
            logging.exception("Caught exception while gathering key price!")
            time.sleep(45)
            continue

        time.sleep(24 * HOUR)


async def send(chat_list, text):
    if not bot.is_connected:
        await asyncio.sleep(4)

    for chat_id in chat_list:
        msg = await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        if chat_id == config.INCS2CHAT:
            await msg.pin(disable_notification=True)


async def send_alert(key, new_value):
    loc = locale('ru')
    
    if key == "online_players":
        text = loc.notifs_new_playerspeak.format(new_value)
    elif key == "monthly_unique_players": 
        text = loc.notifs_new_monthlyunique.format(*new_value)
    else:
        logging.warning(f"Got wrong key to send alert: {key}")
        return

    if not config.TEST_MODE:
        chat_list = [config.INCS2CHAT, config.AQ]
    else:
        chat_list = [config.AQ]

    await send(chat_list, text)


def main():
    t1 = Thread(target=info_updater_prepare)
    t2 = Thread(target=unique_monthly_prepare)
    t3 = Thread(target=check_currency)

    t1.start()
    t2.start()
    t3.start()

    bot.run()


if __name__ == "__main__":
    main()
