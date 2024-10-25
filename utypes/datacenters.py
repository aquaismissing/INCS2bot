from __future__ import annotations

import json
from typing import NamedTuple, TYPE_CHECKING

from functions import caching
from .states import State, States
# noinspection PyPep8Naming


if TYPE_CHECKING:
    from pathlib import Path


__all__ = ('Datacenter', 'DatacenterRegion', 'DatacenterGroup',
           'DatacenterState', 'DatacenterRegionState', 'DatacenterGroupState',
           'DatacenterInlineResult',
           'DatacenterVariation', 'DatacenterStateVariation')


class Datacenter(NamedTuple):
    id: str
    symbol: str = ""
    l10n_key_name: str = ""
    l10n_key_title: str = ""

    def cached_state(self, filename: Path) -> DatacenterState:
        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        data = cache_file['datacenters'][self.id]
        capacity, load = States.get(data['capacity']), States.get(data['load'])
        return DatacenterState(self, capacity, load)


class DatacenterRegion(NamedTuple):
    id: str
    datacenters: list[Datacenter]
    symbol: str = ""
    l10n_key_name: str = ""
    l10n_key_title: str = ""

    def cached_state(self, filename: Path) -> DatacenterRegionState:
        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        obj_data = cache_file['datacenters'][self.id]
        states = []

        for dc in self.datacenters:
            data = obj_data[dc.id]
            capacity, load = States.get(data['capacity']), States.get(data['load'])
            states.append(DatacenterState(dc, capacity, load))

        return DatacenterRegionState(self, states)


class DatacenterGroup(NamedTuple):
    id: str
    regions: list[DatacenterRegion]
    l10n_key_title: str

    def cached_state(self, filename: Path) -> DatacenterGroupState:
        with open(filename, encoding='utf-8') as f:
            cache_file = json.load(f)

        obj_data = cache_file['datacenters'][self.id]
        region_states = []

        for region in self.regions:
            region_data = obj_data[region.id]

            states = []
            for datacenter in region.datacenters:
                data = region_data[datacenter.id]
                capacity, load = States.get(data['capacity']), States.get(data['load'])

                states.append(DatacenterState(datacenter, capacity, load))
            region_states.append(DatacenterRegionState(region, states))

        return DatacenterGroupState(self, region_states)


class DatacenterState(NamedTuple):
    datacenter: Datacenter
    capacity: State
    load: State


class DatacenterRegionState(NamedTuple):
    region: DatacenterRegion
    states: list[DatacenterState]


class DatacenterGroupState(NamedTuple):
    group: DatacenterGroup
    region_states: list[DatacenterRegionState]


DatacenterVariation = Datacenter | DatacenterRegion | DatacenterGroup
DatacenterStateVariation = DatacenterState | DatacenterRegionState | DatacenterGroupState


class DatacenterInlineResult(NamedTuple):
    title: str
    thumbnail: str
    state: DatacenterStateVariation
    tags: set
