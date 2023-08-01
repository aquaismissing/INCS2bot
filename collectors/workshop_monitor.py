import asyncio
import logging
import re
import time

import config
import requests
from pyrogram import Client
from pyrogram.enums import ParseMode
from l10n import locale

workshop_url = f"https://api.steampowered.com/IPublishedFileService/GetUserFiles/v1/?key={config.STEAM_API_KEY}" \
               f"&steamid={config.CS_STEAM_PROFILE_ID}&appid={config.CS_APP_ID}&page=1&numperpage=18"
pattern = r"\[.*?\]"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")
bot = Client(config.BOT_WM_MODULE_NAME,
             api_id=config.API_ID,
             api_hash=config.API_HASH,
             bot_token=config.BOT_TOKEN)


def _get_initial_ids():
    try:
        initial_data = requests.get(workshop_url, timeout=15).json()["response"]["publishedfiledetails"]
        return [_map["publishedfileid"] for _map in initial_data]
    except Exception:
        logging.exception(f"Caught an exception at initial run!")
        time.sleep(45)


def _get_rerun_data():
    try:
        return requests.get(workshop_url, timeout=15).json()["response"]["publishedfiledetails"]
    except Exception:
        logging.exception(f"Caught an exception at rerun!")
        time.sleep(45)


def _get_updated_maps(maps_data, maps_ids):
    try:
        return {x["publishedfileid"]: re.sub(pattern, "", x['title']).strip()
                for x in maps_data if x["publishedfileid"] in maps_ids}
    except Exception:
        logging.exception(f"Caught an exception at map names remapping!")
        time.sleep(45)


def _format_updated_maps_data(updated_maps):
    ru_loc = locale('ru')

    if len(updated_maps) == 1:
        map_id, map_name = updated_maps.items()[0]
        return ru_loc.notifs_new_map.format(map_id, map_name, map_id)

    maps_names = updated_maps.values()
    maps_names = " и ".join(maps_names if len(maps_names) == 2
                            else [", ".join(maps_names.values()[:-1]), maps_names[-1]])
    return ru_loc.notifs_new_map_multiple.format(maps_names)


async def main():
    logging.info("Starting initial run...")
    initial_ids = []
    while not initial_ids:  # пока не наберётся начальный набор данных
        initial_ids = _get_initial_ids()

    while True:  # главная часть
        logging.info("Rerunning...")

        rerun_data = _get_rerun_data()
        
        if not rerun_data:
            continue

        rerun_ids = [_map["publishedfileid"] for _map in rerun_data]

        if rerun_ids != initial_ids:
            new_ids = [_id for _id in rerun_ids if _id not in initial_ids]

            updated_maps = _get_updated_maps(rerun_data, new_ids)
            text = _format_updated_maps_data(updated_maps)

            await send_alert(text)
            initial_ids = rerun_ids
        logging.info(f"Rerun ended, sleeping for 45 seconds.")
        time.sleep(45)


async def send(chat_list, text):
    if not bot.is_connected:
        await asyncio.sleep(4)

    for chat_id in chat_list:
        msg = await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
        if chat_id == config.INCS2CHAT:
            await msg.pin(disable_notification=True)


async def send_alert(text):
    logging.info("Maps got updated! Sending alert...")

    if not config.TEST_MODE:
        chat_list = [config.INCS2CHAT, config.CSTRACKER]
    else:
        chat_list = [config.AQ]

    await send(chat_list, text)


if __name__ == "__main__":
    asyncio.run(main())
