from __future__ import annotations

import dataclasses
from dataclasses import dataclass
import datetime as dt
import json
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

import requests

import config
from functions import utime
from .states import State, States
from .protobufs import ScoreLeaderboardData

__all__ = ('GameVersion', 'GameVersionData',
           'ExchangeRate', 'ExchangeRateData',
           'GameServers', 'OverallGameServersData', 'ServerStatusData', 'MatchmakingStatsData',
           'LeaderboardStats',
           'get_monthly_unique_players', 'drop_cap_reset_timer', 'LEADERBOARD_API_REGIONS')


MONTHLY_UNIQUE_PLAYERS_API = 'https://api.steampowered.com/ICSGOServers_730/GetMonthlyPlayerCount/v1'
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
        3: 'dust2',
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
    cs2_version_timestamp: float | str

    def asdict(self):
        return self._asdict()


class ExchangeRateData(NamedTuple):
    USD: float
    GBP: float
    EUR: float
    RUB: float
    BRL: float
    JPY: float
    NOK: float
    IDR: float
    MYR: float
    PHP: float
    SGD: float
    THB: float
    VND: float
    KRW: float
    UAH: float
    MXN: float
    CAD: float
    AUD: float
    NZD: float
    PLN: float
    CHF: float
    AED: float
    CLP: float
    CNY: float
    COP: float
    PEN: float
    SAR: float
    TWD: float
    HKD: float
    ZAR: float
    INR: float
    CRC: float
    ILS: float
    KWD: float
    QAR: float
    UYU: float
    KZT: float

    def asdict(self):
        return self._asdict()


@dataclass(frozen=True, slots=True)
class BasicServerStatusData:
    info_requested_datetime: dt.datetime
    game_coordinator_state: State
    sessions_logon_state: State

    def is_maintenance(self):
        now = utime.utcnow()
        return (((now.weekday() == 1 and now.hour > 21) or (now.weekday() == 2 and now.hour < 4))
                and not (self.game_coordinator_state is States.NORMAL and self.sessions_logon_state is States.NORMAL))

    def asdict(self):
        return dataclasses.asdict(self)


@dataclass(frozen=True, slots=True)
class ServerStatusData(BasicServerStatusData):
    matchmaking_scheduler_state: State
    steam_community_state: State
    webapi_state: State


@dataclass(frozen=True, slots=True)
class MatchmakingStatsData(BasicServerStatusData):
    graph_url: str
    online_servers: int
    online_players: int
    active_players: int
    searching_players: int
    average_search_time: int
    player_24h_peak: int
    player_alltime_peak: int
    monthly_unique_players: int


@dataclass(frozen=True, slots=True)
class OverallGameServersData:
    api_timestamp: int
    sessions_logon_state: State
    matchmaking_scheduler_state: State
    steam_community_state: State
    webapi_state: State
    online_servers: int
    active_players: int
    searching_players: int
    average_search_time: int
    datacenters: dict

    def asdict(self):
        return dataclasses.asdict(self)


class GameVersion:
    CS2_VERSION_DATA_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CS2/master/game/csgo/steam.inf'

    @classmethod
    def request(cls):
        options = {}

        # cs2
        cs2_data = requests.get(cls.CS2_VERSION_DATA_URL, headers=HEADERS, timeout=15).text
        config_entries = (line for line in cs2_data.split('\n') if line)

        for entry in config_entries:
            key, val = entry.split('=')
            options[key] = val

        version_datetime = dt.datetime.strptime(f'{options["VersionDate"]} {options["VersionTime"]}',
                                                '%b %d %Y %H:%M:%S')

        cs2_client_version = int(options['ClientVersion']) - 2000000
        cs2_server_version = int(options['ServerVersion']) - 2000000
        cs2_patch_version = options['PatchVersion']
        cs2_version_timestamp = version_datetime.timestamp()

        return GameVersionData(cs2_client_version,
                               cs2_server_version,
                               cs2_patch_version,
                               cs2_version_timestamp)
    
    @staticmethod
    def cached_data(filename: str | Path):
        """Get the version of the game"""

        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        cs2_client_version = cache_file.get('cs2_client_version', 'unknown')
        cs2_server_version = cache_file.get('cs2_client_version', 'unknown')
        cs2_patch_version = cache_file.get('cs2_patch_version', 'unknown')

        cs2_version_timestamp = cache_file.get('cs2_version_timestamp', 0)
        return GameVersionData(cs2_client_version,
                               cs2_server_version,
                               cs2_patch_version,
                               cs2_version_timestamp)


class ExchangeRate:
    GET_KEY_PRICES_API = f'https://api.steampowered.com/ISteamEconomy/GetAssetPrices/v1/' \
                         f'?appid=730&key={config.STEAM_API_KEY}'
    CURRENCIES_SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€", "RUB": "₽",
                          "BRL": "R$", "JPY": "¥", "NOK": "kr", "IDR": "Rp",
                          "MYR": "RM", "PHP": "₱", "SGD": "S$", "THB": "฿",
                          "VND": "₫", "KRW": "₩", "UAH": "₴", "MXN": "Mex$",
                          "CAD": "CDN$", "AUD": "A$", "NZD": "NZ$", "PLN": "zł",
                          "CHF": "CHF", "AED": "AED", "CLP": "CLP$", "CNY": "¥",
                          "COP": "COL$", "PEN": "S/.", "SAR": "SR", "TWD": "NT$",
                          "HKD": "HK$", "ZAR": "R", "INR": "₹", "CRC": "₡",
                          "ILS": "₪", "KWD": "KD", "QAR": "QR", "UYU": "$U",
                          "KZT": "₸"}
    UNDEFINED_CURRENCIES = ('Unknown', 'ARS', 'BYN', 'TRY')

    @classmethod
    def request(cls):
        r = requests.get(cls.GET_KEY_PRICES_API, timeout=15).json()['result']['assets']
        key_price = [item for item in r if item['classid'] == '1544098059'][0]['prices']

        for currency in cls.UNDEFINED_CURRENCIES:
            del key_price[currency]

        prices = {k: v / 100 for k, v in key_price.items()}
        formatted_prices = {k: f'{v:.0f}' if v % 1 == 0 else f'{v:.2f}'
                            for k, v in prices.items()}

        return ExchangeRateData(**formatted_prices)

    @staticmethod
    def cached_data(filename: str | Path):
        """Get the currencies for CS2 store"""

        with open(filename, encoding='utf-8') as f:
            key_prices = json.load(f).get('key_price')

        if key_prices is None:
            return {}

        for cur in ('ARS', 'TRY'):   # these values could be left in the cache
            if key_prices.get(cur):  # todo: remove later
                del key_prices[cur]

        return ExchangeRateData(**key_prices)
    

class GameServers:
    GAME_SERVERS_STATUS_API = f'https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1' \
                              f'?key={config.STEAM_API_KEY}'

    @classmethod
    def request(cls):
        response = requests.get(cls.GAME_SERVERS_STATUS_API, timeout=15)
        if response.status_code != 200:
            return

        result = response.json()['result']
        services = result['services']
        matchmaking = result['matchmaking']

        api_timestamp = result['app']['timestamp']
        sessions_logon = States.get(services['SessionsLogon'])
        steam_community = States.get(services['SteamCommunity'])
        matchmaking_scheduler = States.get(matchmaking['scheduler'])
        online_servers = matchmaking['online_servers']
        active_players = matchmaking['online_players']
        searching_players = matchmaking['searching_players']
        average_search_time = matchmaking['search_seconds_avg']
        datacenters = result['datacenters']

        return OverallGameServersData(api_timestamp,
                                      sessions_logon,
                                      matchmaking_scheduler,
                                      steam_community,
                                      States.NORMAL,
                                      online_servers,
                                      active_players,
                                      searching_players,
                                      average_search_time,
                                      datacenters)

    @staticmethod
    def cached_server_status(filename: str | Path):
        """Get the status of Counter-Strike servers"""

        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        game_server_dt = GameServers.latest_info_update(filename)
        if game_server_dt == States.UNKNOWN:
            return States.UNKNOWN

        gc_state = States.get_or_unknown(cache_file.get('game_coordinator_state'))
        sl_state = States.get_or_unknown(cache_file.get('sessions_logon_state'))
        ms_state = States.get_or_unknown(cache_file.get('matchmaking_scheduler_state'))
        sc_state = States.get_or_unknown(cache_file.get('steam_community_state'))
        webapi_state = States.get_or_unknown(cache_file.get('webapi_state'))

        return ServerStatusData(game_server_dt,
                                gc_state, sl_state, ms_state, sc_state, webapi_state)
    
    @staticmethod
    def cached_matchmaking_stats(filename: str | Path):
        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)
        
        game_server_dt = GameServers.latest_info_update(filename)
        if game_server_dt is States.UNKNOWN:
            return States.UNKNOWN
        
        gc_state = States.get_or_unknown(cache_file.get('game_coordinator_state'))
        sl_state = States.get_or_unknown(cache_file.get('sessions_logon_state'))

        graph_url = cache_file.get('graph_url', '')
        online_players = cache_file.get('online_players', 0)
        online_servers = cache_file.get('online_servers', 0)
        active_players = cache_file.get('active_players', 0)
        average_search_time = cache_file.get('average_search_time', 0)
        searching_players = cache_file.get('searching_players', 0)

        player_24h_peak = cache_file.get('player_24h_peak', 0)
        player_alltime_peak = cache_file.get('player_alltime_peak', 0)
        monthly_unique_players = cache_file.get('monthly_unique_players', 0)

        return MatchmakingStatsData(game_server_dt,
                                    gc_state, sl_state,
                                    graph_url,
                                    online_servers,
                                    online_players, active_players, searching_players, average_search_time,
                                    player_24h_peak, player_alltime_peak, monthly_unique_players)
    
    @staticmethod
    def latest_info_update(filename: str | Path):
        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        if cache_file.get('api_timestamp', 'unknown') == 'unknown':
            return States.UNKNOWN

        return dt.datetime.fromtimestamp(cache_file['api_timestamp'], dt.UTC)


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
                    last_wins[map_name] = ((entry.val << (4 * map_id)) & 0xF0000000) >> 4 * 7
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
    def cached_world_stats(filename: str | Path):
        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        world_leaderboard_stats = cache_file.get('world_leaderboard_stats', [])
        return [LeaderboardStats(**person) for person in world_leaderboard_stats]

    @staticmethod
    def cached_regional_stats(filename: str | Path, region: str):
        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        regional_leaderboard_stats = cache_file.get(f'regional_leaderboard_stats_{region}', [])
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
