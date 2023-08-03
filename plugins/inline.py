import logging
import re
from zoneinfo import ZoneInfo

import datetime as dt

import pandas as pd
from babel.dates import format_datetime
from pyrogram import Client, filters
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import ParseMode

# noinspection PyUnresolvedReferences
import env
import config
import keyboards
from functions import datacenter_handlers, log_inline, server_stats_handlers
from l10n import dump_tags
from utypes import (BClient, ExchangeRate, GameServersData,
                    GameVersionData, DatacenterInlineResult,
                    drop_cap_reset_timer)


VALVE_TIMEZONE = ZoneInfo("America/Los_Angeles")
TAGS = dump_tags()

CLOCKS = ('🕛', '🕐', '🕑', '🕒', '🕓', '🕔',
          '🕕', '🕖', '🕗', '🕘', '🕙', '🕚')


def log_exception_inline(func):
    """Decorator to catch and log exceptions in bot inline functions. Also call `something_went_wrong(message)`."""

    async def inner(client: Client, inline_query: InlineQuery, *args, **kwargs):
        try:
            await func(client, inline_query, *args, **kwargs)
        except Exception as e:
            logging.exception('Caught exception!')
            await client.send_message(config.LOGCHANNEL, f'❗️{e}\n\n↩️ inline_query', disable_notification=True)

    return inner


async def _is_user_stats_page_func(_, __, query: InlineQuery):
    steamid = re.search('-[0-9]+-', query.query.strip())
    if steamid is None:
        return False
    steamid = steamid.group(0)[1:-1]
    return query.query.startswith('https://telegra.ph/') and steamid.startswith('7656') and len(steamid) == 17


is_user_stats_page_filter = filters.create(_is_user_stats_page_func)


async def _triggers_any_dc_tag_func(_, __, query: InlineQuery):
    data = query.query.strip().lower()
    return data and any(t.startswith(data) for tag in TAGS.dcs_to_set() for t in tag.split())


triggers_any_dc_tag_filter = filters.create(_triggers_any_dc_tag_func)


def get_triggered_tags(query: str):
    data = query.strip().lower()
    for tags in TAGS.to_dict().values():
        for tag in tags:
            if any(t.startswith(data) for t in tag.split()):
                yield tag


@BClient.on_inline_query()
async def sync_user_data_inline(client: BClient, inline_query: InlineQuery):
    user = inline_query.from_user
    await log_inline(client, inline_query)

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

    inline_query.continue_propagation()


# noinspection PyTypeChecker
@BClient.on_inline_query(is_user_stats_page_filter)
async def share_inline(client: BClient, inline_query: InlineQuery):
    r = InlineQueryResultArticle(client.locale.user_gamestats_inline_title,
                                 InputTextMessageContent(inline_query.query),
                                 description=inline_query.query)
    await inline_query.answer([r], cache_time=5)


@BClient.on_inline_query(filters.regex("price"))
@log_exception_inline
async def inline_exchange_rate(client: BClient, inline_query: InlineQuery):
    data = ExchangeRate.cached_data()

    try:
        query = inline_query.query.split()[1]
    except IndexError:
        result = [
            InlineQueryResultArticle(
                client.locale.exchangerate_inline_title,
                InputTextMessageContent(client.locale.exchangerate_inline_text_default),
                description=client.locale.exchangerate_inline_description,
            )
        ]
        return await inline_query.answer(result, cache_time=5)

    results = []

    if not any(query in tag for tag in TAGS.currencies_to_list()):
        currency_available = (client.locale.currencies_tags.format(k.upper(),
                                                                   client.locale.get(f'currencies_{k}'), ', '.join(v))
                              for k, v in TAGS.currencies_to_dict().items())

        results.append(
            InlineQueryResultArticle(
                client.locale.exchangerate_inline_title_notfound,
                InputTextMessageContent('\n'.join(currency_available), parse_mode=ParseMode.HTML),
                description=client.locale.exchangerate_inline_description_notfound,
            )
        )
        return await inline_query.answer(results, cache_time=5)

    currencies = []
    for k, v in TAGS.currencies_to_dict().items():
        if any(query in tag for tag in v):
            currencies.append(k)

    for currency in currencies:
        value = data[currency.upper()]
        symbol = ExchangeRate.currencies_symbols[currency.upper()]
        results.append(
            InlineQueryResultArticle(
                client.locale.exchangerate_inline_title_selected.format(symbol),
                InputTextMessageContent(client.locale.exchangerate_inline_text_selected.format(value, symbol),
                                        parse_mode=ParseMode.HTML),
                description=client.locale.exchangerate_inline_description_selected.format(value, symbol)
            )
        )

    await inline_query.answer(results, cache_time=5)


# noinspection PyTypeChecker
@BClient.on_inline_query(filters.regex("dc"))
@log_exception_inline
async def inline_datacenters(client: BClient, inline_query: InlineQuery):
    dcs = [
        DatacenterInlineResult(client.locale.dc_china_inline_title,
                               'https://telegra.ph/file/ff0dad30ae32144d7cd0c.jpg',
                               datacenter_handlers.china,
                               TAGS.dc_asia_china),
        DatacenterInlineResult(client.locale.dc_emirates_inline_title,
                               'https://telegra.ph/file/1de1e51e62b79cae5181a.jpg',
                               datacenter_handlers.emirates,
                               TAGS.dc_asia_emirates),
        DatacenterInlineResult(client.locale.dc_hongkong_inline_title,
                               'https://telegra.ph/file/0b209e65c421910419f34.jpg',
                               datacenter_handlers.hongkong,
                               TAGS.dc_asia_hongkong),
        DatacenterInlineResult(client.locale.dc_india_inline_title,
                               'https://telegra.ph/file/b2213992b750940113b69.jpg',
                               datacenter_handlers.india,
                               TAGS.dc_asia_india),
        DatacenterInlineResult(client.locale.dc_japan_inline_title,
                               'https://telegra.ph/file/11b6601a3e60940d59c88.jpg',
                               datacenter_handlers.japan,
                               TAGS.dc_asia_japan),
        DatacenterInlineResult(client.locale.dc_singapore_inline_title,
                               'https://telegra.ph/file/1c2121ceec5d1482173d5.jpg',
                               datacenter_handlers.singapore,
                               TAGS.dc_asia_singapore),
        DatacenterInlineResult(client.locale.dc_southkorea_inline_title,
                               'https://telegra.ph/file/2265e9728d06632773537.png',
                               datacenter_handlers.south_korea,
                               TAGS.dc_asia_southkorea),
        DatacenterInlineResult(client.locale.dc_eu_north_inline_title,
                               'https://telegra.ph/file/4d269cb98aadaae391024.jpg',
                               datacenter_handlers.eu_north,
                               TAGS.dc_europe_north),
        DatacenterInlineResult(client.locale.dc_eu_east_inline_title,
                               'https://telegra.ph/file/4d269cb98aadaae391024.jpg',
                               datacenter_handlers.eu_east,
                               TAGS.dc_europe_east),
        DatacenterInlineResult(client.locale.dc_eu_west_inline_title,
                               'https://telegra.ph/file/4d269cb98aadaae391024.jpg',
                               datacenter_handlers.eu_west,
                               TAGS.dc_europe_west),
        DatacenterInlineResult(client.locale.dc_us_north_inline_title,
                               'https://telegra.ph/file/06119c30872031d1047d0.jpg',
                               datacenter_handlers.us_north,
                               TAGS.dc_us_north),
        DatacenterInlineResult(client.locale.dc_us_south_inline_title,
                               'https://telegra.ph/file/06119c30872031d1047d0.jpg',
                               datacenter_handlers.us_south,
                               TAGS.dc_us_south),
        DatacenterInlineResult(client.locale.dc_australia_inline_title,
                               'https://telegra.ph/file/5dc6beef1556ea852284c.jpg',
                               datacenter_handlers.australia,
                               TAGS.dc_australia),
        DatacenterInlineResult(client.locale.dc_africa_inline_title,
                               'https://telegra.ph/file/12628c8193b48302722e8.jpg',
                               datacenter_handlers.africa,
                               TAGS.dc_africa),
        DatacenterInlineResult(client.locale.dc_southamerica_inline_title,
                               'https://telegra.ph/file/60f8226ea5d72815bef57.jpg',
                               datacenter_handlers.south_america,
                               TAGS.dc_southamerica)
    ]
    dcs.sort(key=lambda x: x.title)

    inline_btn = keyboards.markup_inline_button(client.locale)

    resulted_dcs = []
    resulted_articles = []

    try:
        query = inline_query.query.split()[1]
    except IndexError:
        for _dc in dcs:
            resulted_articles.append(
                InlineQueryResultArticle(
                    _dc.title,
                    InputTextMessageContent(_dc.summary_from(client.session_lang_code), parse_mode=ParseMode.HTML),
                    description=client.locale.dc_status_inline_description,
                    reply_markup=inline_btn,
                    thumb_url=_dc.thumbnail
                )
            )
        return await inline_query.answer(resulted_articles, cache_time=5)

    for tag in get_triggered_tags(query):
        for _dc in dcs:
            if tag in _dc.tags and _dc not in resulted_dcs:
                resulted_dcs.append(_dc)
                resulted_articles.append(
                    InlineQueryResultArticle(
                        _dc.title,
                        InputTextMessageContent(_dc.summary_from(client.session_lang_code), parse_mode=ParseMode.HTML),
                        description=client.locale.dc_status_inline_description,
                        reply_markup=inline_btn,
                        thumb_url=_dc.thumbnail
                    )
                )

    await inline_query.answer(resulted_articles, cache_time=5)


@BClient.on_inline_query()
@log_exception_inline
async def default_inline(client: BClient, inline_query: InlineQuery):
    lang_code = inline_query.from_user.language_code

    valve_hq_datetime = dt.datetime.now(tz=VALVE_TIMEZONE)
    game_version_data = GameVersionData.cached_data()

    server_status_text = server_stats_handlers.get_server_status_summary(GameServersData.cached_server_status(),
                                                                         lang_code)
    matchmaking_stats_text = server_stats_handlers.get_matchmaking_stats_summary(
        GameServersData.cached_matchmaking_stats(), lang_code
    )
    valve_hq_dt_formatted = f'{format_datetime(valve_hq_datetime, "HH:mm:ss, dd MMM", locale=lang_code).title()} ' \
                            f'({valve_hq_datetime:%Z})'

    valve_hq_time_text = client.locale.valve_hqtime_text.format(CLOCKS[valve_hq_datetime.hour % 12],
                                                                valve_hq_dt_formatted)
    drop_cap_reset_timer_text = client.locale.game_dropcaptimer_text.format(*drop_cap_reset_timer())
    game_version_text = server_stats_handlers.get_game_version_summary(game_version_data, lang_code)

    inline_btn = keyboards.markup_inline_button(client.locale)

    server_status = InlineQueryResultArticle(client.locale.game_status_inline_title,
                                             InputTextMessageContent(server_status_text, parse_mode=ParseMode.HTML),
                                             description=client.locale.game_status_inline_description,
                                             reply_markup=inline_btn,
                                             thumb_url="https://telegra.ph/file/8b640b85f6d62f8ed2900.jpg")
    matchmaking_stats = InlineQueryResultArticle(client.locale.stats_matchmaking_inline_title,
                                                 InputTextMessageContent(matchmaking_stats_text,
                                                                         parse_mode=ParseMode.HTML),
                                                 description=client.locale.stats_matchmaking_inline_description,
                                                 reply_markup=inline_btn,
                                                 thumb_url="https://telegra.ph/file/57ba2b279c53d69d72481.jpg")
    valve_hq_time = InlineQueryResultArticle(client.locale.valve_hqtime_inline_title,
                                             InputTextMessageContent(valve_hq_time_text, parse_mode=ParseMode.HTML),
                                             description=client.locale.valve_hqtime_inline_description,
                                             reply_markup=inline_btn,
                                             thumb_url="https://telegra.ph/file/24b05cea99de936fd12bf.jpg")
    drop_cap_reset = InlineQueryResultArticle(client.locale.game_dropcaptimer_inline_title,
                                              InputTextMessageContent(drop_cap_reset_timer_text,
                                                                      parse_mode=ParseMode.HTML),
                                              description=client.locale.game_dropcaptimer_inline_description,
                                              reply_markup=inline_btn,
                                              thumb_url="https://telegra.ph/file/6948255408689d2f6a472.jpg")
    game_version = InlineQueryResultArticle(client.locale.game_version_inline_title,
                                            InputTextMessageContent(game_version_text,
                                                                    parse_mode=ParseMode.HTML,
                                                                    disable_web_page_preview=True),
                                            description=client.locale.game_version_inline_description,
                                            reply_markup=inline_btn,
                                            thumb_url="https://telegra.ph/file/82d8df1e9f5140da70232.jpg")

    results = [server_status, matchmaking_stats, valve_hq_time, drop_cap_reset, game_version]
    await inline_query.answer(results, cache_time=5)
