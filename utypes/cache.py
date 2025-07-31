from __future__ import annotations


__all__ = ['CoreCache', 'GCCache', 'GraphCache', 'LeaderboardCache']

from typing import Literal


_premier_leaderboard_entries = Literal['world_leaderboard_stats',
                                       'regional_leaderboard_stats_northamerica',
                                       'regional_leaderboard_stats_southamerica',
                                       'regional_leaderboard_stats_europe',
                                       'regional_leaderboard_stats_asia',
                                       'regional_leaderboard_stats_australia',
                                       'regional_leaderboard_stats_china',
                                       'regional_leaderboard_stats_africa',]

CoreCache = dict[str, ...]  # todo: implement actual dataclasses
GCCache = dict[str, ...]
GraphCache = dict[str, str]
LeaderboardCache = dict[_premier_leaderboard_entries, list[dict[str, ...]]]
