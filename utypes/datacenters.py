# import env

import config
from .states import State, States

import json
from typing import NamedTuple
from l10n import LocaleKeys as LK


__all__ = ('DatacenterAtlas', 'Datacenter', 'DatacenterRegion', 'DatacenterGroup',
           'DatacenterState', 'DatacenterRegionState', 'DatacenterGroupState', 'DatacenterInlineResult')


class Datacenter(NamedTuple):
    id: str
    symbol: str = ""
    l10n_key_name: str = ""
    l10n_key_title: str = ""


class DatacenterState(NamedTuple):
    dc: Datacenter
    capacity: State
    load: State


class DatacenterRegion(NamedTuple):
    id: str
    datacenters: list[Datacenter]
    symbol: str = ""
    l10n_key_name: str = ""
    l10n_key_title: str = ""


class DatacenterRegionState(NamedTuple):
    region: DatacenterRegion
    states: list[DatacenterState]


class DatacenterGroup(NamedTuple):
    id: str
    regions: list[DatacenterRegion]
    l10n_key_title: str


class DatacenterGroupState(NamedTuple):
    group: DatacenterGroup
    region_states: list[DatacenterRegionState]


class DatacenterAtlas:
    AFRICA = DatacenterRegion(
        "south_africa",
        [
            Datacenter(
                "johannesburg",
                l10n_key_title=LK.dc_africa_johannesburg
            ),
        ],
        "🇿🇦",
        LK.dc_africa,
        LK.dc_africa_title
    )

    AUSTRALIA = DatacenterRegion(
        "australia",
        [
            Datacenter(
                "sydney",
                l10n_key_title=LK.dc_australia_sydney
            ),
        ],
        "🇦🇺",
        LK.dc_australia,
        LK.dc_australia_title
    )

    EU_NORTH = DatacenterGroup(
        "eu_north",
        [
            DatacenterRegion(
                "sweden",
                [
                    Datacenter(
                        "stockholm",
                        l10n_key_title=LK.dc_sweden_stockholm
                    ),
                ],
                symbol="🇸🇪",
                l10n_key_title=LK.dc_sweden_title
            ),
        ],
        LK.dc_north
    )

    EU_WEST = DatacenterGroup(
        "eu_west",
        [
            DatacenterRegion(
                "germany",
                [
                    Datacenter(
                        "frankfurt",
                        l10n_key_title=LK.dc_germany_frankfurt
                    ),
                ],
                symbol="🇩🇪",
                l10n_key_title=LK.dc_germany_title
            ),
            DatacenterRegion(
                "spain",
                [
                    Datacenter(
                        "madrid",
                        l10n_key_title=LK.dc_spain_madrid
                    ),
                ],
                symbol="🇪🇸",
                l10n_key_title=LK.dc_spain_title
            )
        ],
        LK.dc_west
    )

    EU_EAST = DatacenterGroup(
        "eu_east",
        [
            DatacenterRegion(
                "austria",
                [
                    Datacenter(
                        "vienna",
                        l10n_key_title=LK.dc_austria_vienna
                    ),
                ],
                symbol="🇦🇹",
                l10n_key_title=LK.dc_austria_title
            ),
            DatacenterRegion(
                "poland",
                [
                    Datacenter(
                        "warsaw",
                        l10n_key_title=LK.dc_poland_warsaw
                    ),
                ],
                symbol="🇵🇱",
                l10n_key_title=LK.dc_poland_title
            )
        ],
        LK.dc_east
    )

    US_NORTH = DatacenterGroup(
        "us_north",
        [
            DatacenterRegion(
                "northcentral",
                [
                    Datacenter(
                        "chicago",
                        l10n_key_title=LK.dc_us_north_central_chicago
                    ),
                ],
                symbol="🇺🇸",
                l10n_key_title=LK.dc_us_north_central_title
            ),
            DatacenterRegion(
                "northeast",
                [
                    Datacenter(
                        "sterling",
                        l10n_key_title=LK.dc_us_north_east_sterling
                    ),
                ],
                symbol="🇺🇸",
                l10n_key_title=LK.dc_us_north_east_title
            ),
            DatacenterRegion(
                "northwest",
                [
                    Datacenter(
                        "moses_lake",
                        l10n_key_title=LK.dc_us_north_west_moses_lake
                    ),
                ],
                symbol="🇺🇸",
                l10n_key_title=LK.dc_us_north_west_title
            )
        ],
        LK.dc_north
    )

    US_SOUTH = DatacenterGroup(
        "us_south",
        [
            DatacenterRegion(
                "southwest",
                [
                    Datacenter(
                        "los_angeles",
                        l10n_key_title=LK.dc_us_south_west_los_angeles
                    ),
                ],
                symbol="🇺🇸",
                l10n_key_title=LK.dc_us_south_west_title
            ),
            DatacenterRegion(
                "southeast",
                [
                    Datacenter(
                        "atlanta",
                        l10n_key_title=LK.dc_us_south_east_atlanta
                    ),
                ],
                symbol="🇺🇸",
                l10n_key_title=LK.dc_us_south_east_title
            )
        ],
        LK.dc_south
    )

    SOUTH_AMERICA = DatacenterGroup(
        "south_america",
        [
            DatacenterRegion(
                "brazil",
                [
                    Datacenter(
                        "sao_paulo",
                        l10n_key_title=LK.dc_brazil_sao_paulo
                    ),
                ],
                symbol="🇧🇷",
                l10n_key_title=LK.dc_brazil_title
            ),
            DatacenterRegion(
                "chile",
                [
                    Datacenter(
                        "santiago",
                        l10n_key_title=LK.dc_chile_santiago
                    ),
                ],
                symbol="🇨🇱",
                l10n_key_title=LK.dc_chile_title
            ),
            DatacenterRegion(
                "peru",
                [
                    Datacenter(
                        "lima",
                        l10n_key_title=LK.dc_peru_lima
                    ),
                ],
                symbol="🇵🇪",
                l10n_key_title=LK.dc_peru_title
            ),
            DatacenterRegion(
                "argentina",
                [
                    Datacenter(
                        "buenos_aires",
                        l10n_key_title=LK.dc_argentina_buenos_aires
                    ),
                ],
                symbol="🇦🇷",
                l10n_key_title=LK.dc_argentina_title
            )
        ],
        LK.dc_southamerica
    )

    HONGKONG = Datacenter(
        "hongkong",
        "🇭🇰",
        LK.dc_hongkong,
        LK.dc_hongkong_title
    )

    INDIA = DatacenterRegion(
        "india",
        [
            Datacenter(
                "mumbai",
                l10n_key_title=LK.dc_india_mumbai
            ),
            Datacenter(
                "chennai",
                l10n_key_title=LK.dc_india_chennai
            )
        ],
        "🇮🇳",
        LK.dc_india, 
        LK.dc_india_title
    )

    CHINA = DatacenterRegion(
        "china",
        [
            Datacenter(
                "shanghai",
                l10n_key_title=LK.dc_china_shanghai
            ),
            Datacenter(
                "tianjin",
                l10n_key_title=LK.dc_china_tianjin
            ),
            Datacenter(
                "guangzhou",
                l10n_key_title=LK.dc_china_guangzhou
            )
        ],
        "🇨🇳",
        LK.dc_china, 
        LK.dc_china_title
    )

    SOUTH_KOREA = DatacenterRegion(
        "south_korea",
        [
            Datacenter(
                "seoul",
                l10n_key_title=LK.dc_southkorea_seoul
            ),
        ],
        "🇰🇷",
        LK.dc_southkorea, 
        LK.dc_southkorea_title
    )

    SINGAPORE = Datacenter(
        "singapore",
        "🇸🇬",
        LK.dc_singapore,
        LK.dc_singapore_title
    )

    EMIRATES = DatacenterRegion(
        "emirates",
        [
            Datacenter(
                "dubai",
                l10n_key_title=LK.dc_emirates_dubai
            ),
        ],
        "🇦🇪",
        LK.dc_emirates, 
        LK.dc_emirates_title
    )

    JAPAN = DatacenterRegion(
        "japan",
        [
            Datacenter(
                "tokyo",
                l10n_key_title=LK.dc_japan_tokyo
            ),
        ],
        "🇯🇵",
        LK.dc_japan, 
        LK.dc_japan_title
    )

    @staticmethod
    def get_data(_obj: Datacenter | DatacenterRegion | DatacenterGroup):
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache_file = json.load(f)
            
        if isinstance(_obj, Datacenter):
            data = cache_file['datacenters'][_obj.id]
            capacity, load = States.get(data['capacity']), States.get(data['load'])
            return DatacenterState(_obj, capacity, load)
        
        if isinstance(_obj, DatacenterRegion):
            obj_data = cache_file['datacenters'][_obj.id]
            states = []

            for dc in _obj.datacenters:
                data = obj_data[dc.id]
                capacity, load = States.get(data['capacity']), States.get(data['load'])
                states.append(DatacenterState(dc, capacity, load))

            return DatacenterRegionState(_obj, states)
        
        if isinstance(_obj, DatacenterGroup):
            obj_data = cache_file['datacenters'][_obj.id]
            region_states = []

            for region in _obj.regions:
                region_data = obj_data[region.id]

                states = []
                for dc in region.datacenters:
                    data = region_data[dc.id]
                    capacity, load = States.get(data['capacity']), States.get(data['load'])

                    states.append(DatacenterState(dc, capacity, load))
                region_states.append(DatacenterRegionState(region, states))

            return DatacenterGroupState(_obj, region_states)
    
    @classmethod
    def available_dcs(cls):
        return (v for k, v in vars(DatacenterAtlas).items()
                if not (k.startswith('__') or callable(v)))


class DatacenterInlineResult(NamedTuple):
    title: str
    thumbnail: str
    summary_from: callable
    tags: list
