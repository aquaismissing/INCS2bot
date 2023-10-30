import logging
import re
import traceback

from pyrogram.enums import ParseMode
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

# noinspection PyUnresolvedReferences
import env
import config
from functions import datacenter_handlers, info_formatters
import keyboards
from l10n import dump_tags
from utypes import (BClient, DatacenterInlineResult, ExchangeRate,
                    GameServersData, GameVersionData, UserSession,
                    drop_cap_reset_timer)


TAGS = dump_tags()


def log_exception_inline(func):
    """Decorator to catch and log exceptions in bot inline functions."""

    async def inner(client: BClient, session: UserSession, inline_query: InlineQuery, *args, **kwargs):
        # noinspection PyBroadException
        try:
            await func(client, session, inline_query, *args, **kwargs)
        except Exception:
            logging.exception('Caught exception!')
            await client.log(f'❗️ {traceback.format_exc()}\n'
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
    if user.id not in client.sessions:
        await client.register_session(user, force_lang=config.FORCE_LANG)

    session = client.sessions[user.id]
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
        DatacenterInlineResult(session.locale.dc_austria_inline_title,
                               'https://telegra.ph/file/2287811648e78e851867f.png',
                               datacenter_handlers.austria,
                               TAGS.dc_europe_austria),
        DatacenterInlineResult(session.locale.dc_finland_inline_title,
                               'https://telegra.ph/file/679a01598932aeebceb55.png',
                               datacenter_handlers.finland,
                               TAGS.dc_europe_finland),
        DatacenterInlineResult(session.locale.dc_germany_inline_title,
                               'https://telegra.ph/file/e19c71673c65a791f1e7b.png',
                               datacenter_handlers.germany,
                               TAGS.dc_europe_germany),
        DatacenterInlineResult(session.locale.dc_netherlands_inline_title,
                               'https://telegra.ph/file/984b82bbf8bcff40d7e74.png',
                               datacenter_handlers.netherlands,
                               TAGS.dc_europe_netherlands),
        DatacenterInlineResult(session.locale.dc_poland_inline_title,
                               'https://telegra.ph/file/485df799a416149642142.png',
                               datacenter_handlers.poland,
                               TAGS.dc_europe_poland),
        DatacenterInlineResult(session.locale.dc_spain_inline_title,
                               'https://telegra.ph/file/72b3dfb6830aa95f48064.png',
                               datacenter_handlers.spain,
                               TAGS.dc_europe_spain),
        DatacenterInlineResult(session.locale.dc_sweden_inline_title,
                               'https://telegra.ph/file/f552dc251f2c0a4e5be53.png',
                               datacenter_handlers.sweden,
                               TAGS.dc_europe_sweden),
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
        DatacenterInlineResult(session.locale.dc_brazil_inline_title,
                               'https://telegra.ph/file/71264c82d0f7f6b8cb848.png',
                               datacenter_handlers.brazil,
                               TAGS.dc_southamerica_brazil),
        DatacenterInlineResult(session.locale.dc_peru_inline_title,
                               'https://telegra.ph/file/df707dd2664bdfcaef66f.png',
                               datacenter_handlers.peru,
                               TAGS.dc_southamerica_peru),
        DatacenterInlineResult(session.locale.dc_chile_inline_title,
                               'https://telegra.ph/file/85f0997f445ddf5f2e56a.png',
                               datacenter_handlers.chile,
                               TAGS.dc_southamerica_chile),
        DatacenterInlineResult(session.locale.dc_argentina_inline_title,
                               'https://telegra.ph/file/3a2333e7effcc377e3848.png',
                               datacenter_handlers.argentina,
                               TAGS.dc_southamerica_argentina)
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
                    InputTextMessageContent(_dc.summary_from(session.locale)),
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
                        InputTextMessageContent(_dc.summary_from(session.locale)),
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
    game_version_data = GameVersionData.cached_data()

    server_status_text = info_formatters.format_server_status(GameServersData.cached_server_status(),
                                                              session.locale)
    matchmaking_stats_text = info_formatters.format_matchmaking_stats(
        GameServersData.cached_matchmaking_stats(), session.locale
    )

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
