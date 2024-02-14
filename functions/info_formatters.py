import datetime as dt
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from babel.dates import format_datetime
from jinja2 import Environment, FileSystemLoader

from l10n import Locale
from .locale import get_refined_lang_code
from utypes import GameVersionData, ServerStatusData, MatchmakingStatsData, States, LeaderboardStats


MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
MONTH = 30 * DAY
YEAR = 365 * DAY


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


def format_timedelta(td: dt.timedelta) -> str:
    time_elapsed = int(td.total_seconds())

    time_elapsed_strf = []
    if (elapsed_years := time_elapsed // YEAR) != 0:
        time_elapsed_strf.append(f'{elapsed_years} {"year" if elapsed_years == 1 else "years"}')
    if (elapsed_months := time_elapsed % YEAR // MONTH) != 0:
        time_elapsed_strf.append(f'{elapsed_months} {"month" if elapsed_months == 1 else "months"}')
    if (elapsed_days := time_elapsed % MONTH // DAY) != 0:
        time_elapsed_strf.append(f'{elapsed_days} {"day" if elapsed_days == 1 else "days"}')
    if (elapsed_hours := time_elapsed % DAY // HOUR) != 0:
        time_elapsed_strf.append(f'{elapsed_hours} {"hour" if elapsed_hours == 1 else "hours"}')
    if (elapsed_minutes := time_elapsed % HOUR // MINUTE) != 0:
        time_elapsed_strf.append(f'{elapsed_minutes} {"minute" if elapsed_minutes == 1 else "minutes"}')
    elapsed_seconds = time_elapsed % MINUTE // 1
    time_elapsed_strf.append(f'{elapsed_seconds} {"second" if elapsed_seconds == 1 else "seconds"}')

    if len(time_elapsed_strf) > 1:
        time_elapsed_strf = time_elapsed_strf[:-2] + [" and ".join(time_elapsed_strf[-2:])]

    return f'{"~" if elapsed_years or elapsed_months else ""}{", ".join(time_elapsed_strf)}'


def format_server_status(data: ServerStatusData, locale: Locale) -> str:
    if data is States.UNKNOWN:
        return locale.error_internal

    lang_code = get_refined_lang_code(locale)

    tick = '✅' if (data.game_coordinator_state == data.sessions_logon_state
                   == data.matchmaking_scheduler_state == States.NORMAL) else '❌'
    states = tuple(locale.get(state.l10n_key) for state in (data.game_coordinator_state,
                                                            data.sessions_logon_state,
                                                            data.matchmaking_scheduler_state,
                                                            data.steam_community_state,
                                                            data.webapi_state))

    game_servers_dt = data.info_requested_datetime
    game_servers_dt = f'{format_datetime(game_servers_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    text = (
        f'<blockquote>Currently we\'re unable to detect CS2\'s game coordinator status, '
        f'because one of our dependencies is broken. Please, accept our apologies.</blockquote>'
        f'\n\n'
        f'{locale.game_status_text.format(tick, *states)}'
        f'\n\n'
        f'{locale.latest_data_update.format(game_servers_dt)}'
    )

    if data.is_maintenance():
        text += f'\n\n{locale.valve_steam_maintenance_text}'

    return text


def format_matchmaking_stats(data: MatchmakingStatsData, locale: Locale) -> str:
    if data is States.UNKNOWN:
        return locale.error_internal

    lang_code = get_refined_lang_code(locale)

    game_servers_dt = data.info_requested_datetime
    game_servers_dt = f'{format_datetime(game_servers_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    packed = (data.graph_url, data.online_servers, data.online_players,
              data.active_players, data.searching_players, data.average_search_time)
    text = (
        f'{locale.stats_matchmaking_text.format(*packed)}'
        f'\n\n'
        f'{locale.stats_additional.format(data.player_24h_peak, data.player_alltime_peak, data.monthly_unique_players)}'
        f'\n\n'
        f'{locale.latest_data_update.format(game_servers_dt)}'
    )

    if data.is_maintenance():
        text += f'\n\n{locale.valve_steam_maintenance_text}'

    return text


def format_game_version_info(data: GameVersionData, locale: Locale) -> str:
    lang_code = get_refined_lang_code(locale)

    cs2_version_dt = (dt.datetime.fromtimestamp(data.cs2_version_timestamp)
                      .replace(tzinfo=VALVE_TIMEZONE).astimezone(dt.UTC))

    cs2_version_dt = f'{format_datetime(cs2_version_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    return locale.game_version_text.format(data.cs2_patch_version, data.cs2_client_version, cs2_version_dt)


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
        name = person.name.replace('`', r"'")  # escape for formatting
        name_span_limit = 19
        if len(name) > name_span_limit:
            name = name[:name_span_limit - 2] = '...'
        text += f'`{person.rank:2d}.` `{name:<{name_span_limit}}` `{person.rating:>6,}` `{person.region}`\n'

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
        name = person.name.replace('`', r"'")  # escape for formatting
        name_span_limit = 21
        if len(name) > name_span_limit:
            name = name[:name_span_limit - 2] = '...'
        text += f'`{person.rank:2d}.` `{name:<{name_span_limit}}` `{person.rating:>6,}`\n'

    text += f'\n{link_text}'
    return text
