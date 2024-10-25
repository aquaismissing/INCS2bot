from __future__ import annotations

from typing import NamedTuple, Protocol

from .states import State, States


__all__ = ('Datacenter', 'DatacenterRegion', 'DatacenterGroup',
           'DatacenterState', 'DatacenterRegionState', 'DatacenterGroupState',
           'DatacenterInlineResult',
           'DatacenterVariation', 'DatacenterStateVariation')


class DatacenterVariation(Protocol):
    def cached_state(self, cache: dict[str, ...]) -> DatacenterStateVariation:
        ...


class Datacenter(NamedTuple):
    id: str
    symbol: str = ""
    l10n_key_name: str = ""
    l10n_key_title: str = ""

    def cached_state(self, cache: dict[str, ...]) -> DatacenterState:
        dc_data = cache[self.id]
        capacity = States.get(dc_data['capacity'])
        load = States.get(dc_data['load'])

        return DatacenterState(self, capacity, load)


class DatacenterRegion(NamedTuple):
    id: str
    datacenters: list[Datacenter]
    symbol: str = ""
    l10n_key_name: str = ""
    l10n_key_title: str = ""

    def cached_state(self, cache: dict[str, ...]) -> DatacenterRegionState:
        region_data = cache[self.id]
        states = [dc.cached_state(region_data) for dc in self.datacenters]

        return DatacenterRegionState(self, states)


class DatacenterGroup(NamedTuple):
    id: str
    regions: list[DatacenterRegion]
    l10n_key_title: str

    def cached_state(self, cache: dict[str, ...]) -> DatacenterGroupState:
        group_data = cache[self.id]
        region_states = [region.cached_state(group_data) for region in self.regions]

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


DatacenterStateVariation = DatacenterState | DatacenterRegionState | DatacenterGroupState


class DatacenterInlineResult(NamedTuple):
    title: str
    thumbnail: str
    state: DatacenterStateVariation
    tags: set
