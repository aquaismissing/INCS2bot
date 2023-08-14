import asyncio
import datetime as dt
import json
from json import JSONDecodeError
from typing import Callable
import logging
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from babel.dates import format_datetime
import pandas as pd
from pyrogram import filters, idle
from pyrogram.enums import ChatType, ChatAction, ParseMode
from pyrogram.errors import MessageDeleteForbidden, MessageNotModified
from pyrogram.types import CallbackQuery, Message
# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!
from telegraph.aio import Telegraph

import config
from functions import datacenter_handlers, server_stats_handlers # , ufilters
from functions.decorators import *
from functions.logs import *
import keyboards
from keyboards import ExtendedIKB, ExtendedIKM
from l10n import LocaleKeys as LK
from utypes import (BClient, Crosshair, ExchangeRate, GameServersData,
                    GameVersionData, GunInfo, ParsingUserStatsError, ProfileInfo,
                    State, States, UserGameStats, UserSession, drop_cap_reset_timer)

GUNS_INFO = GunInfo.load()

ALL_COMMANDS = ['start', 'help', 'feedback']

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(threadName)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

bot = BClient(config.BOT_NAME,
              api_id=config.API_ID,
              api_hash=config.API_HASH,
              bot_token=config.BOT_TOKEN,
              plugins={'root': 'plugins'})
telegraph = Telegraph(access_token=config.TELEGRAPH_ACCESS_TOKEN)

user_data = pd.read_csv(config.USER_DB_FILE_PATH)

# cat: Main


def log_exception_callback(func):
    """Decorator to catch and log exceptions in bot functions. Also call `something_went_wrong(message)`."""

    async def inner(client: BClient, session: UserSession, callback_query: CallbackQuery, *args, **kwargs):
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
    await log_message(client, message)

    if user.id not in client.sessions:
        if not user_data["UserID"].isin([user.id]).any():
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
            pd.concat([user_data, new_data]).to_csv(config.USER_DB_FILE_PATH, index=False)

        client.register_session(user, force_lang=config.FORCE_LANG)

    message.continue_propagation()


@bot.on_message(filters.command(ALL_COMMANDS))
@ignore_blocking
async def any_command(client: BClient, message: Message):
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    if message.chat.type != ChatType.PRIVATE:
        user = message.from_user

        if user.id not in client.sessions:
            client.register_session(user, force_lang=config.FORCE_LANG)

    message.continue_propagation()


@bot.on_callback_query()
async def sync_user_data_callback(client: BClient, callback_query: CallbackQuery):
    if callback_query.message.chat.type != ChatType.PRIVATE:
        return

    user = callback_query.from_user
    await log_callback(client, callback_query)

    if user.id not in client.sessions:
        if not user_data["UserID"].isin([user.id]).any():
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
            pd.concat([user_data, new_data]).to_csv(config.USER_DB_FILE_PATH, index=False)

        client.register_session(user, force_lang=config.FORCE_LANG)

    # Render selection indicator on selectable markups
    key = callback_query.data

    for markup in keyboards.all_selectable_markups:
        markup.select_button_by_key(key)

    session = client.sessions[user.id]

    match key:
        case 'main':
            return await main_menu(client, session, callback_query)
        case LK.bot_back:
            return await back(client, session, callback_query)

        case LK.bot_servers_stats:
            return await server_stats(client, session, callback_query)
        case LK.game_status_button_title:
            return await send_server_status(client, session, callback_query)
        case LK.stats_matchmaking_button_title:
            return await send_matchmaking_stats(client, session, callback_query)
        case LK.dc_status_title:
            return await datacenters(client, session, callback_query)

        case LK.dc_asia:
            return await dc_asia(client, session, callback_query)
        case LK.dc_europe:
            return await dc_europe(client, session, callback_query)
        case LK.dc_us:
            return await dc_us(client, session, callback_query)
        case LK.dc_africa:
            return await send_dc_africa(client, session, callback_query)
        case LK.dc_australia:
            return await send_dc_australia(client, session, callback_query)
        case LK.dc_eu_north:
            return await send_dc_eu_north(client, session, callback_query)
        case LK.dc_eu_east:
            return await send_dc_eu_east(client, session, callback_query)
        case LK.dc_eu_west:
            return await send_dc_eu_west(client, session, callback_query)
        case LK.dc_us_north:
            return await send_dc_us_north(client, session, callback_query)
        case LK.dc_us_south:
            return await send_dc_us_south(client, session, callback_query)
        case LK.dc_southamerica:
            return await send_dc_south_america(client, session, callback_query)
        case LK.dc_india:
            return await send_dc_india(client, session, callback_query)
        case LK.dc_japan:
            return await send_dc_japan(client, session, callback_query)
        case LK.dc_china:
            return await send_dc_china(client, session, callback_query)
        case LK.dc_emirates:
            return await send_dc_emirates(client, session, callback_query)
        case LK.dc_singapore:
            return await send_dc_singapore(client, session, callback_query)
        case LK.dc_hongkong:
            return await send_dc_hongkong(client, session, callback_query)
        case LK.dc_southkorea:
            return await send_dc_south_korea(client, session, callback_query)

        case LK.bot_profile_info:
            return await profile_info(client, session, callback_query)
        case LK.user_profileinfo_title:
            return await user_profile_info(client, session, callback_query)
        case LK.user_gamestats_button_title:
            return await user_game_stats(client, session, callback_query)

        case LK.bot_extras:
            return await extra_features(client, session, callback_query)

        case LK.crosshair:
            return await crosshair(client, session, callback_query)
        case LK.crosshair_generate:
            return await generate_crosshair(client, session, callback_query)
        case LK.crosshair_decode:
            return await decode_crosshair(client, session, callback_query)

        case LK.valve_hqtime_button_title:
            return await send_valve_hq_time(client, session, callback_query)
        case LK.exchangerate_button_title:
            return await send_exchange_rate(client, session, callback_query)
        case LK.game_dropcap_button_title:
            return await send_dropcap_timer(client, session, callback_query)
        case LK.game_version_button_title:
            return await send_game_version(client, session, callback_query)

        case LK.gun_button_text:
            return await guns(client, session, callback_query)
        case LK.gun_pistols:
            return await pistols(client, session, callback_query)
        case LK.gun_heavy:
            return await heavy(client, session, callback_query)
        case LK.gun_smgs:
            return await smgs(client, session, callback_query)
        case LK.gun_rifles:
            return await rifles(client, session, callback_query)

        case _:  # Nothing found, just return session timeout message
            return await main_menu(client, session, callback_query, session_timeout=True)


@ignore_message_not_modified
async def main_menu(_, session: UserSession,
                    callback_query: CallbackQuery, session_timeout: bool = False):
    text = session.locale.bot_choose_cmd

    if session_timeout:
        text = session.locale.error_session_timeout + '\n\n' + text

    await callback_query.edit_message_text(text, reply_markup=keyboards.main_markup(session.locale))


# cat: Server stats


@came_from(main_menu)
@ignore_message_not_modified
async def server_stats(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.bot_choose_cmd,
                                           reply_markup=keyboards.ss_markup(session.locale))


@log_exception_callback
@ignore_message_not_modified
async def send_server_status(client: BClient, session: UserSession, callback_query: CallbackQuery):
    """Send the status of Counter-Strike servers"""

    data = GameServersData.cached_server_status()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, session, callback_query)

    text = server_stats_handlers.get_server_status_summary(data, session.lang_code)

    await callback_query.edit_message_text(text, reply_markup=keyboards.ss_markup(session.locale))


@log_exception_callback
@ignore_message_not_modified
async def send_matchmaking_stats(client: BClient, session: UserSession, callback_query: CallbackQuery):
    """Send Counter-Strike matchamaking statistics"""

    data = GameServersData.cached_matchmaking_stats()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, callback_query)

    text = server_stats_handlers.get_matchmaking_stats_summary(data, session.lang_code)

    await callback_query.edit_message_text(text, reply_markup=keyboards.ss_markup(session.locale))


# cat: Datacenters


@came_from(server_stats)
@ignore_message_not_modified
async def datacenters(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_choose_region,
                                           reply_markup=keyboards.dc_markup(session.locale))


@came_from(datacenters)
@ignore_message_not_modified
async def dc_asia(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_specify_country,
                                           reply_markup=keyboards.dc_asia_markup(session.locale))


@came_from(datacenters)
@ignore_message_not_modified
async def dc_europe(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_specify_region,
                                           reply_markup=keyboards.dc_eu_markup(session.locale))


@came_from(datacenters)
@ignore_message_not_modified
async def dc_us(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.dc_status_specify_region,
                                           reply_markup=keyboards.dc_us_markup(session.locale))


@came_from(server_stats)
async def send_dc_africa(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.africa, keyboards.dc_markup)


@came_from(server_stats)
async def send_dc_australia(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, session, callback_query, datacenter_handlers.australia, keyboards.dc_markup)


@came_from(datacenters)
async def send_dc_eu_north(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.eu_north, keyboards.dc_eu_markup)


@came_from(datacenters)
async def send_dc_eu_west(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.eu_west, keyboards.dc_eu_markup)


@came_from(datacenters)
async def send_dc_eu_east(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.eu_east, keyboards.dc_eu_markup)


@came_from(datacenters)
async def send_dc_us_north(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.us_north, keyboards.dc_us_markup)


@came_from(datacenters)
async def send_dc_us_south(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.us_south, keyboards.dc_us_markup)


@came_from(server_stats)
async def send_dc_south_america(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.south_america, keyboards.dc_markup)


@came_from(datacenters)
async def send_dc_india(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.india, keyboards.dc_asia_markup)


@came_from(datacenters)
async def send_dc_japan(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.japan, keyboards.dc_asia_markup)


@came_from(datacenters)
async def send_dc_china(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.china, keyboards.dc_asia_markup)


@came_from(datacenters)
async def send_dc_emirates(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.emirates, keyboards.dc_asia_markup)


@came_from(datacenters)
async def send_dc_singapore(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.singapore, keyboards.dc_asia_markup)


@came_from(datacenters)
async def send_dc_hongkong(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.hongkong, keyboards.dc_asia_markup)


@came_from(datacenters)
async def send_dc_south_korea(client: BClient, session: UserSession, callback_query: CallbackQuery):
    await send_dc_state(client, session, callback_query, datacenter_handlers.south_korea, keyboards.dc_asia_markup)


@ignore_message_not_modified
async def send_dc_state(client: BClient, session: UserSession, callback_query: CallbackQuery,
                        dc_state_func: Callable[[str], str | State], reply_markup: ExtendedIKM):

    state = dc_state_func(session.lang_code)

    if state == States.UNKNOWN:
        return await something_went_wrong(client, session, callback_query)

    await callback_query.edit_message_text(state, reply_markup=reply_markup(session.locale))


# cat: Profile info


@came_from(main_menu)
@ignore_message_not_modified
async def profile_info(client: BClient, session: UserSession, callback_query: CallbackQuery):
    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache_file = json.load(f)

    if cache_file['webapi'] != 'normal':
        return await send_about_maintenance(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_choose_cmd,
                                           reply_markup=keyboards.profile_markup(session.locale))


@log_exception_callback
@came_from(main_menu)
@ignore_blocking
async def user_profile_info(client: BClient, session: UserSession,
                            callback_query: CallbackQuery, last_error: str = None):
    text = session.locale.steam_url_example if last_error is None else last_error
    text += '\n\n' + session.locale.bot_use_cancel

    steam_url = await client.ask_message_silently(callback_query, text)

    await log_message(client, steam_url)

    if steam_url.text == "/cancel":
        await steam_url.delete()
        return await profile_info(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_loading)
    await client.send_chat_action(callback_query.message.chat.id, ChatAction.TYPING)

    try:
        info = ProfileInfo.get(steam_url.text)
    except ParsingUserStatsError as e:
        await steam_url.delete()
        error_msg = await user_info_handle_error(client, session, steam_url, e)
        return await user_game_stats(client, session, callback_query, last_error=error_msg)
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


@log_exception_callback
@came_from(main_menu)
@ignore_blocking
@ignore_message_not_modified
async def user_game_stats(client: BClient, session: UserSession, callback_query: CallbackQuery, last_error: str = None):
    text = session.locale.steam_url_example if last_error is None else last_error
    text += '\n\n' + session.locale.bot_use_cancel

    steam_url = await client.ask_message_silently(callback_query, text)

    await log_message(client, steam_url)

    if steam_url.text == "/cancel":
        await steam_url.delete()
        return await profile_info(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_loading)
    await client.send_chat_action(callback_query.message.chat.id, ChatAction.TYPING)

    try:
        user_stats = UserGameStats.get(steam_url.text)
    except ParsingUserStatsError as e:
        await steam_url.delete()
        error_msg = await user_info_handle_error(client, session, steam_url, e)
        return await user_game_stats(client, session, callback_query, last_error=error_msg)
    except Exception as e:
        await steam_url.delete()
        raise e

    steamid, *stats = user_stats
    stats_page_title = session.locale.user_gamestats_page_title.format(steamid)
    stats_page_text = session.locale.user_gamestats_text.format(*stats)

    try:
        telegraph_response = await telegraph.create_page(stats_page_title,
                                                         html_content=stats_page_text,
                                                         author_name="@INCS2bot",
                                                         author_url="https://t.me/INCS2bot")
    except JSONDecodeError:  # Telegraph is a piece of garbage
        await steam_url.delete()
        return await user_game_stats(client, session, callback_query, last_error=session.locale.user_telegraph_error)

    share_btn = ExtendedIKB(session.locale.user_gamestats_share,
                            switch_inline_query=telegraph_response['url'])
    markup_share = ExtendedIKM([[share_btn]])

    await callback_query.message.reply(telegraph_response['url'], reply_markup=markup_share)
    await callback_query.message.reply(session.locale.bot_choose_cmd,
                                       reply_markup=keyboards.profile_markup(session.locale))


async def user_info_handle_error(_, session: UserSession, user_input: Message, exc: ParsingUserStatsError):
    if exc.is_unknown:
        await user_input.delete()
        raise exc

    error_msg = session.locale.user_invalidrequest_error
    if exc.value == ParsingUserStatsError.INVALID_LINK:
        error_msg = session.locale.user_invalidlink_error
    elif exc.value == ParsingUserStatsError.PROFILE_IS_PRIVATE:
        error_msg = '<a href="https://i.imgur.com/CAjblvT.mp4">‎</a>' + \
                    session.locale.user_privateprofile_error

    return error_msg


# cat: Extra features


@came_from(main_menu)
@ignore_message_not_modified
async def extra_features(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.bot_choose_cmd,
                                           reply_markup=keyboards.extra_markup(session.locale))


@came_from(extra_features)
@ignore_message_not_modified
async def crosshair(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.bot_choose_func,
                                           reply_markup=keyboards.crosshair_markup(session.locale))


@came_from(extra_features)
@ignore_message_not_modified
async def generate_crosshair(_, session: UserSession, callback_query: CallbackQuery):  # todo: finally make this shit
    await callback_query.edit_message_text(session.locale.error_wip,
                                           reply_markup=keyboards.crosshair_markup(session.locale))


@log_exception_callback
@came_from(extra_features)
@ignore_message_not_modified
async def decode_crosshair(client: BClient, session: UserSession,
                           callback_query: CallbackQuery, last_error: str = None):
    text = session.locale.crosshair_decode_example if last_error is None else last_error
    text += '\n\n' + session.locale.bot_use_cancel

    decode_input = await client.ask_message_silently(callback_query, text)

    await log_message(client, decode_input)

    if decode_input.text == "/cancel":
        await decode_input.delete()
        return await crosshair(client, session, callback_query)

    await callback_query.edit_message_text(session.locale.bot_loading)

    _crosshair = Crosshair.decode(decode_input.text)
    if _crosshair is None:
        await decode_input.delete()
        return await decode_crosshair(client, session, callback_query, last_error=session.locale.crosshair_decode_error)

    text = session.locale.crosshair_decode_result.format('; '.join(_crosshair.commands))

    await decode_input.reply(text)
    await callback_query.message.reply(session.locale.bot_choose_func,
                                       reply_markup=keyboards.crosshair_markup(session.locale))


@log_exception_callback
@came_from(main_menu)
@ignore_message_not_modified
async def send_exchange_rate(_, session: UserSession, callback_query: CallbackQuery):
    prices = ExchangeRate.cached_data()

    await callback_query.edit_message_text(session.locale.exchangerate_text.format(*prices.values()),
                                           reply_markup=keyboards.extra_markup(session.locale))


@log_exception_callback
@ignore_message_not_modified
async def send_valve_hq_time(_, session: UserSession, callback_query: CallbackQuery):
    """Send the time in Valve headquarters (Bellevue, Washington, US)"""

    text = server_stats_handlers.get_valve_hq_time(session.lang_code)

    await callback_query.edit_message_text(text, reply_markup=keyboards.extra_markup(session.locale))


@log_exception_callback
@ignore_message_not_modified
async def send_dropcap_timer(_, session: UserSession, callback_query: CallbackQuery):
    """Send drop cap reset time"""

    text = session.locale.game_dropcaptimer_text.format(*drop_cap_reset_timer())

    await callback_query.edit_message_text(text, reply_markup=keyboards.extra_markup(session.locale))


@log_exception_callback
@ignore_message_not_modified
async def send_game_version(client: BClient, session: UserSession, callback_query: CallbackQuery):
    """Send a current version of CS:GO/CS 2"""

    data = GameVersionData.cached_data()

    if data == States.UNKNOWN:
        return await something_went_wrong(client, session, callback_query)

    text = server_stats_handlers.get_game_version_summary(data, session.lang_code)

    await callback_query.edit_message_text(text, reply_markup=keyboards.extra_markup(session.locale),
                                           disable_web_page_preview=True)


# cat: Guns info


@came_from(extra_features)
async def guns(_, session: UserSession, callback_query: CallbackQuery):
    await callback_query.edit_message_text(session.locale.gun_select_category,
                                           reply_markup=keyboards.guns_markup(session.locale))


@came_from(guns)
async def pistols(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = await client.listen_callback(callback_query.message.chat.id,
                                                   callback_query.message.id)
    else:
        choosed_gun = await client.ask_callback_silently(callback_query,
                                                         session.locale.gun_select_pistol,
                                                         reply_markup=keyboards.pistols_markup(session.locale))

    await log_callback(client, choosed_gun)

    choosed_gun = choosed_gun.data

    if choosed_gun in GUNS_INFO:
        keyboards.pistols_markup.select_button_by_key(choosed_gun)
        return await send_gun_info(client, session, callback_query, pistols, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.pistols_markup)
    if choosed_gun == LK.bot_back:
        return await back(client, session, callback_query)
    return await unknown_request(client, session, callback_query, keyboards.pistols_markup)


@came_from(guns)
async def heavy(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = await client.listen_callback(callback_query.message.chat.id,
                                                   callback_query.message.id)
    else:
        choosed_gun = await client.ask_callback_silently(callback_query,
                                                         session.locale.gun_select_heavy,
                                                         reply_markup=keyboards.heavy_markup(session.locale))

    await log_callback(client, choosed_gun)

    choosed_gun = choosed_gun.data

    if choosed_gun in GUNS_INFO:
        keyboards.heavy_markup.select_button_by_key(choosed_gun)
        return await send_gun_info(client, session, callback_query, heavy, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.heavy_markup)
    if choosed_gun == LK.bot_back:
        return await back(client, session, callback_query)
    return await unknown_request(client, session, callback_query, keyboards.heavy_markup)


@came_from(guns)
async def smgs(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = await client.listen_callback(callback_query.message.chat.id,
                                                   callback_query.message.id)
    else:
        choosed_gun = await client.ask_callback_silently(callback_query,
                                                         session.locale.gun_select_smg,
                                                         reply_markup=keyboards.smgs_markup(session.locale))

    await log_callback(client, choosed_gun)

    choosed_gun = choosed_gun.data
    if choosed_gun in GUNS_INFO:
        keyboards.smgs_markup.select_button_by_key(choosed_gun)
        return await send_gun_info(client, session, callback_query, smgs, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.smgs_markup)
    if choosed_gun == LK.bot_back:
        return await back(client, session, callback_query)
    return await unknown_request(client, session, callback_query, keyboards.smgs_markup)


@came_from(guns)
async def rifles(client: BClient, session: UserSession, callback_query: CallbackQuery, loop: bool = False):
    if loop:
        choosed_gun = await client.listen_callback(callback_query.message.chat.id,
                                                   callback_query.message.id)
    else:
        choosed_gun = await client.ask_callback_silently(callback_query,
                                                         session.locale.gun_select_rifle,
                                                         reply_markup=keyboards.rifles_markup(session.locale))

    await log_callback(client, choosed_gun)

    choosed_gun = choosed_gun.data
    if choosed_gun in GUNS_INFO:
        keyboards.rifles_markup.select_button_by_key(choosed_gun)
        return await send_gun_info(client, session, callback_query, rifles, GUNS_INFO[choosed_gun],
                                   reply_markup=keyboards.rifles_markup)
    if choosed_gun == LK.bot_back:
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


# cat: Commands


@bot.on_message(filters.command('start'))
async def welcome(client: BClient, message: Message):
    """First bot's message"""

    session = client.sessions[message.from_user.id]

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, session, message)

    text = session.locale.bot_start_text.format(message.from_user.first_name)

    await message.reply(text)
    await message.reply(session.locale.bot_choose_cmd, reply_markup=keyboards.main_markup(session.locale))


@bot.on_message(filters.command('feedback'))
async def leave_feedback(client: BClient, message: Message):
    """Send feedback"""

    session = client.sessions[message.from_user.id]

    if message.chat.type != ChatType.PRIVATE:
        return await pm_only(client, session, message)

    text = session.locale.bot_feedback_text + '\n\n' + session.locale.bot_use_cancel

    feedback = await client.ask_message(message.chat.id, text)

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


@bot.on_message(filters.command('help'))
async def _help(client: BClient, message: Message):
    """/help message"""
    
    session = client.sessions[message.from_user.id]

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


async def back(client: BClient, session: UserSession, callback_query: CallbackQuery):
    if session.came_from is None:
        return await main_menu(client, callback_query, session_timeout=True)
    await session.came_from(client, session, callback_query)


async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(bot.clear_timeout_sessions, 'interval', minutes=10)

    scheduler.start()

    try:
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
        await bot.stop()


if __name__ == '__main__':
    bot.run(main())
