from dataclasses import dataclass
from enum import IntEnum
import json
from pathlib import Path
from pprint import pprint
import re
from typing import NewType

import requests

import config
from db.users import User

GET_TOURNAMENT_LAYOUT_API = 'https://api.steampowered.com/ICSGOTournaments_730/GetTournamentLayout/v1'
GET_TOURNAMENT_PREDICTIONS_API = 'https://api.steampowered.com/ICSGOTournaments_730/GetTournamentFantasyLineup/v1'
UPLOAD_TOURNAMENT_PREDICTIONS_API = 'https://api.steampowered.com/ICSGOTournaments_730/UploadTournamentPredictions/v1'

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0"}


USER_AUTH_KEY_PATTERN = re.compile(r'([A-Za-z0-9]){4}-([A-Za-z0-9]){5}-([A-Za-z0-9]){4}')


TeamPickID = NewType('TeamPickID', int)


class Event(IntEnum):  # the first two used as examples
    IEM_RIO_2022 = 20
    BLAST_PARIS_2023 = 21
    PGL_COPENHAGEN_2024 = 22


@dataclass(frozen=True, slots=True)
class MajorLayoutGroup:
    id: int
    name: str
    points_per_pick: int
    picks_allowed: bool
    teams: list[TeamPickID]
    picks: list[list[TeamPickID]]


@dataclass(frozen=True, slots=True)
class MajorLayoutSection:
    id: int
    name: str
    groups: list[MajorLayoutGroup]  # only one for Challengers and Legends stages
    # todo: maybe do specific dataclasses for stages instead of generic one?


@dataclass(frozen=True, slots=True)
class MajorLayoutTeam:
    pickid: TeamPickID
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

        response = requests.get(GET_TOURNAMENT_LAYOUT_API,
                                params={'key': self.steam_webapi_key, 'event': self.event.value},
                                headers=HEADERS, timeout=15)
        response.raise_for_status()

        layout = response.json()['result']
        event = Event(layout['event'])
        name = layout['name']
        for section in layout['sections']:
            for i, group in enumerate(section['groups']):
                for j, team in enumerate(group['teams']):
                    group['teams'][j] = TeamPickID(team['pickid'])

                for pick in group['picks']:
                    j = pick.pop('index')  # to ensure the order remains
                    group['picks'][j] = list(pick.values())
                group['id'] = group.pop('groupid')

                section['groups'][i] = MajorLayoutGroup(**group)
            section['id'] = section.pop('sectionid')

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
                for k, pickid in enumerate(group['teams']):
                    group['teams'][k] = TeamPickID(pickid)

                section['groups'][j] = MajorLayoutGroup(**group)
            layout['sections'][i] = MajorLayoutSection(**section)

        for i, team in enumerate(layout['teams']):
            layout['teams'][i] = MajorLayoutTeam(**team)

        return MajorLayout(**layout)

    def get_user_predictions(self, user: User):
        if not self.is_event_ongoing():
            return

        picks = requests.get(GET_TOURNAMENT_PREDICTIONS_API,
                             params={'key': self.steam_webapi_key,
                                     'event': self.event.value,
                                     'steamid': user.steamid,
                                     'steamidkey': user.pickem_auth_key},
                             headers=HEADERS, timeout=15).json()['result']['picks']
        return [MajorPredictionsPick(**pick) for pick in picks]

    def set_challengers_stage_predictions(self, user: User, pickids: list[int]):
        if len(pickids) != 9:
            raise ValueError('a count of pickids must be equal to 9')

        params = {'key': self.steam_webapi_key}
        sectionid = 0
        groupid = 0

        data = {
            'event': self.event.value, 'steamid': user.steamid, 'steamidkey': user.pickem_auth_key,
            'sectionid': sectionid, 'groupid': groupid, 'pickid': pickids[0]
        }
        for i, pickid in enumerate(pickids[1:], 1):
            data[f'sectionid{i}'] = sectionid
            data[f'groupid{i}'] = groupid
            data[f'pickid{i}'] = pickid

        response = requests.post(UPLOAD_TOURNAMENT_PREDICTIONS_API, params=params, data=data)
        response.raise_for_status()

    def set_legends_stage_predictions(self, user: User, pickids: list[int]):
        if len(pickids) != 9:
            raise ValueError('a count of pickids must be equal to 9')

        params = {'key': self.steam_webapi_key}
        sectionid = 1
        groupid = 0

        data = {
            'event': self.event.value, 'steamid': user.steamid, 'steamidkey': user.pickem_auth_key,
            'sectionid': sectionid, 'groupid': groupid, 'pickid': pickids[0]
        }
        for i, pickid in enumerate(pickids[1:], 1):
            data[f'sectionid{i}'] = sectionid
            data[f'groupid{i}'] = groupid
            data[f'pickid{i}'] = pickid

        response = requests.post(UPLOAD_TOURNAMENT_PREDICTIONS_API, params=params, data=data)
        response.raise_for_status()

    def set_playoff_predictions(self, user: User, pickids: list[int]):
        if len(pickids) != 7:
            raise ValueError('a count of pickids must be equal to 7')

        params = {'key': self.steam_webapi_key}

        sectionid = 2
        data = {
            'event': self.event.value, 'steamid': user.steamid, 'steamidkey': user.pickem_auth_key,
            'sectionid': sectionid, 'groupid': 0, 'pickid': pickids[0]
        }
        for i, pickid in enumerate(pickids[1:4], 1):
            data[f'sectionid{i}'] = sectionid
            data[f'groupid{i}'] = i
            data[f'pickid{i}'] = pickid

        sectionid = 3
        for i, pickid in enumerate(pickids[4:6], 4):
            data[f'sectionid{i}'] = sectionid
            data[f'groupid{i}'] = i - 4
            data[f'pickid{i}'] = pickid

        sectionid = 4
        data['sectionid6'] = sectionid
        data['groupid6'] = 0
        data['pickid6'] = pickids[6]

        response = requests.post(UPLOAD_TOURNAMENT_PREDICTIONS_API, params=params, data=data)
        response.raise_for_status()


def main():
    a = MajorPickEmService(config.STEAM_API_KEY, Event.BLAST_PARIS_2023)
    layout = a.get_event_layout()
    pprint(layout)
    print(layout.event)
    print(type(layout.event))


if __name__ == '__main__':
    main()
