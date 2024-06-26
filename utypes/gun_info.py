from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# noinspection PyPep8Naming
from l10n import LocaleKeys as LK


__all__ = ['load_gun_infos', 'GunInfo']


gun_origins = {'Germany': LK.gun_origin_germany, 'Austria': LK.gun_origin_austria, 'Italy': LK.gun_origin_italy,
               'Switzerland': LK.gun_origin_switzerland, 'Czech Republic': LK.gun_origin_czech_republic,
               'Belgium': LK.gun_origin_belgium, 'Sweden': LK.gun_origin_sweden, 'Israel': LK.gun_origin_israel,
               'United States': LK.gun_origin_us, 'Russia': LK.gun_origin_russia, 'France': LK.gun_origin_france,
               'United Kingdom': LK.gun_origin_uk, 'South Africa': LK.gun_origin_south_africa}


def load_gun_infos(filename: Path):
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)

    for gun_info in data:
        gun_info['origin'] = gun_origins[gun_info['origin']]
    return {g_info['id']: GunInfo(**g_info) for g_info in data}


@dataclass(slots=True, frozen=True)
class GunInfo:
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

    armored_damage_head: int
    unarmored_damage_head: int

    armored_damage_chest_arms: int
    unarmored_damage_chest_arms: int

    armored_damage_stomach: int
    unarmored_damage_stomach: int

    armored_damage_legs: int
    unarmored_damage_legs: int
    
    def asdict(self):
        return asdict(self)
