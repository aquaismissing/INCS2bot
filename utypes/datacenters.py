import json
from typing import NamedTuple

import config
from .states import State, States
# noinspection PyPep8Naming
from l10n import LocaleKeys as LK


__all__ = ('DatacenterAtlas',
           'Datacenter', 'DatacenterRegion', 'DatacenterGroup',
           'DatacenterState', 'DatacenterRegionState', 'DatacenterGroupState',
           'DatacenterInlineResult',
           'DatacenterVariation', 'DatacenterStateVariation')


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


DatacenterVariation = Datacenter | DatacenterRegion | DatacenterGroup
DatacenterStateVariation = DatacenterState | DatacenterRegionState | DatacenterGroupState


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
        LK.regions_africa,
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
        LK.regions_australia,
        LK.dc_australia_title
    )

    AUSTRIA = DatacenterRegion(
        "austria",
        [
            Datacenter(
                "vienna",
                l10n_key_title=LK.dc_austria_vienna
            ),
        ],
        "🇦🇹",
        LK.dc_austria,
        LK.dc_austria_title
    )

    FINLAND = DatacenterRegion(
        "finland",
        [
            Datacenter(
                "helsinki",
                l10n_key_title=LK.dc_finland_helsinki
            ),
        ],
        "🇫🇮",
        LK.dc_finland,
        LK.dc_finland_title
    )

    GERMANY = DatacenterRegion(
        "germany",
        [
            Datacenter(
                "frankfurt",
                l10n_key_title=LK.dc_germany_frankfurt
            ),
        ],
        "🇩🇪",
        LK.dc_germany,
        LK.dc_germany_title
    )

    NETHERLANDS = DatacenterRegion(
        "netherlands",
        [
            Datacenter(
                "amsterdam",
                l10n_key_title=LK.dc_netherlands_amsterdam
            ),
        ],
        "🇳🇱",
        LK.dc_netherlands,
        LK.dc_netherlands_title
    )

    POLAND = DatacenterRegion(
        "poland",
        [
            Datacenter(
                "warsaw",
                l10n_key_title=LK.dc_poland_warsaw
            ),
        ],
        "🇵🇱",
        LK.dc_poland,
        LK.dc_poland_title
    )

    SPAIN = DatacenterRegion(
        "spain",
        [
            Datacenter(
                "madrid",
                l10n_key_title=LK.dc_spain_madrid
            ),
        ],
        "🇪🇸",
        LK.dc_spain,
        LK.dc_spain_title
    )

    SWEDEN = DatacenterRegion(
        "sweden",
        [
            Datacenter(
                "stockholm",
                l10n_key_title=LK.dc_sweden_stockholm
            ),
        ],
        "🇸🇪",
        LK.dc_sweden,
        LK.dc_sweden_title
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
                        "new_york",
                        l10n_key_title=LK.dc_us_north_west_new_york
                    ),
                    Datacenter(
                        "seattle",
                        l10n_key_title=LK.dc_us_north_west_seattle
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

    ARGENTINA = DatacenterRegion(
        "argentina",
        [
            Datacenter(
                "buenos_aires",
                l10n_key_title=LK.dc_argentina_buenos_aires
            ),
        ],
        "🇦🇷",
        LK.dc_argentina,
        LK.dc_argentina_title
    )

    BRAZIL = DatacenterRegion(
        "brazil",
        [
            Datacenter(
                "sao_paulo",
                l10n_key_title=LK.dc_brazil_sao_paulo
            ),
        ],
        "🇧🇷",
        LK.dc_brazil,
        LK.dc_brazil_title
    )

    CHILE = DatacenterRegion(
        "chile",
        [
            Datacenter(
                "santiago",
                l10n_key_title=LK.dc_chile_santiago
            ),
        ],
        "🇨🇱",
        LK.dc_chile,
        LK.dc_chile_title
    )

    PERU = DatacenterRegion(
        "peru",
        [
            Datacenter(
                "lima",
                l10n_key_title=LK.dc_peru_lima
            ),
        ],
        "🇵🇪",
        LK.dc_peru,
        LK.dc_peru_title
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
            ),
            Datacenter(
                "bombay",
                l10n_key_title=LK.dc_india_bombay
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
            ),
            Datacenter(
                "chengdu",
                l10n_key_title=LK.dc_china_chengdu
            )
        ],
        "🇨🇳",
        LK.regions_china,
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
    def get_state(_obj: DatacenterVariation) -> DatacenterStateVariation:
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
