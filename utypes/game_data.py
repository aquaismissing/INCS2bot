import datetime as dt
import json
from typing import NamedTuple

import requests

import config
from .states import State, States


__all__ = ('GameVersionData',  'ExchangeRate', 'GameServersData',
           'get_monthly_unique_players', 'drop_cap_reset_timer')


MONTHLY_UNIQUE_PLAYERS_API = "https://api.steampowered.com/ICSGOServers_730/GetMonthlyPlayerCount/v1"
CSGO_VERSION_DATA_URL = "https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo/steam.inf"
CS2_VERSION_DATA_URL = "https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/game/csgo/steam.inf"
GET_KEY_PRICES_API = f"https://api.steampowered.com/ISteamEconomy/GetAssetPrices/v1/?appid={config.CS_APP_ID}" \
                     f"&key={config.STEAM_API_KEY}"
GAME_SERVERS_STATUS_API = f"https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1" \
                          f"?key={config.STEAM_API_KEY}"

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0"}

MINUTE = 60
HOUR = 60 * MINUTE


class GameVersionData(NamedTuple):
    csgo_client_version: int
    csgo_server_version: int
    csgo_patch_version: str
    csgo_version_timestamp: float
    cs2_client_version: int
    cs2_server_version: int
    cs2_patch_version: str
    cs2_version_timestamp: float

    @staticmethod
    def request():
        # noinspection PyArgumentList
        options = {}

        # csgo
        csgo_data = requests.get(CSGO_VERSION_DATA_URL, headers=HEADERS, timeout=15).text
        config_entries = (line for line in csgo_data.split('\n') if line)

        for entry in config_entries:
            key, val = entry.split('=')
            options[key] = val

        version_datetime = f'{options["VersionDate"]} {options["VersionTime"]}'

        csgo_client_version = int(options["ClientVersion"])
        csgo_server_version = int(options["ServerVersion"])
        csgo_patch_version = options["PatchVersion"]
        csgo_version_timestamp = dt.datetime.strptime(version_datetime, "%b %d %Y %H:%M:%S").timestamp()

        # cs2
        cs2_data = requests.get(CS2_VERSION_DATA_URL, headers=HEADERS, timeout=15).text
        config_entries = (line for line in cs2_data.split('\n') if line)

        for entry in config_entries:
            key, val = entry.split('=')
            options[key] = val

        version_datetime = f'{options["VersionDate"]} {options["VersionTime"]}'

        cs2_client_version = int(options["ClientVersion"]) - 2000000
        cs2_server_version = int(options["ServerVersion"]) - 2000000
        cs2_patch_version = options["PatchVersion"]
        cs2_version_timestamp = dt.datetime.strptime(version_datetime, "%b %d %Y %H:%M:%S").timestamp()

        return GameVersionData(csgo_client_version,
                               csgo_server_version,
                               csgo_patch_version,
                               csgo_version_timestamp,
                               cs2_client_version,
                               cs2_server_version,
                               cs2_patch_version,
                               cs2_version_timestamp)
    
    @staticmethod
    def cached_data():
        """Get the version of the game"""

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)
        
        csgo_client_version = cache_file["csgo_client_version"]
        csgo_patch_version = cache_file["csgo_patch_version"]
        csgo_version_dt = (dt.datetime.fromtimestamp(cache_file["csgo_version_timestamp"], dt.UTC)
                           + dt.timedelta(hours=8))

        cs2_client_version = cache_file["cs2_client_version"]
        cs2_patch_version = cache_file["cs2_patch_version"]
        cs2_version_dt = (dt.datetime.fromtimestamp(cache_file["cs2_version_timestamp"], dt.UTC)
                          + dt.timedelta(hours=8))

        return (csgo_patch_version, csgo_client_version, csgo_version_dt,
                cs2_patch_version, cs2_client_version, cs2_version_dt)

    def asdict(self):
        return self._asdict()


class ExchangeRate:
    __slots__ = ()
    currencies_symbols = {"USD": "$", "GBP": "£", "EUR": "€", "RUB": "₽",
                          "BRL": "R$", "JPY": "¥", "NOK": "kr", "IDR": "Rp",
                          "MYR": "RM", "PHP": "₱", "SGD": "S$", "THB": "฿",
                          "VND": "₫", "KRW": "₩", "TRY": "₺", "UAH": "₴",
                          "MXN": "Mex$", "CAD": "CDN$", "AUD": "A$",
                          "NZD": "NZ$", "PLN": "zł", "CHF": "CHF", "AED": "AED",
                          "CLP": "CLP$", "CNY": "¥", "COP": "COL$", "PEN": "S/.",
                          "SAR": "SR", "TWD": "NT$", "HKD": "HK$", "ZAR": "R",
                          "INR": "₹", "ARS": "ARS$", "CRC": "₡", "ILS": "₪",
                          "KWD": "KD", "QAR": "QR", "UYU": "$U", "KZT": "₸"}

    @staticmethod
    def request():
        r = requests.get(GET_KEY_PRICES_API, timeout=15).json()['result']['assets']
        key_price = [item for item in r if item['classid'] == '1544098059'][0]["prices"]
        del key_price["Unknown"], key_price["BYN"]

        return key_price

    @staticmethod
    def cached_data():
        """Get the currencies for CS2 store"""

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            key_price = json.load(f)["key_price"]

        prices = {k: v / 100 for k, v in key_price.items()}
        formatted_prices = {k: f'{v:.0f}' if v % 1 == 0 else f'{v:.2f}'
                            for k, v in prices.items()}

        return formatted_prices
    

class GameServersData(NamedTuple):
    webapi: State
    api_timestamp: int
    sessions_logon: State
    steam_community: State
    matchmaking_scheduler: State
    online_servers: int
    active_players: int
    searching_players: int
    average_search_time: int
    datacenters: dict

    @staticmethod
    def request():
        response = requests.get(GAME_SERVERS_STATUS_API, timeout=15)
        if response.status_code == 200:
            webapi = States.NORMAL

            result = response.json()["result"]
            api_timestamp = result["app"]["timestamp"]
            sessions_logon = States.get(result["services"]["SessionsLogon"])
            steam_community = States.get(result["services"]["SteamCommunity"])
            matchmaking_scheduler = States.get(result["matchmaking"]["scheduler"])
            online_servers = result["matchmaking"]["online_servers"]
            active_players = result["matchmaking"]["online_players"]
            searching_players = result["matchmaking"]["searching_players"]
            average_search_time = result["matchmaking"]["search_seconds_avg"]
            datacenters = result["datacenters"]
            return GameServersData(webapi,
                                   api_timestamp,
                                   sessions_logon,
                                   steam_community,
                                   matchmaking_scheduler,
                                   online_servers,
                                   active_players,
                                   searching_players,
                                   average_search_time,
                                   datacenters)
        return GameServersData(States.UNKNOWN, 0, States.UNKNOWN,
                               States.UNKNOWN, States.UNKNOWN, 0,
                               0, 0, 0, {})

    @staticmethod
    def cached_server_status():
        """Get the status of Counter-Strike servers"""

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)

        if cache_file["api_timestamp"] == 'unknown':
            return States.UNKNOWN
        
        game_server_dt = dt.datetime.fromtimestamp(cache_file["api_timestamp"], dt.UTC)
        gc_state = States.get(cache_file["game_coordinator"])
        sl_state = States.get(cache_file["sessions_logon"])
        ms_state = States.get(cache_file["matchmaking_scheduler"])
        sc_state = States.get(cache_file["steam_community"])
        webapi_state = States.get(cache_file["webapi"])
        
        now = dt.datetime.now(dt.UTC)
        is_maintenance = ((now.weekday() == 1 and now.hour > 21) or (now.weekday() == 2 and now.hour < 4)) \
            and not (gc_state == States.NORMAL and sl_state == States.NORMAL)

        return (game_server_dt, gc_state, sl_state, ms_state,
                sc_state, webapi_state, is_maintenance)
    
    @staticmethod
    def cached_matchmaking_stats():
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)

        if cache_file["api_timestamp"] == 'unknown':
            return States.UNKNOWN
        
        game_server_dt = dt.datetime.fromtimestamp(cache_file["api_timestamp"], dt.UTC)
        
        gc_state = States.get(cache_file["game_coordinator"])
        sl_state = States.get(cache_file["sessions_logon"])

        graph_url = cache_file["graph_url"]
        online_players = cache_file["online_players"]
        online_servers = cache_file["online_servers"]
        active_players = cache_file["active_players"] 
        average_search_time = cache_file["average_search_time"]
        searching_players = cache_file["searching_players"]

        player_24h_peak = cache_file["player_24h_peak"]
        player_alltime_peak = cache_file["player_alltime_peak"]
        monthly_unique_players = cache_file["monthly_unique_players"]

        now = dt.datetime.now(tz=dt.UTC)
        is_maintenance = ((now.weekday() == 1 and now.hour > 21) or (now.weekday() == 2 and now.hour < 4)) \
            and (gc_state is not States.NORMAL or sl_state is not States.NORMAL)

        return (game_server_dt, graph_url, online_servers, online_players,
                active_players, searching_players, average_search_time,
                player_24h_peak, player_alltime_peak, monthly_unique_players,
                is_maintenance)
    
    @staticmethod
    def latest_info_update():
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)

        if cache_file["api_timestamp"] == 'unknown':
            return States.UNKNOWN

        return dt.datetime.fromtimestamp(cache_file["api_timestamp"], dt.UTC)

    def asdict(self):
        return self._asdict()


def get_monthly_unique_players():
    response = requests.get(MONTHLY_UNIQUE_PLAYERS_API, headers=HEADERS, timeout=15).json()
    return int(response['result']['players'])


def drop_cap_reset_timer():
    """Get drop cap reset time"""

    wanted_weekday = 2
    wanted_time = 2

    now = dt.datetime.now(tz=dt.UTC)
    days_left = (wanted_weekday - now.weekday() - 1) % 7

    wanted_date = (now + dt.timedelta(days=days_left)).replace(hour=wanted_time, minute=0, second=0, microsecond=0)

    time_left = wanted_date - now

    hours_left = time_left.seconds // HOUR
    minutes_left = time_left.seconds % HOUR // MINUTE
    seconds_left = time_left.seconds % MINUTE
    return days_left, hours_left, minutes_left, seconds_left
