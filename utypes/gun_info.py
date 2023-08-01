import json
from typing import NamedTuple

import config
from l10n import LocaleKeys as LK


__all__ = ('GunInfo',)


gun_origins = {'Germany': LK.gun_origin_germany, 'Austria': LK.gun_origin_austria, 'Italy': LK.gun_origin_italy,
               'Switzerland': LK.gun_origin_switzerland, 'Czech Republic': LK.gun_origin_czech_republic,
               'Belgium': LK.gun_origin_belgium, 'Sweden': LK.gun_origin_sweden, 'Israel': LK.gun_origin_israel,
               'United States': LK.gun_origin_us, 'Russia': LK.gun_origin_russia, 'France': LK.gun_origin_france,
               'United Kingdom': LK.gun_origin_uk, 'South Africa': LK.gun_origin_south_africa}


class GunInfo(NamedTuple):
    id: str
    name: str

    origin: str
    team: str
    price: int
    clip_size: int
    reserved_ammo: int
    fire_rate: int
    kill_reward: int
    movement_speed: int

    armor_penetration: int
    accurate_range_stand: float
    accurate_range_crouch: float

    draw_time: float
    reload_clip_ready: float
    reload_fire_ready: float

    unarmored_damage_head: int
    armored_damage_head: int

    unarmored_damage_chest_arms: int
    armored_damage_chest_arms: int

    unarmored_damage_stomach: int
    armored_damage_stomach: int

    unarmored_damage_legs: int
    armored_damage_legs: int
    
    def as_dict(self):
        return self._asdict()
    
    @staticmethod
    def load():
        with open(config.GUN_DATA_FILE_PATH) as f:
            data = json.load(f)

        for g_info in data:
            g_info['origin'] = gun_origins[g_info['origin']]
        return {g_info['id']: GunInfo(**g_info) for g_info in data}
