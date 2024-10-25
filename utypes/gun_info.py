from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# noinspection PyPep8Naming
__all__ = ['load_gun_infos', 'GunInfo']


def load_gun_infos(filename: Path):
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)

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
