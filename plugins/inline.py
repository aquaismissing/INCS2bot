import logging
import re
import traceback

import pandas as pd
from pyrogram.enums import ParseMode
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

# noinspection PyUnresolvedReferences
import env
import config
from functions import datacenter_handlers, log_inline, server_stats_handlers
import keyboards
from l10n import dump_tags
from utypes import (BClient, DatacenterInlineResult, ExchangeRate,
                    GameServersData, GameVersionData, UserSession,
                    drop_cap_reset_timer)


TAGS = dump_tags()


def log_exception_inline(func):
    """Decorator to catch and log exceptions in bot inline functions."""

    async def inner(client: BClient, session: UserSession, inline_query: InlineQuery, *args, **kwargs):
        try:
            await func(client, session, inline_query, *args, **kwargs)
        except Exception as e:
            logging.exception('Caught exception!')
            await client.send_message(config.LOGCHANNEL, f'❗️ {traceback.format_exc()}\n'
                                                         f'\n'
                                                         f'↩️ inline_query',
                                      disable_notification=True, parse_mode=ParseMode.DISABLED)

    return inner


def is_user_stats_page(query: InlineQuery):
    steamid = re.search('-[0-9]+-', query.query.strip())
    if steamid is None:
        return False

    steamid = steamid.group(0)[1:-1]
    return query.query.startswith('https://telegra.ph/') and steamid.startswith('7656') and len(steamid) == 17


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

    if user.id not in client.sessions:
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

        client.register_session(user, force_lang=config.FORCE_LANG)

    session = client.sessions[user.id]
    query = inline_query.query.strip()

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
    data = ExchangeRate.cached_data()

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

    if not any(query in tag for tag in TAGS.currencies_to_list()):
        currency_available = (session.locale.currencies_tags.format(k.upper(),
                                                                    session.locale.get(f'currencies_{k}'),
                                                                    ', '.join(v[1:]))
                              for k, v in TAGS.currencies_to_dict().items())

        results.append(
            InlineQueryResultArticle(
                session.locale.exchangerate_inline_title_notfound,
                InputTextMessageContent('\n'.join(currency_available)),
                description=session.locale.exchangerate_inline_description_notfound,
            )
        )
        return await inline_query.answer(results, cache_time=5)

    currencies = []
    for k, v in TAGS.currencies_to_dict().items():
        if any(query in tag for tag in v):
            currencies.append(k)

    for i, currency in enumerate(currencies):
        value = data[currency.upper()]
        symbol = ExchangeRate.currencies_symbols[currency.upper()]
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
    dcs = [
        DatacenterInlineResult(session.locale.dc_china_inline_title,
                               'https://telegra.ph/file/ff0dad30ae32144d7cd0c.jpg',
                               datacenter_handlers.china,
                               TAGS.dc_asia_china),
        DatacenterInlineResult(session.locale.dc_emirates_inline_title,
                               'https://telegra.ph/file/1de1e51e62b79cae5181a.jpg',
                               datacenter_handlers.emirates,
                               TAGS.dc_asia_emirates),
        DatacenterInlineResult(session.locale.dc_hongkong_inline_title,
                               'https://telegra.ph/file/0b209e65c421910419f34.jpg',
                               datacenter_handlers.hongkong,
                               TAGS.dc_asia_hongkong),
        DatacenterInlineResult(session.locale.dc_india_inline_title,
                               'https://telegra.ph/file/b2213992b750940113b69.jpg',
                               datacenter_handlers.india,
                               TAGS.dc_asia_india),
        DatacenterInlineResult(session.locale.dc_japan_inline_title,
                               'https://telegra.ph/file/11b6601a3e60940d59c88.jpg',
                               datacenter_handlers.japan,
                               TAGS.dc_asia_japan),
        DatacenterInlineResult(session.locale.dc_singapore_inline_title,
                               'https://telegra.ph/file/1c2121ceec5d1482173d5.jpg',
                               datacenter_handlers.singapore,
                               TAGS.dc_asia_singapore),
        DatacenterInlineResult(session.locale.dc_southkorea_inline_title,
                               'https://telegra.ph/file/2265e9728d06632773537.png',
                               datacenter_handlers.south_korea,
                               TAGS.dc_asia_southkorea),
        DatacenterInlineResult(session.locale.dc_eu_north_inline_title,
                               'https://telegra.ph/file/4d269cb98aadaae391024.jpg',
                               datacenter_handlers.eu_north,
                               TAGS.dc_europe_north),
        DatacenterInlineResult(session.locale.dc_eu_east_inline_title,
                               'https://telegra.ph/file/4d269cb98aadaae391024.jpg',
                               datacenter_handlers.eu_east,
                               TAGS.dc_europe_east),
        DatacenterInlineResult(session.locale.dc_eu_west_inline_title,
                               'https://telegra.ph/file/4d269cb98aadaae391024.jpg',
                               datacenter_handlers.eu_west,
                               TAGS.dc_europe_west),
        DatacenterInlineResult(session.locale.dc_us_north_inline_title,
                               'https://telegra.ph/file/06119c30872031d1047d0.jpg',
                               datacenter_handlers.us_north,
                               TAGS.dc_us_north),
        DatacenterInlineResult(session.locale.dc_us_south_inline_title,
                               'https://telegra.ph/file/06119c30872031d1047d0.jpg',
                               datacenter_handlers.us_south,
                               TAGS.dc_us_south),
        DatacenterInlineResult(session.locale.dc_australia_inline_title,
                               'https://telegra.ph/file/5dc6beef1556ea852284c.jpg',
                               datacenter_handlers.australia,
                               TAGS.dc_australia),
        DatacenterInlineResult(session.locale.dc_africa_inline_title,
                               'https://telegra.ph/file/12628c8193b48302722e8.jpg',
                               datacenter_handlers.africa,
                               TAGS.dc_africa),
        DatacenterInlineResult(session.locale.dc_southamerica_inline_title,
                               'https://telegra.ph/file/60f8226ea5d72815bef57.jpg',
                               datacenter_handlers.south_america,
                               TAGS.dc_southamerica)
    ]
    dcs.sort(key=lambda x: x.title)

    inline_btn = keyboards.markup_inline_button(session.locale)

    resulted_dcs = []
    resulted_articles = []

    try:
        query = inline_query.query.split()[1]
    except IndexError:
        for i, _dc in enumerate(dcs):
            resulted_articles.append(
                InlineQueryResultArticle(
                    _dc.title,
                    InputTextMessageContent(_dc.summary_from(session.lang_code)),
                    f'{i}',
                    description=session.locale.dc_status_inline_description,
                    reply_markup=inline_btn,
                    thumb_url=_dc.thumbnail
                )
            )
        return await inline_query.answer(resulted_articles, cache_time=5)

    i = 0
    for tag in get_triggered_tags(query):
        for _dc in dcs:
            if tag in _dc.tags and _dc not in resulted_dcs:
                resulted_dcs.append(_dc)
                res = InlineQueryResultArticle(
                        _dc.title,
                        InputTextMessageContent(_dc.summary_from(session.lang_code)),
                        f'{i}',
                        description=session.locale.dc_status_inline_description,
                        reply_markup=inline_btn,
                        thumb_url=_dc.thumbnail
                )
                resulted_articles.append(res)
                i += 1

    await inline_query.answer(resulted_articles, cache_time=10)


@log_exception_inline
async def default_inline(_, session: UserSession, inline_query: InlineQuery):
    lang_code = session.lang_code

    game_version_data = GameVersionData.cached_data()

    server_status_text = server_stats_handlers.get_server_status_summary(GameServersData.cached_server_status(),
                                                                         lang_code)
    matchmaking_stats_text = server_stats_handlers.get_matchmaking_stats_summary(
        GameServersData.cached_matchmaking_stats(), lang_code
    )

    valve_hq_time_text = server_stats_handlers.get_valve_hq_time(lang_code)
    drop_cap_reset_timer_text = session.locale.game_dropcaptimer_text.format(*drop_cap_reset_timer())
    game_version_text = server_stats_handlers.get_game_version_summary(game_version_data, lang_code)

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
