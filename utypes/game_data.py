from __future__ import annotations

import dataclasses
from dataclasses import dataclass
import datetime as dt
from typing import NamedTuple, TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from functions import utime
from .cache import CoreCache, GCCache, GraphCache
from .states import States
from .steam_webapi import SteamWebAPI
from .protobufs import ScoreLeaderboardData

if TYPE_CHECKING:
    import requests

    from .states import State

__all__ = ('GameVersion', 'GameVersionData',
           'ExchangeRate', 'ExchangeRateData',
           'GameServers', 'OverallGameServersData', 'ServerStatusData', 'MatchmakingStatsData',
           'LeaderboardStats',
           'drop_cap_reset_timer', 'LEADERBOARD_API_REGIONS')


CS2_LEADERBOARD_API = 'https://api.steampowered.com/ICSGOServers_730/GetLeaderboardEntries/v1/' \
                      '?lbname=official_leaderboard_premier_season1'

LEADERBOARD_API_REGIONS = ('northamerica', 'southamerica', 'europe', 'asia', 'australia', 'china', 'africa')

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
    cs2_client_version: int | str
    cs2_server_version: int | str
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

    @classmethod
    def converter(cls, data: dict[str, Any]):
        """
        Used for convertion in ``@attrs.define``.

        You can use it as you would use a ``from_dict()`` method,
        but it returns the same object if you passed it as an argument.
        """

        if isinstance(data, cls):
            return data

        return ExchangeRateData(**data)

    def asdict(self):
        return self._asdict()


@dataclass(frozen=True, slots=True)
class BasicServerStatusData:
    info_requested_datetime: dt.datetime
    game_coordinator_state: State
    sessions_logon_state: State

    def is_maintenance(self):
        now = utime.utcnow()

        between_tuesday_and_wednesday = (now.weekday() == 1 and now.hour > 21) or (now.weekday() == 2 and now.hour < 4)
        game_coordinator_is_fine = (self.game_coordinator_state is States.NORMAL)
        sessions_logon_is_fine = (self.sessions_logon_state is States.NORMAL)
        return between_tuesday_and_wednesday and not (game_coordinator_is_fine and sessions_logon_is_fine)

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
    def request(cls, session: requests.Session):
        cs2_data = session.get(cls.CS2_VERSION_DATA_URL).text
        config_entries = (line for line in cs2_data.split('\n') if line)

        options = {}
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
    def cached_data(gc_cache: GCCache):
        """Get the version of the game"""

        cs2_client_version = gc_cache.get('cs2_client_version', 'unknown')
        cs2_server_version = gc_cache.get('cs2_client_version', 'unknown')
        cs2_patch_version = gc_cache.get('cs2_patch_version', 'unknown')

        cs2_version_timestamp = gc_cache.get('cs2_version_timestamp', 0)
        return GameVersionData(cs2_client_version,
                               cs2_server_version,
                               cs2_patch_version,
                               cs2_version_timestamp)


class ExchangeRate:
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
    def request(cls, webapi: SteamWebAPI):
        r = webapi.get_asset_prices(730)['result']['assets']
        key_price = [item for item in r if item['classid'] == '1544098059'][0]['prices']

        for currency in cls.UNDEFINED_CURRENCIES:
            if currency in key_price:
                del key_price[currency]

        prices = {k: v / 100 for k, v in key_price.items()}
        formatted_prices = {k: f'{v:.0f}' if v % 1 == 0 else f'{v:.2f}'
                            for k, v in prices.items()}

        return ExchangeRateData(**formatted_prices)

    @staticmethod
    def cached_data(core_cache: CoreCache):
        """Get the currencies for CS2 store"""

        key_prices = core_cache.get('key_price')

        if key_prices is None:
            # to allow chaining `ExchangeRate.cached_data().asdict()`
            # and get more sensible error later on
            return MockDict()

        return ExchangeRateData(**key_prices)


class MockDict(dict):
    def asdict(self):
        return self


class GameServers:
    @classmethod
    def request(cls, webapi: SteamWebAPI):
        response = webapi.csgo_get_game_servers_status()

        result = response['result']
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
    def cached_server_status(core_cache: CoreCache, gc_cache: GCCache):
        """Get the status of Counter-Strike servers"""

        game_server_dt = GameServers.latest_info_update(core_cache)
        if game_server_dt == States.UNKNOWN:
            return States.UNKNOWN

        gc_state = States.get_or_unknown(gc_cache.get('game_coordinator_state'))  # GC!!!!
        sl_state = States.get_or_unknown(core_cache.get('sessions_logon_state'))
        ms_state = States.get_or_unknown(core_cache.get('matchmaking_scheduler_state'))
        sc_state = States.get_or_unknown(core_cache.get('steam_community_state'))
        webapi_state = States.get_or_unknown(core_cache.get('webapi_state'))

        return ServerStatusData(game_server_dt,
                                gc_state, sl_state, ms_state, sc_state, webapi_state)
    
    @staticmethod
    def cached_matchmaking_stats(core_cache: CoreCache, gc_cache: GCCache, graph_cache: GraphCache):
        game_server_dt = GameServers.latest_info_update(core_cache)
        if game_server_dt is States.UNKNOWN:
            return States.UNKNOWN
        
        gc_state = States.get_or_unknown(core_cache.get('game_coordinator_state'))
        sl_state = States.get_or_unknown(core_cache.get('sessions_logon_state'))

        graph_url = graph_cache.get('graph_url', '')  # graph!!!!
        online_players = gc_cache.get('online_players', 0)  # GC!!!!

        online_servers = core_cache.get('online_servers', 0)
        active_players = core_cache.get('active_players', 0)
        average_search_time = core_cache.get('average_search_time', 0)
        searching_players = core_cache.get('searching_players', 0)

        player_24h_peak = core_cache.get('player_24h_peak', 0)
        player_alltime_peak = core_cache.get('player_alltime_peak', 0)
        monthly_unique_players = core_cache.get('monthly_unique_players', 0)

        return MatchmakingStatsData(game_server_dt,
                                    gc_state, sl_state,
                                    graph_url,
                                    online_servers,
                                    online_players, active_players, searching_players, average_search_time,
                                    player_24h_peak, player_alltime_peak, monthly_unique_players)
    
    @staticmethod
    def latest_info_update(cache: CoreCache):
        if cache.get('api_timestamp', 'unknown') == 'unknown':
            return States.UNKNOWN

        return dt.datetime.fromtimestamp(cache['api_timestamp'], dt.UTC)


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

        last_wins = {map_name: 0 for map_name in MAPS.values()}
        stats = {entry.tag: entry.val for entry in detail_data.matchentries}

        wins = stats.get(16, -1)
        ties = stats.get(17, -1)
        losses = stats.get(18, -1)
        if stats.get(19):
            for map_id, map_name in MAPS.items():
                last_wins[map_name] = ((stats[19] << (4 * map_id)) & 0xF0000000) >> 4 * 7
        timestamp = stats.get(20, -1)
        region = REGIONS.get(stats.get(21), 'unknown')

        return cls(rank, rating, name, wins, ties, losses, last_wins, timestamp, region)

    @classmethod
    def converter(cls, data: list[Any]):
        """
        Used for convertion in ``@attrs.define``.

        You can use it as you would use a ``from_dict()`` method,
        but it returns the same object if you passed it as an argument.
        """

        if isinstance(data, cls):
            return data

        return [LeaderboardStats.from_json(person) for person in data]

    @staticmethod
    def request_world(session: requests.Session):
        world_leaderboard_data = session.get(CS2_LEADERBOARD_API).json()
        world_leaderboard_data = world_leaderboard_data['result']['entries']
        world_leaderboard_data = world_leaderboard_data[:10]

        return [LeaderboardStats.from_json(person).asdict() for person in world_leaderboard_data]

    @staticmethod
    def request_regional(session: requests.Session, region: str):
        api_link = CS2_LEADERBOARD_API + f'_{region}'
        regional_leaderboard_data = session.get(api_link).json()
        regional_leaderboard_data = regional_leaderboard_data['result']['entries']
        regional_leaderboard_data = regional_leaderboard_data[:10]

        return [LeaderboardStats.from_json(person).asdict() for person in regional_leaderboard_data]

    @staticmethod
    def cached_world_stats(core_cache: CoreCache):
        world_leaderboard_stats = core_cache.get('world_leaderboard_stats', [])
        return [LeaderboardStats(**person) for person in world_leaderboard_stats]

    @staticmethod
    def cached_regional_stats(core_cache: CoreCache, region: str):
        regional_leaderboard_stats = core_cache.get(f'regional_leaderboard_stats_{region}', [])
        return [LeaderboardStats(**person) for person in regional_leaderboard_stats]

    def asdict(self):
        return self._asdict()


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
