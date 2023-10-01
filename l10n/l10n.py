from __future__ import annotations

import json
from pathlib import Path

from sl10n import SL10n, SLocale
from sl10n.pimpl import JSONImpl


__all__ = ('SL10n', 'Locale', 'LocaleKeys', 'locale', 'get_available_languages')


class Locale(SLocale):
    lang: str

    # bot
    bot_start_text: str
    bot_help_text: str
    bot_feedback_text: str
    bot_choose_cmd: str
    bot_choose_func: str
    bot_choose_setting: str
    bot_use_cancel: str
    bot_feedback_success: str
    bot_pmonly_text: str
    bot_back: str
    bot_loading: str
    bot_author_text: str
    bot_author_link: str
    bot_servers_stats: str
    bot_profile_info: str
    bot_extras: str
    bot_settings: str

    # crosshair
    crosshair: str
    crosshair_generate: str
    crosshair_decode: str
    crosshair_decode_example: str
    crosshair_decode_error: str
    crosshair_decode_result: str

    # currencies
    currencies_usd: str  # U.S. Dollar
    currencies_gbp: str  # British Pound
    currencies_eur: str  # Euro
    currencies_rub: str  # Russian Ruble
    currencies_brl: str  # Brazilian Real
    currencies_jpy: str  # Japanese Yen
    currencies_nok: str  # Norwegian Krone
    currencies_idr: str  # Indonesian Rupiah
    currencies_myr: str  # Malaysian Ringgit
    currencies_php: str  # Philippine Peso
    currencies_sgd: str  # Singapore Dollar
    currencies_thb: str  # Thai Baht
    currencies_vnd: str  # Vietnamese Dong
    currencies_krw: str  # South Korean Won
    currencies_try: str  # Turkish Lira
    currencies_uah: str  # Ukrainian Hryvnia
    currencies_mxn: str  # Mexican Peso
    currencies_cad: str  # Canadian Dollar
    currencies_aud: str  # Australian Dollar
    currencies_nzd: str  # New Zealand Dollar
    currencies_pln: str  # Polish Zloty
    currencies_chf: str  # Swiss Franc
    currencies_aed: str  # U.A.E. Dirham
    currencies_clp: str  # Chilean Peso
    currencies_cny: str  # Chinese Yuan
    currencies_cop: str  # Colombian Peso
    currencies_pen: str  # Peruvian Sol
    currencies_sar: str  # Saudi Riyal
    currencies_twd: str  # Taiwan Dollar
    currencies_hkd: str  # Hong Kong Dollar
    currencies_zar: str  # South African Rand
    currencies_inr: str  # Indian Rupee
    currencies_ars: str  # Argentine Peso
    currencies_crc: str  # Costa Rican Colon
    currencies_ils: str  # Israeli Shekel
    currencies_kwd: str  # Kuwaiti Dinar
    currencies_qar: str  # Qatari Riyal
    currencies_uyu: str  # Uruguayan Peso
    currencies_kzt: str  # Kazakhstani Tenge

    currencies_tags: str  # EUR (tags: euro, евро)

    # datacenters
    dc_status_title: str
    dc_status_inline_description: str
    dc_status_choose_region: str
    dc_status_specify_region: str
    dc_status_specify_country: str
    dc_status_text_title: str
    dc_status_text_summary: str
    dc_status_text_summary_city: str

    dc_north: str  # North
    dc_south: str  # South
    dc_west: str  # West
    dc_east: str  # East

    dc_africa_title: str  # South Africaʼs DC
    dc_africa_inline_title: str  # African DC
    dc_africa_johannesburg: str  # Johannesburg

    dc_australia_title: str  # Australiaʼs DC
    dc_australia_inline_title: str  # Australian DC
    dc_australia_sydney: str  # Sydney

    dc_eu_north: str  # North
    dc_eu_west: str  # West
    dc_eu_east: str  # East
    dc_eu_north_inline_title: str  # North European DC
    dc_sweden_title: str  # Swedenʼs DC
    dc_sweden_stockholm: str  # Stockholm
    dc_eu_west_inline_title: str  # West European DC
    dc_germany_title: str  # Germanyʼs DC
    dc_germany_frankfurt: str  # Frankfurt
    dc_spain_title: str  # Spainʼs DC
    dc_spain_madrid: str  # Madrid
    dc_eu_east_inline_title: str  # East European DC
    dc_austria_title: str  # Austriaʼs DC
    dc_austria_vienna: str  # Vienna
    dc_poland_title: str  # Polandʼs DC
    dc_poland_warsaw: str  # Warsaw

    dc_us: str  # USA
    dc_us_north: str  # North
    dc_us_south: str  # South
    dc_us_north_inline_title: str  # Northern USA DC
    dc_us_north_central_title: str  # Northcentral DC
    dc_us_north_central_chicago: str  # Chicago
    dc_us_north_east_title: str  # Northeast DC
    dc_us_north_east_sterling: str  # Sterling
    dc_us_north_west_title: str  # Northwest DC
    dc_us_north_west_moses_lake: str  # Moses Lake
    dc_us_south_inline_title: str  # Southern USA DC
    dc_us_south_east_title: str  # Southeast DC
    dc_us_south_east_atlanta: str  # Atlanta
    dc_us_south_west_title: str  # Southwest DC
    dc_us_south_west_los_angeles: str  # Los Angeles

    dc_southamerica_inline_title: str  # South American DC
    dc_brazil_title: str  # Brazilʼs DC
    dc_brazil_sao_paulo: str  # Sao Paulo
    dc_chile_title: str  # Chileʼs DC
    dc_chile_santiago: str  # Santiago
    dc_peru_title: str  # Peruʼs DC
    dc_peru_lima: str  # Lima
    dc_argentina_title: str  # Argentinaʼs DC
    dc_argentina_buenos_aires: str  # Buenos Aires

    dc_india: str  # India
    dc_india_title: str  # Indiaʼs DC
    dc_india_inline_title: str  # Indian DC
    dc_india_mumbai: str  # Mumbai
    dc_india_chennai: str  # Chennai
    dc_japan: str  # Japan
    dc_japan_title: str  # Japanʼs DC
    dc_japan_inline_title: str  # Japanese DC
    dc_japan_tokyo: str  # Tokyo

    dc_china_title: str  # Chinaʼs DC
    dc_china_inline_title: str  # Chinese DC
    dc_china_shanghai: str  # Shanghai
    dc_china_tianjin: str  # Tianjin
    dc_china_guangzhou: str  # Guangzhou
    dc_emirates: str  # Emirates
    dc_emirates_title: str  # Emiratesʼ DC
    dc_emirates_inline_title: str  # Emirati DC
    dc_emirates_dubai: str  # Dubai
    dc_singapore: str  # Singapore
    dc_singapore_title: str  # Singaporeʼs DC
    dc_singapore_inline_title: str  # Singaporean DC
    dc_hongkong: str  # Hong Kong
    dc_hongkong_title: str  # Hong Kongʼs DC
    dc_hongkong_inline_title: str  # Hong Kongese DC
    dc_southkorea: str  # South Korea
    dc_southkorea_title: str  # South Koreaʼs DC
    dc_southkorea_inline_title: str  # South Korean DC
    dc_southkorea_seoul: str  # Seoul

    # errors
    error_internal: str
    error_unknownrequest: str
    error_wip: str
    error_session_timeout: str

    # exchange rate
    exchangerate_button_title: str
    exchangerate_text: str

    exchangerate_inline_title: str
    exchangerate_inline_description: str
    exchangerate_inline_text_default: str
    exchangerate_inline_title_selected: str
    exchangerate_inline_description_selected: str
    exchangerate_inline_text_selected: str
    exchangerate_inline_title_notfound: str
    exchangerate_inline_description_notfound: str

    # game info
    game_status_button_title: str
    game_status_inline_title: str
    game_status_inline_description: str
    game_status_text: str

    game_version_button_title: str
    game_version_inline_title: str
    game_version_inline_description: str
    game_version_text: str

    game_dropcap_button_title: str
    game_dropcaptimer_inline_title: str
    game_dropcaptimer_inline_description: str
    game_dropcaptimer_text: str

    game_leaderboard_button_title: str
    game_leaderboard_world: str
    game_leaderboard_header_world: str
    game_leaderboard_header_regional: str

    # guns info
    gun_button_text: str
    gun_select_category: str
    gun_pistols: str
    gun_select_pistol: str
    gun_heavy: str
    gun_select_heavy: str
    gun_smgs: str
    gun_select_smg: str
    gun_rifles: str
    gun_select_rifle: str
    gun_summary_text: str

    gun_origin_germany: str  # Germany
    gun_origin_austria: str  # Austria
    gun_origin_italy: str  # Italy
    gun_origin_switzerland: str  # Switzerland
    gun_origin_czech_republic: str  # Czech Republic
    gun_origin_belgium: str  # Belgium
    gun_origin_sweden: str  # Sweden
    gun_origin_israel: str  # Israel
    gun_origin_us: str  # United States
    gun_origin_russia: str  # Russia
    gun_origin_france: str  # France
    gun_origin_uk: str  # United Kingdom
    gun_origin_south_africa: str  # South Africa

    # data
    latest_data_update: str
    data_not_found: str

    # notifications (currently not used)
    notifs_build_public: str
    notifs_build_dpr: str
    notifs_build_dprp: str
    notifs_build_sdk: str
    notifs_build_ds: str
    notifs_build_valve_ds: str
    notifs_build_cs2_client: str
    notifs_build_cs2_server: str
    notifs_new_map: str
    notifs_new_map_multiple: str
    notifs_new_playerspeak: str
    notifs_new_monthlyunique: str

    # regions (used across the bot)
    regions_africa: str  # South Africa
    regions_asia: str  # Asia
    regions_australia: str  # Australia
    regions_china: str  # China
    regions_europe: str  # Europe
    regions_northamerica: str  # North America
    regions_southamerica: str  # South America

    # states (used in dc and stats)
    states_low: str
    states_medium: str
    states_high: str
    states_full: str
    states_normal: str
    states_surge: str
    states_delayed: str
    states_idle: str
    states_offline: str
    states_critical: str
    states_internal_server_error: str
    states_internal_bot_error: str
    states_reloading: str
    states_internal_steam_error: str
    states_unknown: str

    # stats
    stats_matchmaking_button_title: str
    stats_matchmaking_inline_title: str
    stats_matchmaking_inline_description: str
    stats_matchmaking_text: str
    stats_additional: str

    # steam
    steam_url_example: str

    # settings
    settings_language_button_title: str
    settings_language_choose: str

    # user stats
    user_gamestats_button_title: str
    user_gamestats_inline_title: str
    user_gamestats_page_title: str  # Statistics for #{}

    user_gamestats_generated_with: str
    user_gamestats_header: str
    user_gamestats_playtime: str
    user_gamestats_kills: str
    user_gamestats_deaths: str
    user_gamestats_kd_ratio: str
    user_gamestats_matches_played: str
    user_gamestats_matches_won: str
    user_gamestats_win_percentage: str
    user_gamestats_rounds_played: str
    user_gamestats_pistol_rounds_won: str
    user_gamestats_aim_stats: str
    user_gamestats_shots: str
    user_gamestats_hits: str
    user_gamestats_aim_accuracy: str
    user_gamestats_hs_percentage: str
    user_gamestats_maps_stats: str
    user_gamestats_best_map: str
    user_gamestats_misc_stats: str
    user_gamestats_mvp_rewards: str
    user_gamestats_total_income: str
    user_gamestats_hostages_rescued: str
    user_gamestats_weapons_dropped: str
    user_gamestats_windows_broken: str
    user_gamestats_dealt_damage: str
    user_gamestats_bombs_planted: str
    user_gamestats_bombs_defused: str
    user_gamestats_knife_kills: str
    user_gamestats_grenade_kills: str
    user_gamestats_molotov_kills: str
    user_gamestats_zeus_shots: str
    user_gamestats_zeus_kills: str
    user_gamestats_zeus_aim_accuracy: str
    user_gamestats_knife_fights_won: str
    user_gamestats_enemy_weapon_kills: str
    user_gamestats_flashed_enemies_kills: str
    user_gamestats_scoped_snipers_kills: str
    user_gamestats_gun_stats: str
    user_gamestats_pistols_stats: str
    user_gamestats_heavy_stats: str
    user_gamestats_smgs_stats: str
    user_gamestats_rifles_stats: str
    user_gamestats_snipers_stats: str

    user_gamestats_share: str
    user_invalidlink_error: str
    user_invalidrequest_error: str
    user_telegraph_error: str
    user_privateprofile_error: str
    user_profileinfo_title: str
    user_profileinfo_text: str
    user_profileinfo_notset: str
    user_profileinfo_notfound: str
    user_profileinfo_none: str
    user_profileinfo_banned: str

    # valve
    valve_hqtime_button_title: str
    valve_hqtime_inline_title: str
    valve_hqtime_inline_description: str
    valve_hqtime_text: str

    valve_steam_maintenance_text: str


LocaleKeys: Locale = Locale.sample()

_l10n = SL10n(Locale, Path(__file__).parent / 'data', ignore_filenames=['tags'],
              parsing_impl=JSONImpl(json, indent=4, ensure_ascii=False))  # SL10n singleton for fast lookups


def locale(lang: str = None) -> Locale:
    """
    Initializes a L10n singleton and returns a Locale object, containing
    all defined string keys translated to the requested language
    (if such translation exists, otherwise returns English 'en').

    Useful for fast Locale object creation.
    """

    if not _l10n.initialized:
        _l10n.init()
    return _l10n.locale(lang)


def get_available_languages() -> dict[str, str]:
    """
    Initializes a L10n singleton and returns a dictionary with lang codes (access keys, not overriden!)
    as keys and lang names as values.
    """

    if not _l10n.initialized:
        _l10n.init()
    return {lang_code: container.lang for lang_code, container in _l10n.locales.items()}


if __name__ == '__main__':
    _l10n.init()
