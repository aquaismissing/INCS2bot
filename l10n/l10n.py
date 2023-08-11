from __future__ import annotations
import json  # todo: json5 for multiline strings instead of lists?
import logging
from pathlib import Path
from typing import NamedTuple
import warnings


__all__ = ('Locale', 'L10n', 'locale', 'LocaleKeys')


_l10n = None  # L10n singleton for fast lookups

logger = logging.getLogger('l10n')
logger.formatter = logging.Formatter("%(asctime)s | L10n: %(message)s", "%H:%M:%S — %d/%m/%Y")


class UnexpectedLocaleKey(UserWarning):
    pass


class UndefinedLocaleKey(UserWarning):
    pass


class PrimaryLangFileNotFound(UserWarning):
    pass


class Locale(NamedTuple):
    """Object containing all the localization strings. All strings
       can be accessed as object attributes or by string keys using
       get(key) method. Can be converted to dict using to_dict() method."""
    # bot
    bot_start_text: str
    bot_help_text: str
    bot_feedback_text: str
    bot_choose_cmd: str
    bot_choose_func: str
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

    dc_africa: str  # South Africa
    dc_africa_title: str  # South Africaʼs DC
    dc_africa_inline_title: str  # African DC
    dc_africa_johannesburg: str  # Johannesburg

    dc_australia: str  # Australia
    dc_australia_title: str  # Australiaʼs DC
    dc_australia_inline_title: str  # Australian DC
    dc_australia_sydney: str  # Sydney

    dc_europe: str  # Europe
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

    dc_southamerica: str  # South America
    dc_southamerica_inline_title: str  # South American DC
    dc_brazil_title: str  # Brazilʼs DC
    dc_brazil_sao_paulo: str  # Sao Paulo
    dc_chile_title: str  # Chileʼs DC
    dc_chile_santiago: str  # Santiago
    dc_peru_title: str  # Peruʼs DC
    dc_peru_lima: str  # Lima
    dc_argentina_title: str  # Argentinaʼs DC
    dc_argentina_buenos_aires: str  # Buenos Aires

    dc_asia: str  # Asia
    dc_india: str  # India
    dc_india_title: str  # Indiaʼs DC
    dc_india_inline_title: str  # Indian DC
    dc_india_mumbai: str  # Mumbai
    dc_india_chennai: str  # Chennai
    dc_japan: str  # Japan
    dc_japan_title: str  # Japanʼs DC
    dc_japan_inline_title: str  # Japanese DC
    dc_japan_tokyo: str  # Tokyo
    dc_china: str  # China
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

    # latest data update
    latest_data_update: str

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

    # user stats
    user_gamestats_button_title: str
    user_gamestats_inline_title: str
    user_gamestats_page_title: str  # Statistics for #{}
    user_gamestats_text: str
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

    @classmethod
    def sample(cls) -> Locale:
        """Returns a sample Locale object with key names as values"""

        return cls(**{field: field for field in cls._fields})

    def to_dict(self) -> dict[str, str]:
        """Returns a dict converted from a Locale object."""

        return self._asdict()

    def get(self, key: str) -> str:
        """
        Returns a string associated with the given key
        (if such key exists, otherwise returns the key itself).
        """

        if key not in self._fields:
            warnings.warn(f'Got unexpected key "{key}", returned the key', UnexpectedLocaleKey, stacklevel=2)
            return key
        return getattr(self, key)


LocaleKeys = Locale.sample()


class L10n:
    """Simple text localization system."""

    _reserved_fields = ('l10n_redump',)

    def __init__(self, path: str | Path = None):
        self.path = Path(path) if path else Path(__file__).parent
        if not (self.path / 'en.json').exists():
            warnings.warn(f"Can't find English in locales, generating a file...", PrimaryLangFileNotFound)
            L10n.create_lang_file(self.path, 'en')

        self.locales = {}
        self._define_locales()

    def _define_locales(self):
        """Finds all lang files to make Locales."""

        for file in self.path.glob('*.json'):
            if file.stem == 'tags':
                continue
            self.locales[file.stem] = self._get_locale(file)

    @classmethod
    def _get_locale(cls, file: Path):
        """Creates a Locale object from lang file and stores it in memory."""

        lang = file.stem
        if lang == 'tags':
            return

        with open(file, encoding='utf-8') as f:
            data = json.load(f)

        # Add undefined keys
        found_undefined_keys = False
        for key in Locale._fields:
            if key not in data and key not in cls._reserved_fields:
                warnings.warn(f'Found undefined key "{key}" in "{file}"', UndefinedLocaleKey, stacklevel=4)
                data[key] = key
                found_undefined_keys = True

        used_reserved_fields = []
        for field in cls._reserved_fields:
            if field in data:
                used_reserved_fields.append(field)

        redump = data.get('l10n_redump')  # explicitly tells the parser to redump a file

        # Find unexpected keys
        unexpected_keys = []
        for key in tuple(data):
            if key not in Locale._fields and key not in cls._reserved_fields:
                warnings.warn(f'Got unexpected key "{key}" in "{file}"', UnexpectedLocaleKey, stacklevel=4)
                unexpected_keys.append(key)

        # Dump data with undefined and unexpected keys
        if found_undefined_keys or unexpected_keys or redump:
            if redump:
                logger.info(f'Redumping {file.name}...')
            with open(file, 'w', encoding='utf-8') as f:
                data = {key: data[key] for key in Locale._fields + tuple(used_reserved_fields)
                        + tuple(unexpected_keys)}  # fixing pairs order
                json.dump(data, f, indent=4, ensure_ascii=False)

        # Remove unexpected keys
        for key in tuple(unexpected_keys) + cls._reserved_fields:
            if key in data:
                del data[key]

        # Concat strings from lists with '\n'
        for key, val in data.items():
            if isinstance(val, list):
                data[key] = '\n'.join(val)

        return Locale(**data)

    def locale(self, lang: str = 'en') -> Locale:
        """
        Returns a Locale object, containing all defined string keys translated to the requested language
        (if such translation exists, otherwise returns English).
        """

        if self.locales.get(lang) is None:
            warnings.warn(f'Got unexpected lang "{lang}", returned "en"', UnexpectedLocaleKey, stacklevel=2)
            lang = 'en'

        return self.locales.get(lang)

    @classmethod
    def create_lang_file(cls, path: str | Path, lang: str, override: bool = False):
        """
        Creates a sample lang file in a requested path.
        If you want to override existing file - set 'override' to True.

        Useful for fast lang file creation.
        """

        if (Path(path) / 'en.json').exists():
            sample = cls._get_locale(Path(path) / 'en.json')
        else:
            sample = Locale.sample()

        path = Path(path) / f'{lang}.json'
        if override is False and path.exists():
            warnings.warn(f'Lang file "{path}" already exists.', stacklevel=2)
            return

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(sample.to_dict(), f, indent=4, ensure_ascii=False)


def locale(lang: str = None) -> Locale:
    """
    Creates a L10n singleton and returns a Locale object, containing
    all defined string keys translated to the requested language
    (if such translation exists, otherwise returns English 'en').

    Useful for fast Locale object creation.
    """

    global _l10n

    if _l10n is None:
        _l10n = L10n(Path(__file__).parent / 'data')
    return _l10n.locale(lang)


if __name__ == '__main__':
    L10n('data')
