from __future__ import annotations

import datetime as dt
import json
from typing import NamedTuple
from zoneinfo import ZoneInfo

import requests

import config
from .states import State, States
from .protobufs import ScoreLeaderboardData

__all__ = ('GameVersionData',  'ExchangeRate', 'GameServersData', 'LeaderboardStats',
           'get_monthly_unique_players', 'drop_cap_reset_timer', 'LEADERBOARD_API_REGIONS')


MONTHLY_UNIQUE_PLAYERS_API = 'https://api.steampowered.com/ICSGOServers_730/GetMonthlyPlayerCount/v1'
CS2_VERSION_DATA_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CS2/master/game/csgo/steam.inf'
GET_KEY_PRICES_API = f'https://api.steampowered.com/ISteamEconomy/GetAssetPrices/v1/' \
                     f'?appid={config.CS_APP_ID}&key={config.STEAM_API_KEY}'
GAME_SERVERS_STATUS_API = f'https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1' \
                          f'?key={config.STEAM_API_KEY}'
CS2_LEADERBOARD_API = 'https://api.steampowered.com/ICSGOServers_730/GetLeaderboardEntries/v1/' \
                      '?lbname=official_leaderboard_premier_season1'

LEADERBOARD_API_REGIONS = ('northamerica', 'southamerica', 'europe', 'asia', 'australia', 'china', 'africa')

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0"}

MINUTE = 60
HOUR = 60 * MINUTE
VALVE_TIMEZONE = ZoneInfo('America/Los_Angeles')


SLD = ScoreLeaderboardData()
MAPS = {1: 'ancient',
        2: 'nuke',
        3: 'overpass',
        4: 'vertigo',
        5: 'mirage',
        6: 'inferno',
        7: 'anubis'}
REGIONS = {1: 'NA',
           2: 'SA',
           3: 'EU',
           4: 'AS',
           5: 'AU',
           7: 'AF',
           9: 'CH'}


class GameVersionData(NamedTuple):
    cs2_client_version: int
    cs2_server_version: int
    cs2_patch_version: str
    cs2_version_timestamp: str

    @staticmethod
    def request():
        options = {}

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
        cs2_version_timestamp = dt.datetime.strptime(version_datetime, "%b %d %Y %H:%M:%S").isoformat()

        return GameVersionData(cs2_client_version,
                               cs2_server_version,
                               cs2_patch_version,
                               cs2_version_timestamp)
    
    @staticmethod
    def cached_data():
        """Get the version of the game"""

        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)

        cs2_client_version = cache_file['cs2_client_version']
        cs2_patch_version = cache_file['cs2_patch_version']
        cs2_version_dt = dt.datetime.fromisoformat(cache_file['cs2_version_timestamp']) \
            .replace(tzinfo=VALVE_TIMEZONE).astimezone(ZoneInfo("UTC"))

        return cs2_patch_version, cs2_client_version, cs2_version_dt

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


class LeaderboardStats(NamedTuple):
    rank: int
    rating: int
    name: str
    wins: int
    ties: int
    losses: int
    last_wins: dict[str, int]
    timestamp: int
    region: str

    @classmethod
    def from_json(cls, data):
        rank = data['rank']
        rating = data['score'] >> 15
        name = data['name']

        detail_data = data['detailData']
        detail_data = detail_data[2:].rstrip('0')
        detail_data = SLD.parse(bytes.fromhex(detail_data))

        wins = 0
        ties = 0
        losses = 0
        last_wins = {map_name: 0 for map_name in MAPS.values()}
        timestamp = 0
        region = 0
        for entry in detail_data.matchentries:
            if entry.tag == 16:
                wins = entry.val
            elif entry.tag == 17:
                ties = entry.val
            elif entry.tag == 18:
                losses = entry.val
            elif entry.tag == 19:
                for map_id, map_name in MAPS.items():
                    last_wins[map_name] = ((entry.val << (4 * map_id)) & 0xF0000000) >> 4*7
            elif entry.tag == 20:
                timestamp = entry.val
            elif entry.tag == 21:
                region = REGIONS.get(entry.val, 'unknown')

        return cls(rank, rating, name, wins, ties, losses, last_wins, timestamp, region)

    @staticmethod
    def request_world():
        world_leaderboard_data = requests.get(CS2_LEADERBOARD_API, headers=HEADERS, timeout=15).json()
        world_leaderboard_data = world_leaderboard_data['result']['entries']
        world_leaderboard_data = world_leaderboard_data[:10]

        return [LeaderboardStats.from_json(person).asdict() for person in world_leaderboard_data]

    @staticmethod
    def request_regional(region: str):
        api_link = CS2_LEADERBOARD_API + f'_{region}'
        regional_leaderboard_data = requests.get(api_link, headers=HEADERS, timeout=15).json()
        regional_leaderboard_data = regional_leaderboard_data['result']['entries']
        regional_leaderboard_data = regional_leaderboard_data[:10]

        return [LeaderboardStats.from_json(person).asdict() for person in regional_leaderboard_data]

    @staticmethod
    def cached_world_stats():
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)

        world_leaderboard_stats = cache_file['world_leaderboard_stats']
        return [LeaderboardStats(**person) for person in world_leaderboard_stats]

    @staticmethod
    def cached_regional_stats(region: str):
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)

        regional_leaderboard_stats = cache_file[f'regional_leaderboard_stats_{region}']
        return [LeaderboardStats(**person) for person in regional_leaderboard_stats]

    def asdict(self):
        return self._asdict()


def get_monthly_unique_players() -> int:
    response = requests.get(MONTHLY_UNIQUE_PLAYERS_API, headers=HEADERS, timeout=15).json()
    return int(response['result']['players'])


def is_pdt(_datetime: dt.datetime) -> bool:
    return _datetime.strftime('%Z') == 'PDT'


def drop_cap_reset_timer() -> tuple[int, int, int, int]:
    """Get drop cap reset time"""

    wanted_weekday = 1
    wanted_time = 17

    now = dt.datetime.now(tz=VALVE_TIMEZONE)
    if is_pdt(now):
        wanted_time += 1

    days_until_wanted_weekday = (wanted_weekday - now.weekday()) % 7

    wanted_datetime = now + dt.timedelta(days=days_until_wanted_weekday)
    wanted_datetime = wanted_datetime.replace(hour=wanted_time, minute=0, second=0, microsecond=0)

    time_left = wanted_datetime - now

    days_left = time_left.days % 7
    hours_left = time_left.seconds // HOUR
    minutes_left = time_left.seconds % HOUR // MINUTE
    seconds_left = time_left.seconds % MINUTE
    return days_left, hours_left, minutes_left, seconds_left
