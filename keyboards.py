# noinspection PyPep8Naming
from l10n import LocaleKeys as LK, get_available_languages

from utypes import ExtendedIKB, ExtendedIKM


# Back button
back_button = ExtendedIKB(LK.bot_back, selectable=False)

# Channel link for inline messages
inline_button_channel_link = ExtendedIKB(LK.bot_author_text, url=LK.bot_author_link)

markup_inline_button = ExtendedIKM([[inline_button_channel_link]])

# Ping button for specific log
log_ping_button = ExtendedIKB('Ping', 'log_ping')

log_ping_markup = ExtendedIKM([[log_ping_button]])

# Default
_server_stats = ExtendedIKB(LK.bot_servers_stats)
_profile_info = ExtendedIKB(LK.bot_profile_info)
_extra_features = ExtendedIKB(LK.bot_extras)
_settings = ExtendedIKB(LK.bot_settings)

main_markup = ExtendedIKM([
    [_server_stats],
    [_profile_info],
    [_extra_features],
    [_settings]
])

# Server Statistics
_server_status = ExtendedIKB(LK.game_status_button_title)
_matchmaking = ExtendedIKB(LK.stats_matchmaking_button_title)
_dc = ExtendedIKB(LK.dc_status_title)

ss_markup = ExtendedIKM([
    [_server_status],
    [_matchmaking],
    [_dc],
    [back_button]
])


# Profile Information
_profile_info = ExtendedIKB(LK.user_profileinfo_title)
_cs_stats = ExtendedIKB(LK.user_gamestats_button_title)

profile_markup = ExtendedIKM([
    [_profile_info],
    [_cs_stats],
    [back_button]
])

# Extra Features

_crosshair = ExtendedIKB(LK.crosshair)
_currency = ExtendedIKB(LK.exchangerate_button_title)
_valve_hq_time = ExtendedIKB(LK.valve_hqtime_button_title)
_timer = ExtendedIKB(LK.game_dropcap_button_title)
_game_version = ExtendedIKB(LK.game_version_button_title)
_leaderboard = ExtendedIKB(LK.game_leaderboard_button_title, selectable=False)
_guns = ExtendedIKB(LK.gun_button_text)

extra_markup = ExtendedIKM([
    [_crosshair, _currency, _game_version],
    [_valve_hq_time, _timer],
    [_leaderboard, _guns],
    [back_button]
])

# Settings

_language = ExtendedIKB(LK.settings_language_button_title)
settings_markup = ExtendedIKM([
    [_language],
    [back_button]
])

# DC

_europe = ExtendedIKB(LK.regions_europe)
_asia = ExtendedIKB(LK.regions_asia)
_africa = ExtendedIKB(LK.regions_africa)
_south_america = ExtendedIKB(LK.regions_southamerica)
_australia = ExtendedIKB(LK.regions_australia)
_us = ExtendedIKB(LK.dc_us)

dc_markup = ExtendedIKM([
    [_asia, _australia, _europe],
    [_africa, _south_america, _us],
    [back_button]
])

# DC Asia

_china = ExtendedIKB(LK.regions_china)
_emirates = ExtendedIKB(LK.dc_emirates)
_hongkong = ExtendedIKB(LK.dc_hongkong)
_india = ExtendedIKB(LK.dc_india)
_japan = ExtendedIKB(LK.dc_japan)
_singapore = ExtendedIKB(LK.dc_singapore)
_south_korea = ExtendedIKB(LK.dc_southkorea)

dc_asia_markup = ExtendedIKM([
    [_china, _emirates, _hongkong],
    [_india, _japan],
    [_singapore, _south_korea],
    [back_button]
])

# DC Europe

_austria = ExtendedIKB(LK.dc_austria)
_finland = ExtendedIKB(LK.dc_finland)
_germany = ExtendedIKB(LK.dc_germany)
_netherlands = ExtendedIKB(LK.dc_netherlands)
_poland = ExtendedIKB(LK.dc_poland)
_spain = ExtendedIKB(LK.dc_spain)
_sweden = ExtendedIKB(LK.dc_sweden)

dc_eu_markup = ExtendedIKM([
    [_austria, _finland, _germany],
    [_poland, _netherlands],
    [_spain, _sweden],
    [back_button]
])

# DC USA

_us_northwest = ExtendedIKB(LK.dc_north, LK.dc_us_north)
_us_southwest = ExtendedIKB(LK.dc_south, LK.dc_us_south)

dc_us_markup = ExtendedIKM([
    [_us_northwest, _us_southwest],
    [back_button]
])

# DC South America

_argentina = ExtendedIKB(LK.dc_argentina)
_brazil = ExtendedIKB(LK.dc_brazil)
_chile = ExtendedIKB(LK.dc_chile)
_peru = ExtendedIKB(LK.dc_peru)

dc_southamerica_markup = ExtendedIKM([
    [_argentina, _brazil],
    [_chile, _peru],
    [back_button]
])

# Guns

_pistols = ExtendedIKB(LK.gun_pistols)
_heavy = ExtendedIKB(LK.gun_heavy)
_smgs = ExtendedIKB(LK.gun_smgs)
_rifles = ExtendedIKB(LK.gun_rifles)

guns_markup = ExtendedIKM([
    [_pistols, _heavy],
    [_smgs, _rifles],
    [back_button]
])

# Pistols

_usps = ExtendedIKB("USP-S", "usps", translatable=False)
_p2000 = ExtendedIKB("P2000", "p2000", translatable=False)
_glock = ExtendedIKB("Glock-18", "glock18", translatable=False)
_dualies = ExtendedIKB("Dual Berettas", "dualberettas", translatable=False)
_p250 = ExtendedIKB("P250", "p250", translatable=False)
_cz75 = ExtendedIKB("CZ75-Auto", "cz75auto", translatable=False)
_five_seven = ExtendedIKB("Five-SeveN", "fiveseven", translatable=False)
_tec = ExtendedIKB("Tec-9", "tec9", translatable=False)
_deagle = ExtendedIKB("Desert Eagle", "deserteagle", translatable=False)
_r8 = ExtendedIKB("R8 Revolver", "r8revolver", translatable=False)

pistols_markup = ExtendedIKM([
    [_usps, _p2000, _glock],
    [_dualies, _p250],
    [_five_seven, _tec, _cz75],
    [_deagle, _r8],
    [back_button]
])

# Heavy

_nova = ExtendedIKB("Nova", "nova", translatable=False)
_xm1014 = ExtendedIKB("XM1014", "xm1014", translatable=False)
_mag7 = ExtendedIKB("MAG-7", "mag7", translatable=False)
_sawedoff = ExtendedIKB("Sawed-Off", "sawedoff", translatable=False)
_m249 = ExtendedIKB("M249", "m249", translatable=False)
_negev = ExtendedIKB("Negev", "negev", translatable=False)

heavy_markup = ExtendedIKM([
    [_nova, _xm1014],
    [_mag7, _sawedoff],
    [_m249, _negev],
    [back_button],
])

# SMGs

_mp9 = ExtendedIKB("MP9", "mp9", translatable=False)
_mac10 = ExtendedIKB("MAC-10", "mac10", translatable=False)
_mp7 = ExtendedIKB("MP7", "mp7", translatable=False)
_mp5 = ExtendedIKB("MP5-SD", "mp5sd", translatable=False)
_ump = ExtendedIKB("UMP-45", "ump45", translatable=False)
_p90 = ExtendedIKB("P90", "p90", translatable=False)
_pp = ExtendedIKB("PP-Bizon", "ppbizon", translatable=False)

smgs_markup = ExtendedIKM([
    [_mp9, _mac10],
    [_mp7, _mp5],
    [_ump, _p90, _pp],
    [back_button]
])

# Rifles

_famas = ExtendedIKB("FAMAS", "famas", translatable=False)
_galil = ExtendedIKB("Galil AR", "galilar", translatable=False)
_m4a4 = ExtendedIKB("M4A4", "m4a4", translatable=False)
_m4a1 = ExtendedIKB("M4A1-S", "m4a1s", translatable=False)
_ak = ExtendedIKB("AK-47", "ak47", translatable=False)
_aug = ExtendedIKB("AUG", "aug", translatable=False)
_sg = ExtendedIKB("SG 553", "sg553", translatable=False)
_ssg = ExtendedIKB("SSG 08", "ssg08", translatable=False)
_awp = ExtendedIKB("AWP", "awp", translatable=False)
_scar = ExtendedIKB("SCAR-20", "scar20", translatable=False)
_g3sg1 = ExtendedIKB("G3SG1", "g3sg1", translatable=False)

rifles_markup = ExtendedIKM([
    [_famas, _galil],
    [_m4a4, _m4a1, _ak],
    [_aug, _sg],
    [_ssg, _awp],
    [_scar, _g3sg1],
    [back_button]
])

# Leaderboard
_leaderboard_global = ExtendedIKB(LK.game_leaderboard_world)
_leaderboard_na = ExtendedIKB(LK.regions_northamerica)
_leaderboard_sa = ExtendedIKB(LK.regions_southamerica)
_leaderboard_eu = ExtendedIKB(LK.regions_europe)
_leaderboard_as = ExtendedIKB(LK.regions_asia)
_leaderboard_au = ExtendedIKB(LK.regions_australia)
_leaderboard_china = ExtendedIKB(LK.regions_china)
_leaderboard_af = ExtendedIKB(LK.regions_africa)

leaderboard_markup = ExtendedIKM([
    [_leaderboard_global],
    [_leaderboard_na, _leaderboard_sa],
    [_leaderboard_eu, _leaderboard_as],
    [_leaderboard_au, _leaderboard_af],
    [_leaderboard_china],
    [back_button]
])

# Crosshair
_generate_crosshair = ExtendedIKB(LK.crosshair_generate, LK.crosshair_generate)
_decode_crosshair = ExtendedIKB(LK.crosshair_decode, LK.crosshair_decode)

crosshair_markup = ExtendedIKM([
    [_generate_crosshair, _decode_crosshair],
    [back_button]
])

# Language
_available_langs = get_available_languages()
columns = 3

_language_buttons = []
_row = []
for lang_code, lang_name in _available_langs.items():
    _row.append(ExtendedIKB(lang_name, lang_code, translatable=False))
    if len(_row) == columns:
        _language_buttons.append(_row)  # yes, we append lists
        _row = []
if _row:
    _language_buttons.append(_row)

_language_buttons.append([back_button])

language_settings_markup = ExtendedIKM(_language_buttons)


all_selectable_markups = (ss_markup, extra_markup, dc_markup, dc_asia_markup, dc_eu_markup, dc_us_markup, dc_southamerica_markup,
                          pistols_markup, heavy_markup, smgs_markup, rifles_markup, language_settings_markup)
