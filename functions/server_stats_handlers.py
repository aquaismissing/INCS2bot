from babel.dates import format_datetime

from .locale import locale
from utypes import States


def get_server_status_summary(data, lang_code: str):
    loc = locale(lang_code)
    if data == States.UNKNOWN:
        return loc.error_internal
    gs_dt, gc_state, sl_state, ms_state, \
        sc_state, w_state, is_maintenance = data
    if gc_state == sl_state == ms_state == States.NORMAL:
        tick = "✅"
    else:
        tick = "❌"
    game_servers_datetime = f'{format_datetime(gs_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'
    gc_state = loc.get(gc_state.l10n_key)
    sl_state = loc.get(sl_state.l10n_key)
    ms_state = loc.get(ms_state.l10n_key)
    sc_state = loc.get(sc_state.l10n_key)
    w_state = loc.get(w_state.l10n_key)
    text = (
        f'{loc.game_status_text.format(tick, gc_state, sl_state, ms_state, sc_state, w_state)}'
        f'\n\n'
        f'{loc.latest_data_update.format(game_servers_datetime)}'
    )
    if is_maintenance:
        text += f'\n\n{loc.valve_steam_maintenance_text}'
    return text


def get_matchmaking_stats_summary(data, lang_code: str):
    loc = locale(lang_code)

    if data == States.UNKNOWN:
        return loc.error_internal

    gs_dt, *data, p_24h_peak, p_all_peak, monthly_unique_p, \
        is_maintenance = data

    players_stats = p_24h_peak, p_all_peak, monthly_unique_p

    game_servers_datetime = f'{format_datetime(gs_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'
    text = (
        f'{loc.stats_matchmaking_text.format(*data)}'
        f'\n\n'
        f'{loc.stats_additional.format(*players_stats)}'
        f'\n\n'
        f'{loc.latest_data_update.format(game_servers_datetime)}'
    )

    if is_maintenance:
        text += f'\n\n{loc.valve_steam_maintenance_text}'

    return text


def get_game_version_summary(data, lang_code: str):
    loc = locale(lang_code)

    if data == States.UNKNOWN:
        return loc.error_internal

    (csgo_patch_version, csgo_client_version, csgo_version_dt,
     cs2_patch_version, cs2_client_version, cs2_version_dt) = data

    csgo_version_dt = f'{format_datetime(csgo_version_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'
    cs2_version_dt = f'{format_datetime(cs2_version_dt, "HH:mm:ss, dd MMM", locale=lang_code).title()} (UTC)'

    data = (csgo_patch_version, csgo_client_version, csgo_version_dt,
            cs2_patch_version, cs2_client_version, cs2_version_dt)

    return loc.game_version_text.format(*data)
