import asyncio
import datetime as dt
import json
import logging
from zoneinfo import ZoneInfo

from babel.dates import format_datetime
import pandas as pd
from pyrogram import filters
from pyrogram.enums import ChatType, ChatAction
from pyrogram.errors import MessageDeleteForbidden
from pyrogram.types import CallbackQuery, Message
# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!
from telegraph import Telegraph

import config
import keyboards
from keyboards import TranslatableIKB, TranslatableIKM
from functions import datacenter_handlers, server_stats_handlers, ufilters
from functions.askers import *
from functions.decorators import *
from functions.logs import *
from l10n import LocaleKeys as LK
from utypes import (BClient, Crosshair, ExchangeRate, GameServersData,
                    GameVersionData, GunInfo, ParsingUserStatsError, ProfileInfo,
                    States, UserGameStats, drop_cap_reset_timer)

VALVE_TIMEZONE = ZoneInfo("America/Los_Angeles")
GUNS_INFO = GunInfo.load()
CLOCKS = ('🕛', '🕐', '🕑', '🕒', '🕓', '🕔',
          '🕕', '🕖', '🕗', '🕘', '🕙', '🕚')


bot = BClient(config.BOT_NAME,
              api_id=config.API_ID,
              api_hash=config.API_HASH,
              bot_token=config.BOT_TOKEN,
              plugins={'root': 'plugins'})

ALL_COMMANDS = ['start', 'help', 'feedback']

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(threadName)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")


# cat: Main


def log_exception_callback(func):
    """Decorator to catch and log exceptions in bot functions. Also call `something_went_wrong(message)`."""

    async def inner(client: BClient, callback_query: CallbackQuery, *args, **kwargs):
        try:
            await func(client, callback_query, *args, **kwargs)
        except Exception as e:
            logging.exception('Caught exception!')
            await client.send_message(config.LOGCHANNEL, f'❗️{e}', disable_notification=True)
            await something_went_wrong(client, callback_query)

    return inner


@bot.on_message(~filters.me)
async def sync_user_data(client: BClient, message: Message):
    if message.chat.type != ChatType.PRIVATE:
        message.continue_propagation()

    user = message.from_user
    await log(client, message)

    data = pd.read_csv(config.USER_DB_FILE_PATH)
    if not data["UserID"].isin([user.id]).any():
        new_data = pd.DataFrame(
            [
                [
                    user.first_name,
                    user.id,
                    user.language_code,
                ]
            ],
            columns=["Name", "UserID", "Language"],
        )
        pd.concat([data, new_data]).to_csv(config.USER_DB_FILE_PATH, index=False)

    client.clear_timeout_sessions()
    if user.id not in client.sessions:
        client.register_session(user)

    client.current_session = client.sessions[user.id]

    message.continue_propagation()


@bot.on_message(filters.command(ALL_COMMANDS))
async def any_command(client: BClient, message: Message):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    if message.chat.type != ChatType.PRIVATE:
        await log(client, message)

        user = message.from_user

        client.clear_timeout_sessions()
        if user.id not in client.sessions:
            client.register_session(user)

        client.current_session = client.sessions[user.id]

    message.continue_propagation()


@bot.on_callback_query()
async def sync_user_data_callback(client: BClient, callback_query: CallbackQuery):
    if callback_query.message.chat.type != ChatType.PRIVATE:
        return

    user = callback_query.from_user
    await log_callback(client, callback_query)

    data = pd.read_csv(config.USER_DB_FILE_PATH)
    if not data["UserID"].isin([user.id]).any():
        new_data = pd.DataFrame(
            [
                [
                    user.first_name,
                    user.id,
                    user.language_code,
                ]
            ],
            columns=["Name", "UserID", "Language"],
        )
        pd.concat([data, new_data]).to_csv(config.USER_DB_FILE_PATH, index=False)

    client.clear_timeout_sessions()
    if user.id not in client.sessions:
        client.register_session(user)

    client.current_session = client.sessions[user.id]

    callback_query.continue_propagation()


@bot.on_callback_query(ufilters.callback_data_equals('main'))
@log_exception_callback
async def main(client: BClient, callback_query: CallbackQuery, session_timeout: bool = False):
    if session_timeout:
        text = client.locale.error_session_timeout + '\n\n' + client.locale.bot_choose_cmd
    else:
        text = client.locale.bot_choose_cmd

    await callback_query.edit_message_text(text, reply_markup=keyboards.main_markup(client.locale))


@bot.on_callback_query(ufilters.callback_data_is_gun_filter)
@ignore_message_not_modified
async def handle_back_after_reload(client: BClient, callback_query: CallbackQuery):
    """After bot reload, the gun database menu gets stuck. This func recovers dialog by calling `main`."""

    return await main(client, callback_query, session_timeout=True)


# cat: Server stats


@bot.on_callback_query(ufilters.callback_data_equals(LK.bot_servers_stats))
@came_from(main)
@ignore_message_not_modified
async def server_stats(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.bot_choose_cmd,
                                           reply_markup=keyboards.markup_ss(client.locale))


@log_exception_callback
@bot.on_callback_query(ufilters.callback_data_equals(LK.game_status_button_title))
@ignore_message_not_modified
async def send_server_status(client: BClient, callback_query: CallbackQuery):
    """Send the status of Counter-Strike servers"""

    lang_code = callback_query.from_user.language_code

    data = GameServersData.cached_server_status()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, callback_query)

    text = server_stats_handlers.get_server_status_summary(data, lang_code)

    await callback_query.edit_message_text(text, reply_markup=keyboards.markup_ss(client.locale))


@log_exception_callback
@bot.on_callback_query(ufilters.callback_data_equals(LK.stats_matchmaking_button_title))
@ignore_message_not_modified
async def send_matchmaking_stats(client: BClient, callback_query: CallbackQuery):
    """Send Counter-Strike matchamaking statistics"""

    lang_code = callback_query.from_user.language_code

    data = GameServersData.cached_matchmaking_stats()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, callback_query)

    text = server_stats_handlers.get_matchmaking_stats_summary(data, lang_code)

    await callback_query.edit_message_text(text, reply_markup=keyboards.markup_ss(client.locale))


# cat: Datacenters


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_status_title))
@came_from(server_stats)
@ignore_message_not_modified
async def datacenters(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.dc_status_choose_region,
                                           reply_markup=keyboards.markup_dc(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_asia))
@came_from(datacenters)
@ignore_message_not_modified
async def dc_asia(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.dc_status_specify_country,
                                           reply_markup=keyboards.markup_dc_asia(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_europe))
@came_from(datacenters)
@ignore_message_not_modified
async def dc_europe(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.dc_status_specify_region,
                                           reply_markup=keyboards.markup_dc_eu(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_us))
@came_from(datacenters)
@ignore_message_not_modified
async def dc_us(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.dc_status_specify_region,
                                           reply_markup=keyboards.markup_dc_us(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_africa))
async def send_dc_africa(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.africa(client.session_lang_code),
                        keyboards.markup_dc(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_australia))
async def send_dc_australia(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.australia(client.session_lang_code),
                        keyboards.markup_dc(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_eu_north))
async def send_dc_eu_north(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.eu_north(client.session_lang_code),
                        keyboards.markup_dc_eu(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_eu_east))
async def send_dc_eu_west(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.eu_west(client.session_lang_code),
                        keyboards.markup_dc_eu(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_eu_west))
async def send_dc_eu_east(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.eu_east(client.session_lang_code),
                        keyboards.markup_dc_eu(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_us_north))
async def send_dc_us_north(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.us_north(client.session_lang_code),
                        keyboards.markup_dc_us(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_us_south))
async def send_dc_us_south(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.us_south(client.session_lang_code),
                        keyboards.markup_dc_us(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_southamerica))
async def send_dc_south_america(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.south_america(client.session_lang_code),
                        keyboards.markup_dc(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_india))
async def send_dc_india(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.india(client.session_lang_code),
                        keyboards.markup_dc_asia(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_japan))
async def send_dc_japan(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.japan(client.session_lang_code),
                        keyboards.markup_dc_asia(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_china))
async def send_dc_china(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.china(client.session_lang_code),
                        keyboards.markup_dc_asia(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_emirates))
async def send_dc_emirates(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.emirates(client.session_lang_code),
                        keyboards.markup_dc_asia(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_singapore))
async def send_dc_singapore(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.singapore(client.session_lang_code),
                        keyboards.markup_dc_asia(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_hongkong))
async def send_dc_hongkong(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.hongkong(client.session_lang_code),
                        keyboards.markup_dc_asia(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.dc_southkorea))
async def send_dc_south_korea(client: BClient, callback_query: CallbackQuery):
    await send_dc_state(client, callback_query,
                        datacenter_handlers.south_korea(client.session_lang_code),
                        keyboards.markup_dc_asia(client.locale))


@ignore_message_not_modified
async def send_dc_state(client: BClient, callback_query: CallbackQuery,
                        state: str | States, reply_markup: TranslatableIKM):
    if state == States.UNKNOWN:
        return await something_went_wrong(client, callback_query)

    await callback_query.edit_message_text(state, reply_markup=reply_markup)


# cat: Profile info


@bot.on_callback_query(ufilters.callback_data_equals(LK.bot_profile_info))
@came_from(main)
@ignore_message_not_modified
async def profile_info(client: BClient, callback_query: CallbackQuery):
    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache_file = json.load(f)

    if cache_file['webapi'] != 'normal':
        return await send_about_maintenance(client, callback_query)

    await callback_query.edit_message_text(client.locale.bot_choose_cmd,
                                           reply_markup=keyboards.markup_profile(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.user_profileinfo_title))
@log_exception_callback
async def user_profile_info(client: BClient, callback_query: CallbackQuery):
    steam_url: Message = await ask_message_silently(client, callback_query, client.locale.steam_url_example)

    if steam_url.text == "/cancel":
        await steam_url.delete()
        return await profile_info(client, callback_query)

    await client.send_chat_action(callback_query.message.chat.id, ChatAction.TYPING)

    try:
        info = ProfileInfo.get(steam_url.text)
    except ParsingUserStatsError as e:
        if e.value == ParsingUserStatsError.INVALID_REQUEST:
            error_msg = client.locale.error_unknownrequest
        elif e.value == ParsingUserStatsError.PRIVATE_INFO:
            error_msg = '<a href="https://i.imgur.com/CAjblvT.mp4">‎</a>' + \
                        client.locale.user_gamestats_privateprofile_error
        else:
            raise e

        await callback_query.message.reply(error_msg)
        await callback_query.message.reply(client.locale.bot_choose_cmd,
                                           reply_markup=keyboards.markup_profile(client.locale))
        return await callback_query.message.delete()

    if info.vanity_url is None:
        info.vanity_url = client.locale.user_profileinfo_notset

    info.faceit_ban = client.locale.user_profileinfo_banned \
        if info.faceit_ban else client.locale.user_profileinfo_none

    if info.faceit_lvl is None:
        info.faceit_lvl = client.locale.user_profileinfo_none
        info.faceit_elo = client.locale.user_profileinfo_none

    if info.faceit_url is None:
        info.faceit_url = client.locale.user_profileinfo_notfound

    if info.vac_bans == 0:
        info.vac_bans = client.locale.user_profileinfo_none

    if info.game_bans == 0:
        info.game_bans = client.locale.user_profileinfo_none

    info.community_ban = client.locale.user_profileinfo_banned \
        if info.community_ban else client.locale.user_profileinfo_none

    info.trade_ban = client.locale.user_profileinfo_banned \
        if info.trade_ban else client.locale.user_profileinfo_none

    text = client.locale.user_profileinfo_text.format(*info.to_tuple())

    await callback_query.message.reply(text, disable_web_page_preview=True)
    await callback_query.message.reply(client.locale.bot_choose_cmd,
                                       reply_markup=keyboards.markup_profile(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.user_gamestats_button_title))
@log_exception_callback
@ignore_message_not_modified
async def user_game_stats(client: BClient, callback_query: CallbackQuery):
    steam_url: Message = await ask_message_silently(client, callback_query,
                                                    client.locale.steam_url_example,
                                                    disable_web_page_preview=True)

    if steam_url.text == "/cancel":
        await steam_url.delete()
        return await profile_info(client, callback_query)

    await client.send_chat_action(callback_query.message.chat.id, ChatAction.TYPING)
    try:
        user_stats = UserGameStats.get(steam_url.text)
    except ParsingUserStatsError as e:
        if e.value == ParsingUserStatsError.INVALID_REQUEST:
            error_msg = client.locale.error_unknownrequest
        elif e.value == ParsingUserStatsError.PRIVATE_INFO:
            error_msg = '<a href="https://i.imgur.com/CAjblvT.mp4">‎</a>' + \
                        client.locale.user_gamestats_privateprofile_error
        else:
            raise e

        await callback_query.message.reply(error_msg)
        await callback_query.message.reply(client.locale.bot_choose_cmd,
                                           reply_markup=keyboards.markup_profile(client.locale))
        return await callback_query.message.delete()

    steamid, *stats = user_stats
    stats_page_title = client.locale.user_gamestats_page_title.format(steamid)
    stats_page_text = client.locale.user_gamestats_text.format(*stats)
    telegraph = Telegraph(access_token=config.TELEGRAPH_ACCESS_TOKEN)

    telegraph_response = telegraph.create_page(stats_page_title,
                                               html_content=stats_page_text,
                                               author_name="@incs2bot",
                                               author_url="https://t.me/incs2bot")

    share_btn = TranslatableIKB(client.locale.user_gamestats_share,
                                switch_inline_query=telegraph_response['url'])
    markup_share = TranslatableIKM([[share_btn]])

    await callback_query.message.reply(telegraph_response['url'], reply_markup=markup_share)
    await callback_query.message.reply(client.locale.bot_choose_cmd,
                                       reply_markup=keyboards.markup_profile(client.locale))
    await callback_query.message.delete()


# cat: Extra features


@bot.on_callback_query(ufilters.callback_data_equals(LK.bot_extras))
@came_from(main)
@ignore_message_not_modified
async def extra_features(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.bot_choose_cmd,
                                           reply_markup=keyboards.markup_extra(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.crosshair))
@came_from(extra_features)
@ignore_message_not_modified
async def crosshair(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.bot_choose_func,
                                           reply_markup=keyboards.markup_crosshair(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.crosshair_generate))
@came_from(extra_features)
@ignore_message_not_modified
async def generate_crosshair(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.error_wip,
                                           reply_markup=keyboards.markup_crosshair(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.crosshair_decode))
@log_exception_callback
async def decode_crosshair(client: BClient, callback_query: CallbackQuery):
    decode_input: Message = await ask_message_silently(client, callback_query, client.locale.crosshair_decode_example)

    if decode_input.text == "/cancel":
        await decode_input.delete()
        return await crosshair(client, callback_query)

    _crosshair = Crosshair.decode(decode_input.text)
    if _crosshair is None:
        return await decode_input.reply(client.locale.crosshair_decode_error)

    text = client.locale.crosshair_decode_result.format('; '.join(_crosshair.commands))

    await decode_input.reply(text)
    await callback_query.message.reply(client.locale.bot_choose_func,
                                       reply_markup=keyboards.markup_crosshair(client.locale))


@log_exception_callback
@bot.on_callback_query(ufilters.callback_data_equals(LK.exchangerate_button_title))
@ignore_message_not_modified
async def send_exchange_rate(client: BClient, callback_query: CallbackQuery):
    prices = ExchangeRate.cached_data()

    await callback_query.edit_message_text(client.locale.exchangerate_text.format(*prices.values()),
                                           reply_markup=keyboards.markup_extra(client.locale))


@log_exception_callback
@bot.on_callback_query(ufilters.callback_data_equals(LK.valve_hqtime_button_title))
@ignore_message_not_modified
async def send_valve_hq_time(client: BClient, callback_query: CallbackQuery):
    """Send the time in Valve headquarters (Bellevue, Washington, US)"""

    lang_code = callback_query.from_user.language_code

    valve_hq_datetime = dt.datetime.now(tz=VALVE_TIMEZONE)

    valve_hq_dt_formatted = f'{format_datetime(valve_hq_datetime, "HH:mm:ss, dd MMM", locale=lang_code).title()} ' \
                            f'({valve_hq_datetime:%Z})'

    text = client.locale.valve_hqtime_text.format(CLOCKS[valve_hq_datetime.hour % 12], valve_hq_dt_formatted)

    await callback_query.edit_message_text(text, reply_markup=keyboards.markup_extra(client.locale))


@log_exception_callback
@bot.on_callback_query(ufilters.callback_data_equals(LK.game_dropcap_button_title))
@ignore_message_not_modified
async def send_dropcap_timer(client: BClient, callback_query: CallbackQuery):
    """Send drop cap reset time"""

    text = client.locale.game_dropcaptimer_text.format(*drop_cap_reset_timer())

    await callback_query.edit_message_text(text, reply_markup=keyboards.markup_extra(client.locale))


@log_exception_callback
@bot.on_callback_query(ufilters.callback_data_equals(LK.game_version_button_title))
@ignore_message_not_modified
async def send_game_version(client: BClient, callback_query: CallbackQuery):
    """Send a current version of CS:GO/CS 2"""
    lang_code = callback_query.from_user.language_code

    data = GameVersionData.cached_data()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, callback_query)

    text = server_stats_handlers.get_game_version_summary(data, lang_code)

    await callback_query.edit_message_text(text, reply_markup=keyboards.markup_extra(client.locale),
                                           disable_web_page_preview=True)


# cat: Guns info


@bot.on_callback_query(ufilters.callback_data_equals(LK.gun_button_text))
@came_from(extra_features)
@ignore_message_not_modified
async def guns(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.gun_select_category,
                                           reply_markup=keyboards.markup_guns(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.gun_pistols))
@came_from(guns)
@ignore_message_not_modified
async def pistols(client: BClient, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = (await client.listen_callback(callback_query.message.chat.id,
                                                    callback_query.message.id)).data
    else:
        choosed_gun = (await ask_callback_silently(client,
                                                   callback_query,
                                                   client.locale.gun_select_pistol,
                                                   reply_markup=keyboards.markup_pistols(client.locale))).data

    if choosed_gun in GUNS_INFO:
        return await send_gun_info(client, callback_query, pistols, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.markup_pistols(client.locale))
    if choosed_gun == LK.bot_back:
        return await back(client, callback_query)
    return await unknown_request(client, callback_query, keyboards.markup_pistols(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.gun_heavy))
@came_from(guns)
@ignore_message_not_modified
async def heavy(client: BClient, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = (await client.listen_callback(callback_query.message.chat.id,
                                                    callback_query.message.id)).data
    else:
        choosed_gun = (await ask_callback_silently(client,
                                                   callback_query,
                                                   client.locale.gun_select_heavy,
                                                   reply_markup=keyboards.markup_heavy(client.locale))).data

    if choosed_gun in GUNS_INFO:
        return await send_gun_info(client, callback_query, heavy, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.markup_heavy(client.locale))
    if choosed_gun == LK.bot_back:
        return await back(client, callback_query)
    return await unknown_request(client, callback_query, keyboards.markup_heavy(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.gun_smgs))
@came_from(guns)
@ignore_message_not_modified
async def smgs(client: BClient, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = (await client.listen_callback(callback_query.message.chat.id,
                                                    callback_query.message.id)).data
    else:
        choosed_gun = (await ask_callback_silently(client,
                                                   callback_query,
                                                   client.locale.gun_select_smg,
                                                   reply_markup=keyboards.markup_smgs(client.locale))).data

    if choosed_gun in GUNS_INFO:
        return await send_gun_info(client, callback_query, smgs, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.markup_smgs(client.locale))
    if choosed_gun == LK.bot_back:
        return await back(client, callback_query)
    return await unknown_request(client, callback_query, keyboards.markup_smgs(client.locale))


@bot.on_callback_query(ufilters.callback_data_equals(LK.gun_rifles))
@came_from(guns)
@ignore_message_not_modified
async def rifles(client: BClient, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = (await client.listen_callback(callback_query.message.chat.id,
                                                    callback_query.message.id)).data
    else:
        choosed_gun = (await ask_callback_silently(client,
                                                   callback_query,
                                                   client.locale.gun_select_rifle,
                                                   reply_markup=keyboards.markup_rifles(client.locale))).data

    if choosed_gun in GUNS_INFO:
        return await send_gun_info(client, callback_query, rifles, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.markup_rifles(client.locale))
    if choosed_gun == LK.bot_back:
        return await back(client, callback_query)
    return await unknown_request(client, callback_query, keyboards.markup_rifles(client.locale))


@log_exception_callback
@ignore_message_not_modified
async def send_gun_info(client: BClient, callback_query: CallbackQuery, _from: callable,
                        gun_info: GunInfo, reply_markup: TranslatableIKM):
    """Send archived data about guns"""

    gun_info.origin = client.locale.get(gun_info.origin)
    gun_info = gun_info.as_dict()
    del gun_info['id'], gun_info['team']
    formatted_info = gun_info.values()

    text = client.locale.gun_summary_text.format(*formatted_info)

    await callback_query.edit_message_text(text, reply_markup=reply_markup)
    await _from(client, callback_query, loop=True)


# cat: Commands


@bot.on_message(filters.command("start"))
async def welcome(client: BClient, message: Message):
    """First bot's message"""

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, message)

    text = client.locale.bot_start_text.format(message.from_user.first_name)

    await message.reply(text)
    await message.reply(client.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(client.locale))


@bot.on_message(filters.command("feedback"))
async def leave_feedback(client: BClient, message: Message):
    """Send feedback"""

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, message)

    feedback: Message = await client.ask_message(message.chat.id,
                                                 client.locale.bot_feedback_text)

    if feedback.text == "/cancel":
        await feedback.delete()
        return await message.reply(client.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(client.locale))

    if not config.TEST_MODE:
        await client.send_message(config.AQ,
                                  f'🆔 <a href="tg://user?id={feedback.from_user.id}">{feedback.from_user.id}</a>:',
                                  disable_notification=True)
        await feedback.forward(config.AQ)

    await feedback.reply(client.locale.bot_feedback_success)
    await message.reply(client.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(client.locale))


@bot.on_message(filters.command("help"))
async def _help(client: BClient, message: Message):
    """/help message"""

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, message)

    await message.reply(client.locale.bot_help_text)
    await message.reply(client.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(client.locale))


@bot.on_message(filters.command("delkey"))
async def delete_keyboard(client: BClient, message: Message):
    await message.delete()
    msg = await message.reply("👍", quote=False, reply_markup=keyboards.markup_del)
    await asyncio.sleep(10)
    await msg.delete()


@bot.on_message(filters.command("sueta"))
async def blinky_eyes(client: BClient, message: Message):
    await message.delete()
    msg = await message.reply("👀", quote=False, reply_markup=keyboards.markup_del)
    await asyncio.sleep(10)
    await msg.delete()


# cat: Service


async def pm_only(client: BClient, message: Message):
    msg = await message.reply(client.locale.bot_pmonly_text)

    try:
        await asyncio.sleep(10)
        await message.delete()
    except MessageDeleteForbidden:
        pass
    finally:
        await msg.delete()


@ignore_message_not_modified
async def send_about_maintenance(client: BClient, callback_query: CallbackQuery):
    await callback_query.edit_message_text(client.locale.valve_steam_maintenance_text,
                                           reply_markup=keyboards.main_markup(client.locale))


@ignore_message_not_modified
async def something_went_wrong(client: BClient, callback_query: CallbackQuery):
    """If anything goes wrong"""

    await callback_query.edit_message_text(client.locale.error_internal,
                                           reply_markup=keyboards.main_markup(client.locale))


@ignore_message_not_modified
async def unknown_request(client: BClient, callback_query: CallbackQuery, reply_markup: TranslatableIKM = None):
    if reply_markup is None:
        reply_markup = keyboards.main_markup(client.locale)

    await callback_query.edit_message_text(client.locale.error_unknownrequest, reply_markup=reply_markup)


@bot.on_callback_query(ufilters.callback_data_equals(LK.bot_back))
@ignore_message_not_modified
async def back(client: BClient, callback_query: CallbackQuery):

    if client.came_from is None:
        return await main(client, callback_query)
    await client.came_from(client, callback_query)


if __name__ == '__main__':
    try:
        bot.run()
    except KeyboardInterrupt:
        logging.info('Shutting down the bot...')
        bot.stop()
