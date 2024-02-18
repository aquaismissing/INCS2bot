from dataclasses import dataclass
from enum import IntEnum
import json
from pathlib import Path
from pprint import pprint
import re

import requests

import config

GET_TOURNAMENT_LAYOUT_API = 'https://api.steampowered.com/ICSGOTournaments_730/GetTournamentLayout/v1'
GET_TOURNAMENT_PREDICTIONS_API = 'https://api.steampowered.com/ICSGOTournaments_730/GetTournamentFantasyLineup/v1?key={}&event={}&steamid={}&steamidkey={}'

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0"}


USER_AUTH_KEY_PATTERN = re.compile(r'([A-Za-z0-9]){4}-([A-Za-z0-9]){5}-([A-Za-z0-9]){4}')


class Event(IntEnum):  # the first two used as an example
    IEM_RIO_2022 = 20
    BLAST_PARIS_2023 = 21
    PGL_COPENHAGEN_2024 = 22


@dataclass(frozen=True, slots=True)
class MajorLayoutGroupTeam:
    pickid: int


@dataclass(frozen=True, slots=True)
class MajorLayoutGroupPick:
    index: int
    pickids: list[int]


@dataclass(frozen=True, slots=True)
class MajorLayoutGroup:
    groupid: int
    name: str
    points_per_pick: int
    picks_allowed: bool
    teams: list[MajorLayoutGroupTeam]
    picks: list


@dataclass(frozen=True, slots=True)
class MajorLayoutSection:
    sectionid: int
    name: str
    groups: list[MajorLayoutGroup]  # usually only one


@dataclass(frozen=True, slots=True)
class MajorLayoutTeam:
    pickid: int
    logo: str
    name: str


@dataclass(frozen=True, slots=True)
class MajorLayout:
    event: Event
    name: str
    challengers_stage: MajorLayoutSection
    legends_stage: MajorLayoutSection
    playoff_stage: MajorLayoutSection
    teams: list[MajorLayoutTeam]


@dataclass(frozen=True, slots=True)
class MajorPredictionsPick:
    groupid: int
    index: int
    pick: int


@dataclass(frozen=True, slots=True)
class MajorPickEmService:
    """Provides general information and methods for ongoing Major and its Pick'Em."""

    steam_webapi_key: str
    event: Event | None

    def is_event_ongoing(self) -> bool:
        return self.event is not None

    def get_event_layout(self):
        if not self.is_event_ongoing():
            return

        layout = requests.get(GET_TOURNAMENT_LAYOUT_API,
                              params={'key': self.steam_webapi_key, 'event': self.event.value},
                              headers=HEADERS, timeout=15).json()['result']

        event = Event(layout['event'])
        name = layout['name']
        for i, section in enumerate(layout['sections']):
            for j, group in enumerate(section['groups']):
                for k, team in enumerate(group['teams']):
                    group['teams'][k] = MajorLayoutGroupTeam(team['pickid'])
                for k, pick in enumerate(group['picks']):
                    group['picks'][k] = MajorLayoutGroupPick(**pick)
                section['groups'][j] = MajorLayoutGroup(**group)

        challengers_stage = MajorLayoutSection(**layout['sections'][0])
        legends_stage = MajorLayoutSection(**layout['sections'][1])
        playoff_stage = MajorLayoutSection(**layout['sections'][2])

        teams = [MajorLayoutTeam(**team) for team in layout['teams']]

        return MajorLayout(event, name, challengers_stage, legends_stage, playoff_stage, teams)

    def cached_event_layout(self, filename: str | Path):
        if not self.is_event_ongoing():
            return

        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        layout = cache_file['majors_layout'][str(self.event.value)]

        for i, section in enumerate(layout['sections']):
            for j, group in enumerate(section['groups']):
                for k, team in enumerate(group['teams']):
                    pickid = team['pickid']
                    group['teams'][k] = MajorLayoutGroupTeam(pickid)
                for k, pick in enumerate(group['picks']):
                    group['picks'][k] = MajorLayoutGroupPick(**pick)
                section['groups'][j] = MajorLayoutGroup(**group)
            layout['sections'][i] = MajorLayoutSection(**section)

        for i, team in enumerate(layout['teams']):
            layout['teams'][i] = MajorLayoutTeam(**team)

        return MajorLayout(**layout)


@dataclass(frozen=True, slots=True)
class UserMajorPickEm:
    """User-specific Pick'Em information and methods."""

    pickem_service: MajorPickEmService
    steamid: int  # todo: replace with db.User
    auth_key: str

    def get_predictions(self):
        if not self.pickem_service.is_event_ongoing():
            return
        picks = requests.get(GET_TOURNAMENT_PREDICTIONS_API,
                             params={'key': self.pickem_service.steam_webapi_key,
                                     'event': self.pickem_service.event.value,
                                     'steamid': self.steamid,
                                     'steamidkey': self.auth_key},
                             headers=HEADERS, timeout=15).json()['result']['picks']
        return [MajorPredictionsPick(**pick) for pick in picks]

    def set_challengers_stage_predictions(self, pickids: list[int]):
        if len(pickids) != 9:
            raise ValueError('a count of pickids must be equal to 9')
        # more silly stuff there...


a = MajorPickEmService(config.STEAM_API_KEY, Event.BLAST_PARIS_2023)
data = a.get_event_layout()
pprint(data)
print(data.event)
print(type(data.event))