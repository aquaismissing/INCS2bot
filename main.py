import asyncio
from asyncio.exceptions import TimeoutError
import datetime as dt
import json
from typing import Callable
import logging
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from babel.dates import format_datetime
from csxhair import Crosshair
from pyrogram import filters, idle
from pyrogram.enums import ChatType, ChatAction, ParseMode
from pyrogram.errors import MessageDeleteForbidden, MessageNotModified
from pyrogram.types import CallbackQuery, Message
# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!
from telegraph.aio import Telegraph

import config
from db import db_session
from functions import datacenter_handlers, info_formatters
from functions.decorators import *
from functions.locale import get_available_languages
from functions.logs import *
import keyboards
from keyboards import ExtendedIKB, ExtendedIKM
# noinspection PyPep8Naming
from l10n import Locale, LocaleKeys as LK
from utypes import (BClient, ExchangeRate, GameServersData,
                    GameVersionData, GunInfo, LeaderboardStats,
                    ProfileInfo, State, States, UserGameStats,
                    UserSession, drop_cap_reset_timer)
from utypes.profiles import ErrorCode, ParseUserStatsError  # to clearly indicate relation


GUNS_INFO = GunInfo.load()
AVAILABLE_LANGUAGES = get_available_languages()
ALL_COMMANDS = ['start', 'help', 'feedback']

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(threadName)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

bot = BClient(config.BOT_NAME,
              api_id=config.API_ID,
              api_hash=config.API_HASH,
              bot_token=config.BOT_TOKEN,
              plugins={'root': 'plugins'},
              workdir=config.SESS_FOLDER)

telegraph = Telegraph(access_token=config.TELEGRAPH_ACCESS_TOKEN)


# cat: Main


def log_exception_callback(func):
    """Decorator to catch and log exceptions in bot functions. Also call `something_went_wrong(message)`."""

    async def inner(client: BClient, session: UserSession, callback_query: CallbackQuery, *args, **kwargs):
        # noinspection PyBroadException
        try:
            await func(client, session, callback_query, *args, **kwargs)
        except Exception:
            logging.exception('Caught exception!')
            await client.send_message(config.LOGCHANNEL, f'❗️ {traceback.format_exc()}',
                                      disable_notification=True, parse_mode=ParseMode.DISABLED)
            await something_went_wrong(client, session, callback_query)

    return inner


@bot.on_message(~filters.me)
async def sync_user_data(client: BClient, message: Message):
    if message.chat.type != ChatType.PRIVATE:
        message.continue_propagation()

    user = message.from_user
    if user.id not in client.sessions:
        await client.register_session(user, force_lang=config.FORCE_LANG)

    session = client.sessions[user.id]
    await log_message(client, session, message)

    message.continue_propagation()


@bot.on_message(filters.command(ALL_COMMANDS))
@ignore_blocking
async def any_command(client: BClient, message: Message):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    user = message.from_user

    if (message.chat.type != ChatType.PRIVATE
            and user.id not in client.sessions):
        await client.register_session(user, force_lang=config.FORCE_LANG)

    session = client.sessions[user.id]

    return await client.get_func_by_command(session, message)


@bot.on_callback_query()
async def sync_user_data_callback(client: BClient, callback_query: CallbackQuery):
    if callback_query.message.chat.id == config.LOGCHANNEL:
        user = callback_query.from_user

        if user.id not in client.sessions:
            await client.register_session(user, force_lang=config.FORCE_LANG)

        session = client.sessions[user.id]
        return await client.get_func_by_callback(session, callback_query)

    if callback_query.message.chat.type != ChatType.PRIVATE:
        return

    user = callback_query.from_user

    if user.id not in client.sessions:
        await client.register_session(user, force_lang=config.FORCE_LANG)

    session = client.sessions[user.id]
    await log_callback(client, session, callback_query)

    # Render selection indicator on selectable markups
    for markup in keyboards.all_selectable_markups:
        markup.select_button_by_key(callback_query.data)

    return await client.get_func_by_callback(session, callback_query)


@bot.on_callback_request('main')
@bot.on_callback_request('_', session_timeout=True)
@ignore_message_not_modified
async def main_menu(_, session: UserSession,
                    callback_query: CallbackQuery, session_timeout: bool = False):
    text = session.locale.bot_choose_cmd

    if session_timeout:
        text = session.locale.error_session_timeout + '\n\n' + text

    await callback_query.edit_message_text(text, reply_markup=keyboards.main_markup(session.locale))


# cat: Server stats


@bot.on_callback_request(LK.bot_servers_stats)
@bot.came_from(main_menu, 0)
@ignore_message_not_modified
async def server_stats(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.bot_choose_cmd,
                                           reply_markup=keyboards.ss_markup(session.locale))


@bot.on_callback_request(LK.game_status_button_title)
@log_exception_callback
@ignore_message_not_modified
async def send_server_status(client: BClient, session: UserSession, callback_query: CallbackQuery):
    """Send the status of Counter-Strike servers"""

    data = GameServersData.cached_server_status()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, session, callback_query)

    text = info_formatters.format_server_status(data, session.locale)

    await callback_query.edit_message_text(text, reply_markup=keyboards.ss_markup(session.locale))


@bot.on_callback_request(LK.stats_matchmaking_button_title)
@log_exception_callback
@ignore_message_not_modified
async def send_matchmaking_stats(client: BClient, session: UserSession, callback_query: CallbackQuery):
    """Send Counter-Strike matchamaking statistics"""

    data = GameServersData.cached_matchmaking_stats()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, callback_query)

    text = info_formatters.format_matchmaking_stats(data, session.locale)

    await callback_query.edit_message_text(text, reply_markup=keyboards.ss_markup(session.locale))


# cat: Datacenters


@bot.on_callback_request(LK.dc_status_title)
@bot.came_from(server_stats, 1)
@ignore_message_not_modified
async def datacenters(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_choose_region,
                                           reply_markup=keyboards.dc_markup(session.locale))


@bot.on_callback_request(LK.regions_africa)
@bot.came_from(server_stats)
async def send_dc_africa(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.africa, keyboards.dc_markup)


@bot.on_callback_request(LK.regions_australia)
@bot.came_from(server_stats)
async def send_dc_australia(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.australia, keyboards.dc_markup)


@bot.on_callback_request(LK.regions_europe)
@bot.came_from(datacenters)
@ignore_message_not_modified
async def dc_europe(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_specify_country,
                                           reply_markup=keyboards.dc_eu_markup(session.locale))


@bot.on_callback_request(LK.dc_austria)
@bot.came_from(datacenters)
async def send_dc_austria(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.austria, keyboards.dc_eu_markup)


@bot.on_callback_request(LK.dc_finland)
@bot.came_from(datacenters)
async def send_dc_finland(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.finland, keyboards.dc_eu_markup)


@bot.on_callback_request(LK.dc_germany)
@bot.came_from(datacenters)
async def send_dc_germany(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.germany, keyboards.dc_eu_markup)


@bot.on_callback_request(LK.dc_netherlands)
@bot.came_from(datacenters)
async def send_dc_netherlands(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.netherlands, keyboards.dc_eu_markup)


@bot.on_callback_request(LK.dc_poland)
@bot.came_from(datacenters)
async def send_dc_poland(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.poland, keyboards.dc_eu_markup)


@bot.on_callback_request(LK.dc_spain)
@bot.came_from(datacenters)
async def send_dc_spain(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.spain, keyboards.dc_eu_markup)


@bot.on_callback_request(LK.dc_sweden)
@bot.came_from(datacenters)
async def send_dc_sweden(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.sweden, keyboards.dc_eu_markup)


@bot.on_callback_request(LK.dc_us)
@bot.came_from(datacenters)
@ignore_message_not_modified
async def dc_us(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_specify_region,
                                           reply_markup=keyboards.dc_us_markup(session.locale))


@bot.on_callback_request(LK.dc_us_north)
@bot.came_from(datacenters)
async def send_dc_us_north(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.us_north, keyboards.dc_us_markup)


@bot.on_callback_request(LK.dc_us_south)
@bot.came_from(datacenters)
async def send_dc_us_south(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.us_south, keyboards.dc_us_markup)


@bot.on_callback_request(LK.regions_southamerica)
@bot.came_from(datacenters)
@ignore_message_not_modified
async def send_dc_south_america(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_specify_country,
                                           reply_markup=keyboards.dc_southamerica_markup(session.locale))


@bot.on_callback_request(LK.dc_argentina)
@bot.came_from(datacenters)
async def send_dc_argentina(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query,
                        datacenter_handlers.argentina, keyboards.dc_southamerica_markup)


@bot.on_callback_request(LK.dc_brazil)
@bot.came_from(datacenters)
async def send_dc_brazil(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.brazil, keyboards.dc_southamerica_markup)


@bot.on_callback_request(LK.dc_chile)
@bot.came_from(datacenters)
async def send_dc_chile(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.chile, keyboards.dc_southamerica_markup)


@bot.on_callback_request(LK.dc_peru)
@bot.came_from(datacenters)
async def send_dc_peru(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.peru, keyboards.dc_southamerica_markup)


@bot.on_callback_request(LK.regions_asia)
@bot.came_from(datacenters, 2)
@ignore_message_not_modified
async def dc_asia(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_specify_country,
                                           reply_markup=keyboards.dc_asia_markup(session.locale))


@bot.on_callback_request(LK.dc_india)
@bot.came_from(datacenters)
async def send_dc_india(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.india, keyboards.dc_asia_markup)


@bot.on_callback_request(LK.dc_japan)
@bot.came_from(datacenters)
async def send_dc_japan(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.japan, keyboards.dc_asia_markup)


@bot.on_callback_request(LK.regions_china)
@bot.came_from(datacenters)
async def send_dc_china(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.china, keyboards.dc_asia_markup)


@bot.on_callback_request(LK.dc_emirates)
@bot.came_from(datacenters)
async def send_dc_emirates(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.emirates, keyboards.dc_asia_markup)


@bot.on_callback_request(LK.dc_singapore)
@bot.came_from(datacenters)
async def send_dc_singapore(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.singapore, keyboards.dc_asia_markup)


@bot.on_callback_request(LK.dc_hongkong)
@bot.came_from(datacenters)
async def send_dc_hongkong(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.hongkong, keyboards.dc_asia_markup)


@bot.on_callback_request(LK.dc_southkorea)
@bot.came_from(datacenters)
async def send_dc_south_korea(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.south_korea, keyboards.dc_asia_markup)


@log_exception_callback
@ignore_message_not_modified
async def send_dc_state(client: BClient, session: UserSession, callback_query: CallbackQuery,
                        dc_state_func: Callable[[Locale], str | State], reply_markup: ExtendedIKM):

    state = dc_state_func(session.locale)

    if state == States.UNKNOWN:
        return await something_went_wrong(client, session, callback_query)

    await callback_query.edit_message_text(state, reply_markup=reply_markup(session.locale))


# cat: Profile info


@bot.on_callback_request(LK.bot_profile_info)
@bot.came_from(main_menu)
@ignore_message_not_modified
async def profile_info(client: BClient, session: UserSession, callback_query: CallbackQuery):
    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache_file = json.load(f)

    if cache_file['webapi'] != 'normal':
        return await send_about_maintenance(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_choose_cmd,
                                           reply_markup=keyboards.profile_markup(session.locale))


@bot.on_callback_request(LK.user_profileinfo_title)
@log_exception_callback
@bot.came_from(main_menu)
@ignore_blocking
async def user_profile_info(client: BClient, session: UserSession,
                            callback_query: CallbackQuery, last_error: str = None):
    text = session.locale.steam_url_example if last_error is None else last_error
    text += '\n\n' + session.locale.bot_use_cancel

    try:
        steam_url = await client.ask_message_silently(callback_query, text, timeout=300)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_message(client, session, steam_url)

    if steam_url.text == "/cancel":
        await steam_url.delete()
        return await profile_info(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_loading)
    await client.send_chat_action(callback_query.message.chat.id, ChatAction.TYPING)

    try:
        info = ProfileInfo.get(steam_url.text)
    except ParseUserStatsError as e:
        await steam_url.delete()
        error_msg = await user_info_handle_error(client, session, steam_url, e)
        return await user_profile_info(client, session, callback_query, last_error=error_msg)
    except Exception as e:
        await steam_url.delete()
        raise e

    lang_code = callback_query.from_user.language_code

    if info.vanity_url is None:
        info.vanity_url = session.locale.user_profileinfo_notset

    if info.account_created:
        info.account_created = dt.datetime.fromtimestamp(info.account_created)
        info.account_created = f'{format_datetime(info.account_created, "dd MMM yyyy", locale=lang_code).title()}'
    else:
        info.account_created = session.locale.states_unknown

    info.faceit_ban = session.locale.user_profileinfo_banned \
        if info.faceit_ban else session.locale.user_profileinfo_none

    if info.faceit_lvl is None:
        info.faceit_lvl = session.locale.user_profileinfo_none
        info.faceit_elo = session.locale.user_profileinfo_none

    if info.faceit_url is None:
        info.faceit_url = session.locale.user_profileinfo_notfound

    if info.vac_bans == 0:
        info.vac_bans = session.locale.user_profileinfo_none

    if info.game_bans == 0:
        info.game_bans = session.locale.user_profileinfo_none

    info.community_ban = session.locale.user_profileinfo_banned \
        if info.community_ban else session.locale.user_profileinfo_none

    info.trade_ban = session.locale.user_profileinfo_banned \
        if info.trade_ban else session.locale.user_profileinfo_none

    text = session.locale.user_profileinfo_text.format(*info.to_tuple())

    await callback_query.message.reply(text, disable_web_page_preview=True)
    await callback_query.message.reply(session.locale.bot_choose_cmd,
                                       reply_markup=keyboards.profile_markup(session.locale))


@bot.on_callback_request(LK.user_gamestats_button_title)
@log_exception_callback
@bot.came_from(main_menu)
@ignore_blocking
@ignore_message_not_modified
async def user_game_stats(client: BClient, session: UserSession, callback_query: CallbackQuery, last_error: str = None):
    text = session.locale.steam_url_example if last_error is None else last_error
    text += '\n\n' + session.locale.bot_use_cancel

    try:
        steam_url = await client.ask_message_silently(callback_query, text, timeout=300)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_message(client, session, steam_url)

    if steam_url.text == '/cancel':
        await steam_url.delete()
        return await profile_info(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_loading)
    await client.send_chat_action(callback_query.message.chat.id, ChatAction.TYPING)

    try:
        user_stats = UserGameStats.get(steam_url.text)
    except ParseUserStatsError as e:
        await steam_url.delete()
        error_msg = await user_info_handle_error(client, session, steam_url, e)
        return await user_game_stats(client, session, callback_query, last_error=error_msg)
    except Exception as e:
        await steam_url.delete()
        raise e

    steamid, *stats = user_stats
    stats_page_title = session.locale.user_gamestats_page_title.format(steamid)
    stats_page_text = info_formatters.format_user_game_stats(stats, session.locale)

    try:
        telegraph_response = await telegraph.create_page(stats_page_title,
                                                         html_content=stats_page_text,
                                                         author_name="@INCS2bot",
                                                         author_url="https://t.me/INCS2bot")
    except json.JSONDecodeError:
        await steam_url.delete()
        return await user_game_stats(client, session, callback_query, last_error=session.locale.user_telegraph_error)

    share_btn = ExtendedIKB(session.locale.user_gamestats_share,
                            switch_inline_query=telegraph_response['url'])
    markup_share = ExtendedIKM([[share_btn]])

    await callback_query.message.reply(telegraph_response['url'], reply_markup=markup_share)
    await callback_query.message.reply(session.locale.bot_choose_cmd,
                                       reply_markup=keyboards.profile_markup(session.locale))


async def user_info_handle_error(_, session: UserSession, user_input: Message, exc: ParseUserStatsError):
    if exc.is_unknown:
        await user_input.delete()
        raise exc

    error_msg = session.locale.user_invalidrequest_error
    if exc.code == ErrorCode.INVALID_LINK:
        error_msg = session.locale.user_invalidlink_error
    elif exc.code == ErrorCode.PROFILE_IS_PRIVATE:
        error_msg = '<a href="https://i.imgur.com/CAjblvT.mp4">‎</a>' + \
                    session.locale.user_privateprofile_error

    return error_msg


# cat: Extra features


@bot.on_callback_request(LK.bot_extras)
@bot.came_from(main_menu)
@ignore_message_not_modified
async def extra_features(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.bot_choose_cmd,
                                           reply_markup=keyboards.extra_markup(session.locale))


@bot.on_callback_request(LK.crosshair)
@bot.came_from(extra_features, 3)
@ignore_message_not_modified
async def crosshair(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.bot_choose_func,
                                           reply_markup=keyboards.crosshair_markup(session.locale))


@bot.on_callback_request(LK.crosshair_generate)
@bot.came_from(extra_features)
@ignore_message_not_modified
async def generate_crosshair(_, session: UserSession, callback_query: CallbackQuery):  # todo: finally make this shit
    await callback_query.edit_message_text(session.locale.error_wip,
                                           reply_markup=keyboards.crosshair_markup(session.locale))


@bot.on_callback_request(LK.crosshair_decode)
@log_exception_callback
@bot.came_from(extra_features)
@ignore_message_not_modified
async def decode_crosshair(client: BClient, session: UserSession,
                           callback_query: CallbackQuery, last_error: str = None):
    text = session.locale.crosshair_decode_example if last_error is None else last_error
    text += '\n\n' + session.locale.bot_use_cancel

    try:
        decode_input = await client.ask_message_silently(callback_query, text)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_message(client, session, decode_input)

    if decode_input.text == '/cancel':
        await decode_input.delete()
        return await crosshair(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_loading)

    try:
        _crosshair = Crosshair.decode(decode_input.text)
    except ValueError:
        await decode_input.delete()
        return await decode_crosshair(client, session, callback_query, last_error=session.locale.crosshair_decode_error)

    text = session.locale.crosshair_decode_result.format('; '.join(_crosshair.cs2_commands))

    await decode_input.reply(text)
    await callback_query.message.reply(session.locale.bot_choose_func,
                                       reply_markup=keyboards.crosshair_markup(session.locale))


@bot.on_callback_request(LK.exchangerate_button_title)
@log_exception_callback
@bot.came_from(main_menu)
@ignore_message_not_modified
async def send_exchange_rate(_, session: UserSession, callback_query: CallbackQuery):
    prices = ExchangeRate.cached_data()

    await callback_query.edit_message_text(session.locale.exchangerate_text.format(*prices.values()),
                                           reply_markup=keyboards.extra_markup(session.locale))


@bot.on_callback_request(LK.valve_hqtime_button_title)
@log_exception_callback
@ignore_message_not_modified
async def send_valve_hq_time(_, session: UserSession, callback_query: CallbackQuery):
    """Send the time in Valve headquarters (Bellevue, Washington, US)"""

    text = info_formatters.format_valve_hq_time(session.locale)

    await callback_query.edit_message_text(text, reply_markup=keyboards.extra_markup(session.locale))


@bot.on_callback_request(LK.game_dropcap_button_title)
@log_exception_callback
@ignore_message_not_modified
async def send_dropcap_timer(_, session: UserSession, callback_query: CallbackQuery):
    """Send drop cap reset time"""

    text = session.locale.game_dropcaptimer_text.format(*drop_cap_reset_timer())

    await callback_query.edit_message_text(text, reply_markup=keyboards.extra_markup(session.locale))


@bot.on_callback_request(LK.game_version_button_title)
@log_exception_callback
@ignore_message_not_modified
async def send_game_version(client: BClient, session: UserSession, callback_query: CallbackQuery):
    """Send a current version of CS:GO/CS 2"""

    data = GameVersionData.cached_data()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, session, callback_query)

    text = info_formatters.format_game_version_info(data, session.locale)

    await callback_query.edit_message_text(text, reply_markup=keyboards.extra_markup(session.locale),
                                           disable_web_page_preview=True)


@bot.on_callback_request(LK.game_leaderboard_button_title)
@log_exception_callback
@bot.came_from(extra_features)
@ignore_message_not_modified
async def send_game_leaderboard(client: BClient, session: UserSession, callback_query: CallbackQuery,
                                region: str = LK.game_leaderboard_world):
    """Sends the CS2 leaderboard (top-10), supports both world and regional"""

    keyboards.leaderboard_markup.select_button_by_key(region)

    await callback_query.edit_message_text(session.locale.bot_loading,
                                           reply_markup=keyboards.leaderboard_markup(session.locale))

    region = region.split('_')[-1]
    if region == 'world':
        data = LeaderboardStats.cached_world_stats()
        text = info_formatters.format_game_world_leaderboard(data, session.locale)
    else:
        data = LeaderboardStats.cached_regional_stats(region)
        text = info_formatters.format_game_regional_leaderboard(region, data, session.locale)

    await callback_query.edit_message_text(text, reply_markup=keyboards.leaderboard_markup(session.locale))

    try:
        chosen_region = await client.listen_callback(callback_query.message.chat.id,
                                                     callback_query.message.id, timeout=300)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_callback(client, session, chosen_region)

    chosen_region = chosen_region.data

    if chosen_region == LK.bot_back:
        return await back(client, session, callback_query)
    await send_game_leaderboard(client, session, callback_query, chosen_region)

# cat: Guns info


@bot.on_callback_request(LK.gun_button_text)
@bot.came_from(extra_features)
async def guns(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.gun_select_category,
                                           reply_markup=keyboards.guns_markup(session.locale))


@bot.on_callback_request(LK.gun_pistols)
@bot.came_from(guns, 4)
async def pistols(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    try:
        if loop:
            chosen_gun = await client.listen_callback(callback_query.message.chat.id,
                                                      callback_query.message.id, timeout=300)
        else:
            chosen_gun = await client.ask_callback_silently(callback_query,
                                                            session.locale.gun_select_pistol,
                                                            reply_markup=keyboards.pistols_markup(session.locale),
                                                            timeout=300)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_callback(client, session, chosen_gun)

    chosen_gun = chosen_gun.data

    if chosen_gun in GUNS_INFO:
        keyboards.pistols_markup.select_button_by_key(chosen_gun)
        return await send_gun_info(client, session, callback_query, pistols, GUNS_INFO[chosen_gun],
                                   reply_markup=keyboards.pistols_markup)
    if chosen_gun == LK.bot_back:
        return await back(client, session, callback_query)
    return await unknown_request(client, session, callback_query, keyboards.pistols_markup)


@bot.on_callback_request(LK.gun_heavy)
@bot.came_from(guns)
async def heavy(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    try:
        if loop:
            chosen_gun = await client.listen_callback(callback_query.message.chat.id,
                                                      callback_query.message.id, timeout=300)
        else:
            chosen_gun = await client.ask_callback_silently(callback_query,
                                                            session.locale.gun_select_heavy,
                                                            reply_markup=keyboards.heavy_markup(session.locale),
                                                            timeout=300)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_callback(client, session, chosen_gun)

    chosen_gun = chosen_gun.data

    if chosen_gun in GUNS_INFO:
        keyboards.heavy_markup.select_button_by_key(chosen_gun)
        return await send_gun_info(client, session, callback_query, heavy, GUNS_INFO[chosen_gun],
                                   reply_markup=keyboards.heavy_markup)
    if chosen_gun == LK.bot_back:
        return await back(client, session, callback_query)
    return await unknown_request(client, session, callback_query, keyboards.heavy_markup)


@bot.on_callback_request(LK.gun_smgs)
@bot.came_from(guns)
async def smgs(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    try:
        if loop:
            chosen_gun = await client.listen_callback(callback_query.message.chat.id,
                                                      callback_query.message.id, timeout=300)
        else:
            chosen_gun = await client.ask_callback_silently(callback_query,
                                                            session.locale.gun_select_smg,
                                                            reply_markup=keyboards.smgs_markup(session.locale),
                                                            timeout=300)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_callback(client, session, chosen_gun)

    chosen_gun = chosen_gun.data
    if chosen_gun in GUNS_INFO:
        keyboards.smgs_markup.select_button_by_key(chosen_gun)
        return await send_gun_info(client, session, callback_query, smgs, GUNS_INFO[chosen_gun],
                                   reply_markup=keyboards.smgs_markup)
    if chosen_gun == LK.bot_back:
        return await back(client, session, callback_query)
    return await unknown_request(client, session, callback_query, keyboards.smgs_markup)


@bot.on_callback_request(LK.gun_rifles)
@bot.came_from(guns)
async def rifles(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    try:
        if loop:
            chosen_gun = await client.listen_callback(callback_query.message.chat.id,
                                                      callback_query.message.id, timeout=300)
        else:
            chosen_gun = await client.ask_callback_silently(callback_query,
                                                            session.locale.gun_select_rifle,
                                                            reply_markup=keyboards.rifles_markup(session.locale),
                                                            timeout=300)
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_callback(client, session, chosen_gun)

    chosen_gun = chosen_gun.data
    if chosen_gun in GUNS_INFO:
        keyboards.rifles_markup.select_button_by_key(chosen_gun)
        return await send_gun_info(client, session, callback_query, rifles, GUNS_INFO[chosen_gun],
                                   reply_markup=keyboards.rifles_markup)
    if chosen_gun == LK.bot_back:
        return await back(client, session, callback_query)
    return await unknown_request(client, session, callback_query, keyboards.rifles_markup)


@log_exception_callback
async def send_gun_info(client: BClient, session: UserSession, callback_query: CallbackQuery, _from: callable,
                        gun_info: GunInfo, reply_markup: ExtendedIKM):
    """Send archived data about guns"""

    gun_info_dict = gun_info.as_dict()
    gun_info_dict['origin'] = session.locale.get(gun_info.origin)
    del gun_info_dict['id'], gun_info_dict['team']

    text = session.locale.gun_summary_text.format(*gun_info_dict.values())

    try:
        await callback_query.edit_message_text(text, reply_markup=reply_markup(session.locale))
    except MessageNotModified:
        pass
    finally:
        return await _from(client, session, callback_query, loop=True)


# cat: Settings


@bot.on_callback_request(LK.bot_settings)
@bot.came_from(main_menu)
@ignore_message_not_modified
async def settings(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.bot_choose_setting,
                                           reply_markup=keyboards.settings_markup(session.locale))


@bot.on_callback_request(LK.settings_language_button_title)
@bot.came_from(settings, 5)
@ignore_message_not_modified
async def language(client: BClient, session: UserSession, callback_query: CallbackQuery):
    keyboards.language_settings_markup.select_button_by_key(session.locale.lang_code)

    try:
        chosen_lang = await client.ask_callback_silently(
            callback_query,
            session.locale.settings_language_choose.format(AVAILABLE_LANGUAGES.get(session.locale.lang_code)),
            reply_markup=keyboards.language_settings_markup(session.locale),
            timeout=300
        )
    except TimeoutError:
        return await main_menu(client, session, callback_query, session_timeout=True)

    await log_callback(client, session, chosen_lang)

    chosen_lang = chosen_lang.data
    if chosen_lang == LK.bot_back:
        return await back(client, session, callback_query)
    session.update_lang(chosen_lang)
    return await language(client, session, callback_query)


# cat: Commands


@bot.on_command('start')
async def welcome(client: BClient, session: UserSession, message: Message):
    """First bot's message"""

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, session, message)

    text = session.locale.bot_start_text.format(message.from_user.first_name)

    await message.reply(text)
    await message.reply(session.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(session.locale))


@bot.on_command('feedback')
async def leave_feedback(client: BClient, session: UserSession, message: Message):
    """Send feedback"""

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, session, message)

    text = session.locale.bot_feedback_text + '\n\n' + session.locale.bot_use_cancel

    try:
        feedback = await client.ask_message(message.chat.id, text)
    except TimeoutError:
        return await client.send_message(message.chat.id, 'Timed out.')  # todo: добавить строку локализации

    if feedback.text == '/cancel':
        await feedback.delete()
        return await message.reply(session.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(session.locale))

    if not config.TEST_MODE:
        await client.send_message(config.AQ,
                                  f'🆔 [{feedback.from_user.id}](tg://user?id={feedback.from_user.id}):',
                                  disable_notification=True)
        await feedback.forward(config.AQ)

    await feedback.reply(session.locale.bot_feedback_success)
    await message.reply(session.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(session.locale))


@bot.on_command('help')
async def _help(client: BClient, session: UserSession, message: Message):
    """/help message"""

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, session, message)

    await message.reply(session.locale.bot_help_text)
    await message.reply(session.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(session.locale))


# cat: Service


async def pm_only(_, session: UserSession, message: Message):
    msg = await message.reply(session.locale.bot_pmonly_text)

    try:
        await asyncio.sleep(10)
        await message.delete()
    except MessageDeleteForbidden:
        pass
    finally:
        await msg.delete()


@ignore_message_not_modified
async def send_about_maintenance(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.valve_steam_maintenance_text,
                                           reply_markup=keyboards.main_markup(session.locale))


@ignore_message_not_modified
async def something_went_wrong(_, session: UserSession, callback_query: CallbackQuery):
    """If anything goes wrong"""

    await callback_query.edit_message_text(session.locale.error_internal,
                                           reply_markup=keyboards.main_markup(session.locale))


@ignore_message_not_modified
async def unknown_request(_, session: UserSession, callback_query: CallbackQuery,
                          reply_markup: ExtendedIKM = keyboards.main_markup):
    await callback_query.edit_message_text(session.locale.error_unknownrequest,
                                           reply_markup=reply_markup(session.locale))


@bot.on_callback_request(LK.bot_back)
async def back(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await client.go_back(session, callback_query)


# only for logging channel
@bot.on_callback_request('log_ping')
async def log_ping(_, __, callback_query: CallbackQuery):
    await callback_query.answer('Yes, I AM working!')


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(bot.clear_timeout_sessions, 'interval', minutes=30)
    scheduler.add_job(log, 'interval', hours=8,
                      args=(bot, "Report: I\'m still active!"),
                      kwargs={'reply_markup': keyboards.log_ping_markup})

    scheduler.start()

    try:
        await db_session.init(config.USER_DB_FILE_PATH)
        await bot.start()
        await log(bot, 'Bot started.')
        await idle()
    except Exception as e:
        logging.exception('The bot got terminated because of exception!')
        await log(bot, f'Bot got terminated because of exception!\n'
                       f'\n'
                       f'❗️ {e.__class__.__name__}: {e}', disable_notification=False)
    finally:
        logging.info('Shutting down the bot...')
        await log(bot, 'Bot is shutting down...')
        await bot.dump_sessions()
        await bot.stop(block=False)


if __name__ == '__main__':
    bot.run(main())
