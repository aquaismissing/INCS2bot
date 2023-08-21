import datetime as dt
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from babel.dates import format_datetime
from jinja2 import Environment, FileSystemLoader

from .locale import locale
from l10n import Locale
from utypes import States


VALVE_TIMEZONE = ZoneInfo('America/Los_Angeles')
CLOCKS = ('🕛', '🕐', '🕑', '🕒', '🕓', '🕔',
          '🕕', '🕖', '🕗', '🕘', '🕙', '🕚')

env = Environment(loader=FileSystemLoader(Path(__file__).parent.parent))
game_stats_template = env.get_template('game_stats_template.html')


def format_server_status(data, lang_code: str):
    loc = locale(lang_code)
    if data is States.UNKNOWN:
        return loc.error_internal

    (gs_dt, gc_state, sl_state, ms_state,
        sc_state, w_state, is_maintenance) = data

    tick = "✅" if (gc_state == sl_state == ms_state == States.NORMAL) else "❌"

    gc_state = loc.get(gc_state.l10n_key)
    sl_state = loc.get(sl_state.l10n_key)
    ms_state = loc.get(ms_state.l10n_key)
    sc_state = loc.get(sc_state.l10n_key)
    w_state = loc.get(w_state.l10n_key)

    game_servers_datetime = f'{format_datetime(gs_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    text = (
        f'{loc.game_status_text.format(tick, gc_state, sl_state, ms_state, sc_state, w_state)}'
        f'\n\n'
        f'{loc.latest_data_update.format(game_servers_datetime)}'
    )

    if is_maintenance:
        text += f'\n\n{loc.valve_steam_maintenance_text}'

    return text


def format_matchmaking_stats(data, lang_code: str):
    loc = locale(lang_code)

    if data is States.UNKNOWN:
        return loc.error_internal

    (gs_dt, *data, p_24h_peak, p_all_peak,
        monthly_unique_p, is_maintenance) = data

    game_servers_datetime = f'{format_datetime(gs_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    text = (
        f'{loc.stats_matchmaking_text.format(*data)}'
        f'\n\n'
        f'{loc.stats_additional.format(p_24h_peak, p_all_peak, monthly_unique_p)}'
        f'\n\n'
        f'{loc.latest_data_update.format(game_servers_datetime)}'
    )

    if is_maintenance:
        text += f'\n\n{loc.valve_steam_maintenance_text}'

    return text


def format_game_version_info(data, lang_code: str):
    loc = locale(lang_code)

    if data is States.UNKNOWN:
        return loc.error_internal

    (*data, cs2_version_dt) = data

    cs2_version_dt = f'{format_datetime(cs2_version_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    return loc.game_version_text.format(*data, cs2_version_dt)


def format_valve_hq_time(lang_code: str):
    loc = locale(lang_code)

    valve_hq_datetime = dt.datetime.now(tz=VALVE_TIMEZONE)

    valve_hq_dt_formatted = f'{format_datetime(valve_hq_datetime, "HH:mm:ss, dd MMM", locale=lang_code).title()} ' \
                            f'({valve_hq_datetime:%Z})'

    return loc.valve_hqtime_text.format(CLOCKS[valve_hq_datetime.hour % 12], valve_hq_dt_formatted)


def format_user_game_stats(stats, _locale: Locale):
    rendered_page = game_stats_template.render(**_locale.to_dict())

    # for some reason telegraph interprets newline <li></li> as two <li></li>, one of which is empty
    rendered_page = re.sub(r'\s*<li>\s*', '<li>', rendered_page)  # remove spaces before and after <li>
    rendered_page = re.sub(r'\s*</li>\s*', '</li>', rendered_page)  # remove spaces before and after </li>

    # with open(Path(__file__).parent.parent / 'rendered_game_stats.html', 'w', encoding='utf8') as file:
    #     file.write(rendered_page)

    return rendered_page.format(*stats)
