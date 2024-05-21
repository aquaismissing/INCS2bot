from __future__ import annotations

from dataclasses import astuple, dataclass
from enum import auto, StrEnum
import re
from typing import NamedTuple

from steam import steamid
from steam.steamid import SteamID
import requests

import config
from .steam_webapi import SteamWebAPI


__all__ = ('ErrorCode', 'ParseUserStatsError', 'ProfileInfo', 'UserGameStats')

STEAM_PROFILE_LINK_PATTERN = re.compile(r'(?:https?://)?steamcommunity\.com/(?:profiles|id)/[a-zA-Z0-9]+(/?)\w')
_csgofrcode_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

api = SteamWebAPI(config.STEAM_API_KEY)


def to_percentage(x: int | float, /, round_to: int = 2):
    """Shortcut to `round(x * 100, round_to)`."""

    return round(x * 100, round_to if round_to else None)


class ErrorCode(StrEnum):
    INVALID_REQUEST = auto()
    INVALID_LINK = auto()
    PROFILE_IS_PRIVATE = auto()
    UNKNOWN_ERROR = auto()
    NO_STATS_AVAILABLE = auto()


class ParseUserStatsError(Exception):
    def __init__(self, code: ErrorCode):
        self.code = code

    def __repr__(self):
        return f'{self.__class__.__name__}(code={self.code!r})'

    @property
    def is_unknown(self):
        return self.code == ErrorCode.UNKNOWN_ERROR


class UserGameStats(NamedTuple):
    steamid: int
    total_time_played: float
    total_kills: int
    total_deaths: int
    kd_ratio: float
    total_matches_played: int
    total_matches_won: int
    matches_win_percentage: float
    total_rounds_played: int
    total_wins_pistolround: int
    total_shots_fired: int
    total_shots_hit: int
    hit_accuracy: float
    headshots_percentage: float
    best_map_name: str
    best_map_win_percentage: float
    total_mvps: int
    total_money_earned: int
    total_rescued_hostages: int
    total_weapons_donated: int
    total_broken_windows: int
    total_damage_done: int
    total_planted_bombs: int
    total_defused_bombs: int
    total_kills_knife: int
    total_kills_hegrenade: int
    total_kills_molotov: int
    total_shots_taser: int
    total_kills_taser: int
    taser_accuracy: float
    total_kills_knife_fight: int
    total_kills_enemy_weapon: int
    total_kills_enemy_blinded: int
    total_kills_against_zoomed_sniper: int
    total_shots_ak47: int
    total_hits_ak47: int
    total_kills_ak47: int
    ak47_accuracy: float
    total_shots_m4a1: int
    total_hits_m4a1: int
    total_kills_m4a1: int
    m4a1_accuracy: float
    total_shots_awp: int
    total_hits_awp: int
    total_kills_awp: int
    awp_accuracy: float
    total_shots_glock: int
    total_hits_glock: int
    total_kills_glock: int
    glock_accuracy: float
    total_shots_hkp2000: int
    total_hits_hkp2000: int
    total_kills_hkp2000: int
    hkp2000_accuracy: float
    total_shots_p250: int
    total_hits_p250: int
    total_kills_p250: int
    p250_accuracy: float
    total_shots_elite: int
    total_hits_elite: int
    total_kills_elite: int
    elite_accuracy: float
    total_shots_fiveseven: int
    total_hits_fiveseven: int
    total_kills_fiveseven: int
    fiveseven_accuracy: float
    total_shots_tec9: int
    total_hits_tec9: int
    total_kills_tec9: int
    tec9_accuracy: float
    total_shots_deagle: int
    total_hits_deagle: int
    total_kills_deagle: int
    deagle_accuracy: float
    total_shots_mac10: int
    total_hits_mac10: int
    total_kills_mac10: int
    mac10_accuracy: float
    total_shots_mp7: int
    total_hits_mp7: int
    total_kills_mp7: int
    mp7_accuracy: float
    total_shots_mp9: int
    total_hits_mp9: int
    total_kills_mp9: int
    mp9_accuracy: float
    total_shots_ump45: int
    total_hits_ump45: int
    total_kills_ump45: int
    ump45_accuracy: float
    total_shots_bizon: int
    total_hits_bizon: int
    total_kills_bizon: int
    bizon_accuracy: float
    total_shots_p90: int
    total_hits_p90: int
    total_kills_p90: int
    p90_accuracy: float
    total_shots_famas: int
    total_hits_famas: int
    total_kills_famas: int
    famas_accuracy: float
    total_shots_galilar: int
    total_hits_galilar: int
    total_kills_galilar: int
    galilar_accuracy: float
    total_shots_aug: int
    total_hits_aug: int
    total_kills_aug: int
    aug_accuracy: float
    total_shots_sg556: int
    total_hits_sg556: int
    total_kills_sg556: int
    sg556_accuracy: float
    total_shots_ssg08: int
    total_hits_ssg08: int
    total_kills_ssg08: int
    ssg08_accuracy: float
    total_shots_scar20: int
    total_hits_scar20: int
    total_kills_scar20: int
    scar20_accuracy: float
    total_shots_g3sg1: int
    total_hits_g3sg1: int
    total_kills_g3sg1: int
    g3sg1_accuracy: float
    total_shots_nova: int
    total_hits_nova: int
    total_kills_nova: int
    nova_accuracy: float
    total_shots_mag7: int
    total_hits_mag7: int
    total_kills_mag7: int
    mag7_accuracy: float
    total_shots_sawedoff: int
    total_hits_sawedoff: int
    total_kills_sawedoff: int
    sawedoff_accuracy: float
    total_shots_xm1014: int
    total_hits_xm1014: int
    total_kills_xm1014: int
    xm1014_accuracy: float
    total_shots_negev: int
    total_hits_negev: int
    total_kills_negev: int
    negev_accuracy: float
    total_shots_m249: int
    total_hits_m249: int
    total_kills_m249: int
    m249_accuracy: float

    @staticmethod
    def from_dict(stats: dict[str, str | int | float]) -> UserGameStats:
        weapons = ('ak47', 'm4a1', 'awp', 'glock', 'hkp2000', 'p250', 'elite', 'fiveseven',
                   'tec9', 'deagle', 'mac10', 'mp7', 'mp9', 'ump45', 'bizon', 'p90', 'famas',
                   'galilar', 'aug', 'sg556', 'ssg08', 'scar20', 'g3sg1', 'nova', 'mag7', 'sawedoff',
                   'xm1014', 'negev', 'm249')

        stats['total_time_played'] = round(stats.get('total_time_played', 0) / 3600, 2)
        stats['kd_ratio'] = round(stats.get('total_kills', 0) / stats.get('total_deaths', 1), 2)
        stats['matches_win_percentage'] = to_percentage(
            stats.get('total_matches_won', 0) / stats.get('total_matches_played', 1)
        )
        stats['hit_accuracy'] = to_percentage(stats.get('total_shots_hit', 0) / stats.get('total_shots_fired', 1))
        stats['headshots_percentage'] = to_percentage(
            stats.get('total_kills_headshot', 0) / stats.get('total_kills', 1)
        )

        total_wins_map_stats = [stat for stat in stats if stat.startswith('total_wins_map_')]
        if total_wins_map_stats:
            best_map = max(total_wins_map_stats, key=lambda x: stats[x]).split('_')[-2:]
            stats['best_map_name'] = best_map[-1].capitalize()
            best_map_wins = stats[f'total_wins_map_{"_".join(best_map)}']
            best_map_rounds = stats[f'total_rounds_map_{"_".join(best_map)}']
            stats['best_map_win_percentage'] = to_percentage(best_map_wins / best_map_rounds)
        else:
            stats['best_map_name'] = 'N/A'
            stats['best_map_win_percentage'] = 0

        stats['taser_accuracy'] = to_percentage(stats.get('total_kills_taser', 0) / stats.get('total_shots_taser', 1))

        for weapon in weapons:
            stats[f'{weapon}_accuracy'] = (
                to_percentage(stats.get(f'total_hits_{weapon}', 0) / stats.get(f'total_shots_{weapon}', 1))
            )

        stats = {key: stats.get(key, 0) for key in UserGameStats._fields}
        return UserGameStats(**stats)

    @staticmethod
    async def get(data: str) -> UserGameStats:
        try:
            _id = parse_steamid(data)

            response = api.get_user_game_stats(steamid=_id.as_64, appid=730)
            if not response:
                raise ParseUserStatsError(ErrorCode.PROFILE_IS_PRIVATE)

            if response.get('playerstats') is None or response['playerstats'].get('stats') is None:
                raise ParseUserStatsError(ErrorCode.NO_STATS_AVAILABLE)

            stats_dict = {stat['name']: stat['value'] for stat in response['playerstats']['stats']}
            stats_dict['steamid'] = _id.as_64

            return UserGameStats.from_dict(stats_dict)
        except requests.exceptions.HTTPError as e:  # maybe should only wrap the request itself with these?
            status_code = e.response.status_code

            if status_code == 400:
                raise ParseUserStatsError(ErrorCode.INVALID_REQUEST)
            if status_code == 403:
                raise ParseUserStatsError(ErrorCode.PROFILE_IS_PRIVATE)
            raise e


@dataclass(slots=True)
class ProfileInfo:
    vanity_url: str
    steamid64: int
    account_id: int
    account_created: int
    invite_url: str
    invite_code: str
    csgo_friend_code: str
    faceit_url: str
    faceit_elo: int
    faceit_lvl: int
    faceit_ban: bool
    game_bans: int
    vac_bans: int
    days_since_last_ban: int
    community_ban: bool
    trade_ban: bool

    @staticmethod
    def _extract_faceit_data(data: dict):
        faceit_lvl = faceit_elo = faceit_url = faceit_ban = None

        if data:
            faceit_result = [user for user in data for game in user['games'] if game['name'] == 'cs2']

            if faceit_result:
                user = faceit_result[0]
                elo_api_link = f'https://api.faceit.com/users/v1/users/{user["id"]}'
                elo_api_response = api.session.get(elo_api_link, timeout=15).json()

                if elo_api_response.get('payload'):
                    elo_data = elo_api_response['payload']['games']['cs2']

                    faceit_elo = elo_data.get('faceit_elo', 0)
                    faceit_lvl = elo_data.get('skill_level', 0)
            else:
                user = data[0]

            faceit_url = f'https://faceit.com/en/players/{user["nickname"]}'
            faceit_ban = ('banned' in user.get('status', ''))

        return faceit_elo, faceit_lvl, faceit_url, faceit_ban

    @staticmethod
    async def get(data: str) -> ProfileInfo:
        try:
            _id = parse_steamid(data)

            bans = api.get_player_bans(steamids=str(_id.as_64))
            user_data = api.get_player_summaries(steamids=str(_id.as_64))["response"]["players"][0]

            vanity = user_data['profileurl']

            if not (bans and vanity):
                raise ParseUserStatsError(ErrorCode.PROFILE_IS_PRIVATE)

            account_created = user_data.get('timecreated')

            vanity_url = vanity.split('/')[-2]
            if vanity_url == str(_id.as_64):
                vanity_url = None

            faceit_api_link = f'https://api.faceit.com/search/v2/players?query={_id.as_64}'
            faceit_api_response = api.session.get(faceit_api_link, timeout=15).json()['payload']['results']
            faceit_elo, faceit_lvl, faceit_url, faceit_ban = ProfileInfo._extract_faceit_data(faceit_api_response)

            bans_data = bans['players'][0]

            vac_bans = bans_data['NumberOfVACBans']
            game_bans = bans_data['NumberOfGameBans']

            days_since_last_ban = 0
            if vac_bans or game_bans:
                days_since_last_ban = bans_data['DaysSinceLastBan']

            community_ban = bans_data['CommunityBanned']
            trade_ban = (bans_data['EconomyBan'] == 'banned')

            return ProfileInfo(vanity_url,
                               _id.as_64,
                               _id.id,
                               account_created,
                               _id.invite_url,
                               _id.as_invite_code,
                               _id.as_csgo_friend_code,
                               faceit_url,
                               faceit_elo,
                               faceit_lvl,
                               faceit_ban,
                               game_bans,
                               vac_bans,
                               days_since_last_ban,
                               community_ban,
                               trade_ban)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code

            if status_code == 400:
                raise ParseUserStatsError(ErrorCode.INVALID_REQUEST)
            if status_code == 403:
                raise ParseUserStatsError(ErrorCode.PROFILE_IS_PRIVATE)
            raise e

    def to_tuple(self) -> tuple:
        return astuple(self)


def parse_steamid(data: str) -> SteamID:
    data = data.strip()

    if STEAM_PROFILE_LINK_PATTERN.match(data):
        if not data.startswith('http'):
            data = 'https://' + data

        if (_id := steamid.from_url(data)) is None:
            raise ParseUserStatsError(ErrorCode.INVALID_LINK)

        return _id

    if (_id := SteamID(data)).is_valid():
        return _id

    if (_id := steamid.from_url(f'https://steamcommunity.com/id/{data}')) is None:
        raise ParseUserStatsError(ErrorCode.INVALID_REQUEST)

    return _id
