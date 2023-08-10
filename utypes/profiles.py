from dataclasses import astuple, dataclass
import logging
import re
from typing import NamedTuple

from steam import steamid
from steam.steamid import SteamID
from steam.webapi import WebAPI
import requests
import validators

import config


__all__ = ('ParsingUserStatsError', 'ProfileInfo', 'UserGameStats')


api = WebAPI(key=config.STEAM_API_KEY)


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")


class ParsingUserStatsError(Exception):
    INVALID_REQUEST = 'INVALID_REQUEST'
    PROFILE_IS_PRIVATE = 'PROFILE_IS_PRIVATE'
    UNKNOWN_ERROR = 'UNKNOWN_ERROR'

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'{self.__class__.__name__}(value={self.value!r})'


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

    @classmethod
    def from_dict(cls, stats: dict):
        weapons = ('ak47', 'm4a1', 'awp', 'glock', 'hkp2000', 'p250', 'elite', 'fiveseven',
                   'tec9', 'deagle', 'mac10', 'mp7', 'mp9', 'ump45', 'bizon', 'p90', 'famas',
                   'galilar', 'aug', 'sg556', 'ssg08', 'scar20', 'g3sg1', 'nova', 'mag7', 'sawedoff',
                   'xm1014', 'negev', 'm249')

        stats['total_time_played'] = round(stats["total_time_played"] / 3600, 2)
        stats['kd_ratio'] = round(stats['total_kills'] / stats['total_deaths'], 2)
        stats['matches_win_percentage'] = round(stats['total_matches_won'] / stats['total_matches_played'] * 100, 2)
        stats['hit_accuracy'] = round(stats['total_shots_hit'] / stats['total_shots_fired'] * 100, 2)
        stats['headshots_percentage'] = round(stats['total_kills_headshot'] / stats['total_kills'] * 100, 2)

        best_map = max((stat for stat in stats if stat.startswith('total_wins_map_')),
                       key=lambda x: stats[x]).split('_')[-2:]
        stats['best_map_name'] = best_map[-1].capitalize()
        best_map_wins = stats[f'total_wins_map_{"_".join(best_map)}']
        best_map_rounds = stats[f'total_rounds_map_{"_".join(best_map)}']
        stats['best_map_win_percentage'] = round(best_map_wins / best_map_rounds * 100, 2)

        stats['taser_accuracy'] = round(stats['total_kills_taser'] / stats[f'total_shots_taser'] * 100, 2)

        for weapon in weapons:
            stats[f'{weapon}_accuracy'] = \
                round(stats[f'total_hits_{weapon}'] / stats[f'total_shots_{weapon}'] * 100, 2)

        stats = {k: v for k, v in stats.items() if k in cls._fields}
        for field in cls._fields:
            if stats.get(field) is None:
                stats[field] = 0

        return cls(**stats)
    
    @classmethod
    def get(cls, data):
        try:
            steam64 = parse_steamid64(data)

            response = api.ISteamUserStats.GetUserStatsForGame(appid=730, steamid=steam64)
            if not response:
                raise ParsingUserStatsError(ParsingUserStatsError.PROFILE_IS_PRIVATE)

            stats_dict = {stat['name']: stat['value'] for stat in response["playerstats"]["stats"]}
            stats_dict['steamid'] = steam64

            return cls.from_dict(stats_dict)
        except ParsingUserStatsError as e:
            raise e
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code

            if status_code == 400:
                raise ParsingUserStatsError(ParsingUserStatsError.INVALID_REQUEST)
            if status_code == 403:
                raise ParsingUserStatsError(ParsingUserStatsError.PROFILE_IS_PRIVATE)
            raise e
        except Exception as e:
            logging.exception(f"Caught exception at parsing user CS stats!")
            raise e


@dataclass(slots=True)
class ProfileInfo:
    vanity_url: str
    steam64: int
    account_id: int
    steam2_id: str
    steam3_id: str
    invite_code: str
    invite_url: str
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
    
    @classmethod
    def get(cls, data):
        try:
            steam64 = parse_steamid64(data)

            bans = api.ISteamUser.GetPlayerBans(steamids=steam64)
            vanity = api.ISteamUser.GetPlayerSummaries(steamids=steam64)["response"]["players"][0]["profileurl"]

            if not (bans and vanity):
                raise ParsingUserStatsError(ParsingUserStatsError.PROFILE_IS_PRIVATE)

            faceit_api = f'https://api.faceit.com/search/v2/players?query={steam64}'

            vanity_url = vanity.split("/")[-2]
            if vanity_url == str(steam64):
                vanity_url = None

            steam_id = SteamID(steam64)

            faceit_url = faceit_ban = faceit_elo = faceit_lvl = None
            faceit_response = requests.get(faceit_api, timeout=15).json()['payload']['results']
            if faceit_response:
                faceit_result = [user for user in faceit_response for game in user['games'] if game['name'] == 'csgo']
                if faceit_result:
                    user = faceit_result[0]
                    faceit_url = f'https://faceit.com/en/players/{user["nickname"]}'
                    elo_api = requests.get(f'https://api.faceit.com/users/v1/users/{user["id"]}', 
                                           timeout=15).json()['payload']['games']

                    faceit_elo = 0
                    if 'faceit_elo' in elo_api['csgo']:
                        faceit_elo = elo_api['csgo']['faceit_elo']

                    faceit_lvl = 0
                    for game in user['games']:
                        if game['name'] == 'csgo':
                            faceit_lvl = game['skill_level']
                            break
                else:
                    user = faceit_response[0]
                    faceit_url = f'https://faceit.com/en/players/{user["nickname"]}'

                faceit_ban = ('banned' in user.get('status', ''))

            bans_data = bans['players'][0]

            vac_bans = bans_data['NumberOfVACBans']
            game_bans = bans_data['NumberOfGameBans']

            days_since_last_ban = 0
            if vac_bans or game_bans:
                days_since_last_ban = bans_data['DaysSinceLastBan']

            community_ban = bans_data['CommunityBanned']
            trade_ban = (bans_data['EconomyBan'] == 'banned')

            return cls(vanity_url,
                       steam64,
                       steam_id.id,
                       steam_id.as_steam2,
                       steam_id.as_steam3,
                       steam_id.as_invite_code,
                       steam_id.invite_url,
                       steam_id.as_csgo_friend_code,
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
                raise ParsingUserStatsError(ParsingUserStatsError.INVALID_REQUEST)
            if status_code == 403:
                raise ParsingUserStatsError(ParsingUserStatsError.PROFILE_IS_PRIVATE)
            raise e
        except Exception as e:
            logging.exception(f"Caught exception at parsing user profile info!")
            raise e

    def to_tuple(self):
        return astuple(self)


def parse_steamid64(data: str):
    data = data.strip()
    steam_profile_link_pattern = re.compile(r'(?:https?://)?steamcommunity\.com/(?:profiles|id)/[a-zA-Z0-9]+(/?)\w')

    if validators.url(data):
        if not steam_profile_link_pattern.match(data):
            raise ParsingUserStatsError(ParsingUserStatsError.INVALID_REQUEST)
        try:
            return steamid.from_url(data)
        except requests.exceptions.JSONDecodeError:
            raise ParsingUserStatsError(ParsingUserStatsError.INVALID_REQUEST)

    if SteamID(data).is_valid():
        return SteamID(data)

    resolve_vanity = api.ISteamUser.ResolveVanityURL(vanityurl=data, url_type=1)['response']
    if resolve_vanity['success'] == 1:
        return resolve_vanity['steamid']

    if resolve_vanity['success'] == 42:
        raise ParsingUserStatsError(ParsingUserStatsError.INVALID_REQUEST)

    raise ParsingUserStatsError(ParsingUserStatsError.UNKNOWN_ERROR)
