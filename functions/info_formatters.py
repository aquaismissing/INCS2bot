import datetime as dt
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from babel.dates import format_datetime
from jinja2 import Environment, FileSystemLoader

from l10n import Locale
from .locale import get_refined_lang_code
from utypes import States, LeaderboardStats


VALVE_TIMEZONE = ZoneInfo('America/Los_Angeles')
CLOCKS = ('🕛', '🕐', '🕑', '🕒', '🕓', '🕔',
          '🕕', '🕖', '🕗', '🕘', '🕙', '🕚')

env = Environment(loader=FileSystemLoader(Path(__file__).parent.parent))
game_stats_template = env.get_template('game_stats_template.html')

WEB_LEADERBOARD_LINK = 'https://csleaderboards.net/premier'
WEB_LEADERBOARD_REGIONS = {'africa': 'af',
                           'asia': 'as',
                           'australia': 'au',
                           'china': 'cn',
                           'europe': 'eu',
                           'northamerica': 'na',
                           'southamerica': 'sa'}


def format_server_status(data, locale: Locale) -> str:
    if data is States.UNKNOWN:
        return locale.error_internal

    lang_code = get_refined_lang_code(locale)

    (gs_dt, gc_state, sl_state, ms_state,
        sc_state, w_state, is_maintenance) = data

    tick = "✅" if (gc_state == sl_state == ms_state == States.NORMAL) else "❌"
    states = tuple(locale.get(state.l10n_key) for state in (gc_state, sl_state, ms_state, sc_state, w_state))

    game_servers_datetime = f'{format_datetime(gs_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    text = (
        f'{locale.game_status_text.format(tick, *states)}'
        f'\n\n'
        f'{locale.latest_data_update.format(game_servers_datetime)}'
    )

    if is_maintenance:
        text += f'\n\n{locale.valve_steam_maintenance_text}'

    return text


def format_matchmaking_stats(data, locale: Locale) -> str:
    if data is States.UNKNOWN:
        return locale.error_internal

    lang_code = get_refined_lang_code(locale)

    (gs_dt, *data, p_24h_peak, p_all_peak,
        monthly_unique_p, is_maintenance) = data

    game_servers_datetime = f'{format_datetime(gs_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    text = (
        f'{locale.stats_matchmaking_text.format(*data)}'
        f'\n\n'
        f'{locale.stats_additional.format(p_24h_peak, p_all_peak, monthly_unique_p)}'
        f'\n\n'
        f'{locale.latest_data_update.format(game_servers_datetime)}'
    )

    if is_maintenance:
        text += f'\n\n{locale.valve_steam_maintenance_text}'

    return text


def format_game_version_info(data, locale: Locale) -> str:
    if data is States.UNKNOWN:
        return locale.error_internal

    lang_code = get_refined_lang_code(locale)

    *data, cs2_version_dt = data

    cs2_version_dt = f'{format_datetime(cs2_version_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    return locale.game_version_text.format(*data, cs2_version_dt)


def format_valve_hq_time(locale: Locale) -> str:
    lang_code = get_refined_lang_code(locale)

    valve_hq_datetime = dt.datetime.now(tz=VALVE_TIMEZONE)

    valve_hq_dt_formatted = f'{format_datetime(valve_hq_datetime, "HH:mm:ss, dd MMM", locale=lang_code).title()} ' \
                            f'({valve_hq_datetime:%Z})'

    return locale.valve_hqtime_text.format(CLOCKS[valve_hq_datetime.hour % 12], valve_hq_dt_formatted)


def format_user_game_stats(stats, locale: Locale) -> str:
    rendered_page = game_stats_template.render(**locale.to_dict())

    # for some reason telegraph interprets newline <li></li> as two <li></li>, one of which is empty
    rendered_page = re.sub(r'\s*<li>\s*', '<li>', rendered_page)  # remove spaces before and after <li>
    rendered_page = re.sub(r'\s*</li>\s*', '</li>', rendered_page)  # remove spaces before and after </li>

    # with open(Path(__file__).parent.parent / 'rendered_game_stats.html', 'w', encoding='utf8') as file:
    #     file.write(rendered_page)

    return rendered_page.format(*stats)


def format_game_world_leaderboard(data: list[LeaderboardStats], locale: Locale) -> str:
    text = f'{locale.game_leaderboard_header_world}\n\n'
    link_text = locale.game_leaderboard_detailed_link.format(WEB_LEADERBOARD_LINK)

    if not data:
        text += f'{locale.data_not_found}\n\n{link_text}'
        return text

    for person in data:
        # telegram is shit that doesn't want to align text correctly
        text += f'`{person.rank:2d}.` `{person.name:<35} {person.rating:,}` {person.region}\n'

    text += f'\n{link_text}'
    return text


def format_game_regional_leaderboard(region: str, data: list[LeaderboardStats], locale: Locale) -> str:
    text = f'{locale.game_leaderboard_header_regional}\n\n'
    link = WEB_LEADERBOARD_LINK + f'?lb={WEB_LEADERBOARD_REGIONS.get(region, region)}'
    link_text = locale.game_leaderboard_detailed_link.format(link)

    if not data:
        text += f'{locale.data_not_found}\n\n{link_text}'
        return text

    for person in data:
        text += f'`{person.rank:2d}.` `{person.name:<35} {person.rating:,}`\n'

    text += f'\n{link_text}'
    return text
