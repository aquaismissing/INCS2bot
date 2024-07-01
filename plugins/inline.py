from __future__ import annotations

import datetime as dt
import logging
import re
import traceback
from typing import TYPE_CHECKING

from pyrogram.enums import ParseMode
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from bottypes import BotClient, UserSession
import config
from dcatlas import DatacenterAtlas
from functions import info_formatters, caching
import keyboards
from l10n import load_tags
from utypes import (DatacenterInlineResult, ExchangeRate,
                    GameServers, GameVersion,
                    drop_cap_reset_timer)

if TYPE_CHECKING:
    from keyboards import ExtendedIKM
    from l10n import Locale


TAGS = load_tags()

logger = logging.getLogger('INCS2bot')


def log_exception_inline(func):
    """Decorator to catch and log exceptions in bot inline functions."""

    async def inner(client: BotClient, session: UserSession, inline_query: InlineQuery, *args, **kwargs):
        # noinspection PyBroadException
        try:
            await func(client, session, inline_query, *args, **kwargs)
        except Exception:
            logger.exception('Caught exception!')
            await client.log(f'❗️ {traceback.format_exc()}\n'
                             f'\n'
                             f'↩️ inline_query',
                             disable_notification=True, parse_mode=ParseMode.DISABLED)
            client.rstats.exceptions_caught += 1
    return inner


def is_user_stats_page(query: InlineQuery):
    steamid = re.search('-[0-9]+-', query.query.strip())
    if steamid is None:
        return False

    steamid = steamid.group(0)[1:-1]
    return query.query.startswith('https://telegra.ph/') and steamid.startswith('7656') and len(steamid) == 17


def get_triggered_tags(query: str):
    triggered_tags = set()
    for tags in TAGS.to_dict().values():
        if query in tags:
            triggered_tags.add(query)
            continue

        for tag in tags:
            if any(t.startswith(query) for t in tag.split()):
                triggered_tags.add(tag)

    return triggered_tags


def dc_articles_factory(dcs: list[DatacenterInlineResult],
                        locale: Locale,
                        last_info_update_at: dt.datetime,
                        reply_markup: ExtendedIKM) -> list[InlineQueryResultArticle]:
    result = []
    for i, dc in enumerate(dcs):
        result.append(
            InlineQueryResultArticle(
                dc.title,
                InputTextMessageContent(info_formatters.format_datacenter_state(dc.state, locale, last_info_update_at)),
                f'{i}',
                description=locale.dc_status_inline_description,
                reply_markup=reply_markup,
                thumb_url=dc.thumbnail
            )
        )

    return result


@BotClient.on_inline_query()
async def sync_user_data_inline(client: BotClient, inline_query: InlineQuery):
    user = inline_query.from_user
    session = await client.register_session(user)

    await client.log_inline(session, inline_query)

    query = inline_query.query.strip()

    client.rstats.inline_queries_handled += 1

    # if-chain because it's a plugin
    if is_user_stats_page(inline_query):
        return await share_inline(client, session, inline_query)
    if query.startswith('price'):
        return await inline_exchange_rate(client, session, inline_query)
    if query.startswith('dc'):
        return await inline_datacenters(client, session, inline_query)
    return await default_inline(client, session, inline_query)


async def share_inline(_, session: UserSession, inline_query: InlineQuery):
    r = InlineQueryResultArticle(session.locale.user_gamestats_inline_title,
                                 InputTextMessageContent(inline_query.query),
                                 description=inline_query.query)
    await inline_query.answer([r], cache_time=10)


@log_exception_inline
async def inline_exchange_rate(_, session: UserSession, inline_query: InlineQuery):
    core_cache = caching.load_cache(config.CORE_CACHE_FILE_PATH)
    data = ExchangeRate.cached_data(core_cache).asdict()

    try:
        query = inline_query.query.split()[1].lower()
    except IndexError:
        result = [
            InlineQueryResultArticle(
                session.locale.exchangerate_inline_title,
                InputTextMessageContent(session.locale.exchangerate_inline_text_default),
                description=session.locale.exchangerate_inline_description,
            )
        ]
        return await inline_query.answer(result, cache_time=10)

    results = []
    currencies = []
    for k, v in TAGS.currencies_to_dict().items():
        if any(query in tag for tag in v):
            currencies.append(k)

    if not currencies:
        currency_available = (session.locale.currencies_tags.format(k.upper(),
                                                                    session.locale.get(f'currencies_{k}'),
                                                                    ', '.join(v - {k}))
                              for k, v in TAGS.currencies_to_dict().items())

        results.append(
            InlineQueryResultArticle(
                session.locale.exchangerate_inline_title_notfound,
                InputTextMessageContent('\n'.join(currency_available)),
                description=session.locale.exchangerate_inline_description_notfound,
            )
        )
        return await inline_query.answer(results, cache_time=5)

    for i, currency in enumerate(currencies):
        value = data[currency.upper()]
        symbol = ExchangeRate.CURRENCIES_SYMBOLS[currency.upper()]
        results.append(
            InlineQueryResultArticle(
                session.locale.exchangerate_inline_title_selected.format(symbol),
                InputTextMessageContent(session.locale.exchangerate_inline_text_selected.format(value, symbol)),
                f'{i}',
                description=session.locale.exchangerate_inline_description_selected.format(value, symbol)
            )
        )

    await inline_query.answer(results, cache_time=10)


@log_exception_inline
async def inline_datacenters(_, session: UserSession, inline_query: InlineQuery):
    cache = caching.load_cache(config.CORE_CACHE_FILE_PATH)
    dc_cache = cache['datacenters']

    dcs = [
        DatacenterInlineResult(session.locale.dc_china_inline_title,
                               'https://telegra.ph/file/ff0dad30ae32144d7cd0c.jpg',
                               DatacenterAtlas.CHINA.cached_state(dc_cache),
                               TAGS.dc_asia_china),
        DatacenterInlineResult(session.locale.dc_emirates_inline_title,
                               'https://telegra.ph/file/1de1e51e62b79cae5181a.jpg',
                               DatacenterAtlas.EMIRATES.cached_state(dc_cache),
                               TAGS.dc_asia_emirates),
        DatacenterInlineResult(session.locale.dc_hongkong_inline_title,
                               'https://telegra.ph/file/0b209e65c421910419f34.jpg',
                               DatacenterAtlas.HONGKONG.cached_state(dc_cache),
                               TAGS.dc_asia_hongkong),
        DatacenterInlineResult(session.locale.dc_india_inline_title,
                               'https://telegra.ph/file/b2213992b750940113b69.jpg',
                               DatacenterAtlas.INDIA.cached_state(dc_cache),
                               TAGS.dc_asia_india),
        DatacenterInlineResult(session.locale.dc_japan_inline_title,
                               'https://telegra.ph/file/11b6601a3e60940d59c88.jpg',
                               DatacenterAtlas.JAPAN.cached_state(dc_cache),
                               TAGS.dc_asia_japan),
        DatacenterInlineResult(session.locale.dc_singapore_inline_title,
                               'https://telegra.ph/file/1c2121ceec5d1482173d5.jpg',
                               DatacenterAtlas.SINGAPORE.cached_state(dc_cache),
                               TAGS.dc_asia_singapore),
        DatacenterInlineResult(session.locale.dc_southkorea_inline_title,
                               'https://telegra.ph/file/2265e9728d06632773537.png',
                               DatacenterAtlas.SOUTH_KOREA.cached_state(dc_cache),
                               TAGS.dc_asia_southkorea),
        DatacenterInlineResult(session.locale.dc_austria_inline_title,
                               'https://telegra.ph/file/2287811648e78e851867f.png',
                               DatacenterAtlas.AUSTRIA.cached_state(dc_cache),
                               TAGS.dc_europe_austria),
        DatacenterInlineResult(session.locale.dc_finland_inline_title,
                               'https://telegra.ph/file/679a01598932aeebceb55.png',
                               DatacenterAtlas.FINLAND.cached_state(dc_cache),
                               TAGS.dc_europe_finland),
        DatacenterInlineResult(session.locale.dc_germany_inline_title,
                               'https://telegra.ph/file/e19c71673c65a791f1e7b.png',
                               DatacenterAtlas.GERMANY.cached_state(dc_cache),
                               TAGS.dc_europe_germany),
        # DatacenterInlineResult(session.locale.dc_netherlands_inline_title,
        #                        'https://telegra.ph/file/984b82bbf8bcff40d7e74.png',
        #                        DatacenterAtlas.NETHERLANDS.cached_state(cache),
        #                        TAGS.dc_europe_netherlands),
        DatacenterInlineResult(session.locale.dc_poland_inline_title,
                               'https://telegra.ph/file/485df799a416149642142.png',
                               DatacenterAtlas.POLAND.cached_state(dc_cache),
                               TAGS.dc_europe_poland),
        DatacenterInlineResult(session.locale.dc_spain_inline_title,
                               'https://telegra.ph/file/72b3dfb6830aa95f48064.png',
                               DatacenterAtlas.SPAIN.cached_state(dc_cache),
                               TAGS.dc_europe_spain),
        DatacenterInlineResult(session.locale.dc_sweden_inline_title,
                               'https://telegra.ph/file/f552dc251f2c0a4e5be53.png',
                               DatacenterAtlas.SWEDEN.cached_state(dc_cache),
                               TAGS.dc_europe_sweden),
        DatacenterInlineResult(session.locale.dc_uk_inline_title,
                               'https://telegra.ph/file/f92ba1d5bd6f2b01e0ad8.png',
                               DatacenterAtlas.UK.cached_state(dc_cache),
                               TAGS.dc_europe_uk),
        DatacenterInlineResult(session.locale.dc_us_east_inline_title,
                               'https://telegra.ph/file/06119c30872031d1047d0.jpg',
                               DatacenterAtlas.US_EAST.cached_state(dc_cache),
                               TAGS.dc_us_east),
        DatacenterInlineResult(session.locale.dc_us_west_inline_title,
                               'https://telegra.ph/file/06119c30872031d1047d0.jpg',
                               DatacenterAtlas.US_WEST.cached_state(dc_cache),
                               TAGS.dc_us_west),
        DatacenterInlineResult(session.locale.dc_australia_inline_title,
                               'https://telegra.ph/file/5dc6beef1556ea852284c.jpg',
                               DatacenterAtlas.AUSTRALIA.cached_state(dc_cache),
                               TAGS.dc_australia),
        DatacenterInlineResult(session.locale.dc_africa_inline_title,
                               'https://telegra.ph/file/12628c8193b48302722e8.jpg',
                               DatacenterAtlas.AFRICA.cached_state(dc_cache),
                               TAGS.dc_africa),
        DatacenterInlineResult(session.locale.dc_brazil_inline_title,
                               'https://telegra.ph/file/71264c82d0f7f6b8cb848.png',
                               DatacenterAtlas.BRAZIL.cached_state(dc_cache),
                               TAGS.dc_southamerica_brazil),
        DatacenterInlineResult(session.locale.dc_peru_inline_title,
                               'https://telegra.ph/file/df707dd2664bdfcaef66f.png',
                               DatacenterAtlas.PERU.cached_state(dc_cache),
                               TAGS.dc_southamerica_peru),
        DatacenterInlineResult(session.locale.dc_chile_inline_title,
                               'https://telegra.ph/file/85f0997f445ddf5f2e56a.png',
                               DatacenterAtlas.CHILE.cached_state(dc_cache),
                               TAGS.dc_southamerica_chile),
        DatacenterInlineResult(session.locale.dc_argentina_inline_title,
                               'https://telegra.ph/file/3a2333e7effcc377e3848.png',
                               DatacenterAtlas.ARGENTINA.cached_state(dc_cache),
                               TAGS.dc_southamerica_argentina)
    ]
    dcs.sort(key=lambda x: x.title)

    last_info_updated_at = GameServers.latest_info_update(cache)  # fixme: what happens if returns States.UNKNOWN?

    inline_btn = keyboards.markup_inline_button(session.locale)

    try:
        query = inline_query.query.split()[1].strip().lower()
    except IndexError:  # no query, return all DCs
        resulted_articles = dc_articles_factory(dcs, session.locale, last_info_updated_at, inline_btn)
        return await inline_query.answer(resulted_articles, cache_time=5)

    triggered_tags = get_triggered_tags(query)
    resulted_dcs = [dc for dc in dcs if dc.tags & triggered_tags]

    resulted_articles = dc_articles_factory(resulted_dcs, session.locale, last_info_updated_at, inline_btn)
    await inline_query.answer(resulted_articles, cache_time=10)


@log_exception_inline
async def default_inline(_, session: UserSession, inline_query: InlineQuery):
    core_cache = caching.load_cache(config.CORE_CACHE_FILE_PATH)
    gc_cache = caching.load_cache(config.GC_CACHE_FILE_PATH)
    graph_cache = caching.load_cache(config.GRAPH_CACHE_FILE_PATH)

    servers_status_data = GameServers.cached_server_status(core_cache, gc_cache)
    matchmaking_stats_data = GameServers.cached_matchmaking_stats(core_cache, gc_cache, graph_cache)
    game_version_data = GameVersion.cached_data(gc_cache)

    server_status_text = info_formatters.format_server_status(servers_status_data, session.locale)
    matchmaking_stats_text = info_formatters.format_matchmaking_stats(matchmaking_stats_data, session.locale)
    valve_hq_time_text = info_formatters.format_valve_hq_time(session.locale)
    drop_cap_reset_timer_text = session.locale.game_dropcaptimer_text.format(*drop_cap_reset_timer())
    game_version_text = info_formatters.format_game_version_info(game_version_data, session.locale)

    inline_btn = keyboards.markup_inline_button(session.locale)

    server_status = InlineQueryResultArticle(session.locale.game_status_inline_title,
                                             InputTextMessageContent(server_status_text),
                                             '0',
                                             description=session.locale.game_status_inline_description,
                                             reply_markup=inline_btn,
                                             thumb_url="https://telegra.ph/file/8b640b85f6d62f8ed2900.jpg")
    matchmaking_stats = InlineQueryResultArticle(session.locale.stats_matchmaking_inline_title,
                                                 InputTextMessageContent(matchmaking_stats_text),
                                                 '1',
                                                 description=session.locale.stats_matchmaking_inline_description,
                                                 reply_markup=inline_btn,
                                                 thumb_url="https://telegra.ph/file/57ba2b279c53d69d72481.jpg")
    valve_hq_time = InlineQueryResultArticle(session.locale.valve_hqtime_inline_title,
                                             InputTextMessageContent(valve_hq_time_text),
                                             '2',
                                             description=session.locale.valve_hqtime_inline_description,
                                             reply_markup=inline_btn,
                                             thumb_url="https://telegra.ph/file/24b05cea99de936fd12bf.jpg")
    drop_cap_reset = InlineQueryResultArticle(session.locale.game_dropcaptimer_inline_title,
                                              InputTextMessageContent(drop_cap_reset_timer_text),
                                              '3',
                                              description=session.locale.game_dropcaptimer_inline_description,
                                              reply_markup=inline_btn,
                                              thumb_url="https://telegra.ph/file/6948255408689d2f6a472.jpg")
    game_version = InlineQueryResultArticle(session.locale.game_version_inline_title,
                                            InputTextMessageContent(game_version_text, disable_web_page_preview=True),
                                            '4',
                                            description=session.locale.game_version_inline_description,
                                            reply_markup=inline_btn,
                                            thumb_url="https://telegra.ph/file/82d8df1e9f5140da70232.jpg")

    results = [server_status, matchmaking_stats, valve_hq_time, drop_cap_reset, game_version]
    await inline_query.answer(results, cache_time=10)
