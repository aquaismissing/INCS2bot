from l10n import LocaleKeys as LK
from utypes import Datacenter, DatacenterRegion, DatacenterVariation

__all__ = ["DatacenterAtlas"]


class _DCAtlasMethods:
    @classmethod
    def available_dcs(cls):
        return (v for k, v in vars(cls).items() if isinstance(v, DatacenterVariation))


class DatacenterAtlas(_DCAtlasMethods):
    AFRICA = DatacenterRegion(
        "south_africa",
        [
            Datacenter("johannesburg", associated_api_id="South Africa", l10n_key_title=LK.dc_africa_johannesburg),
        ],
        "🇿🇦",
        LK.regions_africa,
        LK.dc_africa_title
    )

    AUSTRALIA = DatacenterRegion(
        "australia",
        [
            Datacenter("sydney", associated_api_id="Australia", l10n_key_title=LK.dc_australia_sydney),
        ],
        "🇦🇺",
        LK.regions_australia,
        LK.dc_australia_title
    )

    AUSTRIA = DatacenterRegion(
        "austria",
        [
            Datacenter("vienna", associated_api_id="EU Vienna", l10n_key_title=LK.dc_austria_vienna),
        ],
        "🇦🇹",
        LK.dc_austria,
        LK.dc_austria_title
    )

    FINLAND = DatacenterRegion(
        "finland",
        [
            Datacenter("helsinki", associated_api_id="EU Helsinki", l10n_key_title=LK.dc_finland_helsinki),
        ],
        "🇫🇮",
        LK.dc_finland,
        LK.dc_finland_title
    )

    GERMANY = DatacenterRegion(
        "germany",
        [
            Datacenter("frankfurt", associated_api_id="EU Frankfurt", l10n_key_title=LK.dc_germany_frankfurt),
        ],
        "🇩🇪",
        LK.dc_germany,
        LK.dc_germany_title
    )

    # NETHERLANDS = DatacenterRegion(
    #     "netherlands",
    #     [
    #         Datacenter("amsterdam", associated_api_id="EU Holland", l10n_key_title=LK.dc_netherlands_amsterdam),
    #     ],
    #     "🇳🇱",
    #     LK.dc_netherlands,
    #     LK.dc_netherlands_title
    # )

    POLAND = DatacenterRegion(
        "poland",
        [
            Datacenter("warsaw", associated_api_id="EU Warsaw", l10n_key_title=LK.dc_poland_warsaw),
        ],
        "🇵🇱",
        LK.dc_poland,
        LK.dc_poland_title
    )

    SPAIN = DatacenterRegion(
        "spain",
        [
            Datacenter("madrid", associated_api_id="EU Madrid", l10n_key_title=LK.dc_spain_madrid),
        ],
        "🇪🇸",
        LK.dc_spain,
        LK.dc_spain_title
    )

    SWEDEN = DatacenterRegion(
        "sweden",
        [
            Datacenter("stockholm", associated_api_id="EU Stockholm", l10n_key_title=LK.dc_sweden_stockholm),
        ],
        "🇸🇪",
        LK.dc_sweden,
        LK.dc_sweden_title
    )

    UK = DatacenterRegion(
        "uk",
        [
            Datacenter("london", associated_api_id="United Kingdom", l10n_key_title=LK.dc_uk_london),
        ],
        "🇬🇧",
        LK.dc_uk,
        LK.dc_uk_title
    )

    US_EAST = DatacenterRegion(
        "us_east",
        [
            Datacenter("chicago", associated_api_id="US Chicago", l10n_key_title=LK.dc_us_chicago),
            Datacenter("sterling", associated_api_id="US Virginia", l10n_key_title=LK.dc_us_sterling),
            # Datacenter("new_york", associated_api_id="US NewYork", l10n_key_title=LK.dc_us_new_york),
            Datacenter("atlanta", associated_api_id="US Atlanta", l10n_key_title=LK.dc_us_atlanta)
        ],
        "🇺🇸",
        LK.dc_east,
        LK.dc_us_east_title
    )

    US_WEST = DatacenterRegion(
        "us_west",
        [
            Datacenter("los_angeles", associated_api_id="US California", l10n_key_title=LK.dc_us_los_angeles),
            Datacenter("seattle", associated_api_id="US Seattle", l10n_key_title=LK.dc_us_seattle)
        ],
        "🇺🇸",
        LK.dc_west,
        LK.dc_us_west_title
    )

    US_SOUTH = DatacenterRegion(
        "us_south",
        [
            Datacenter("dallas", associated_api_id="US Dallas", l10n_key_title=LK.dc_us_dallas)
        ],
        "🇺🇸",
        LK.dc_south,
        LK.dc_us_south_title
    )

    ARGENTINA = DatacenterRegion(
        "argentina",
        [
            Datacenter("buenos_aires", associated_api_id="Argentina", l10n_key_title=LK.dc_argentina_buenos_aires),
        ],
        "🇦🇷",
        LK.dc_argentina,
        LK.dc_argentina_title
    )

    BRAZIL = DatacenterRegion(
        "brazil",
        [
            Datacenter("sao_paulo", associated_api_id="Brazil", l10n_key_title=LK.dc_brazil_sao_paulo),
        ],
        "🇧🇷",
        LK.dc_brazil,
        LK.dc_brazil_title
    )

    CHILE = DatacenterRegion(
        "chile",
        [
            Datacenter("santiago", associated_api_id="Chile", l10n_key_title=LK.dc_chile_santiago),
        ],
        "🇨🇱",
        LK.dc_chile,
        LK.dc_chile_title
    )

    PERU = DatacenterRegion(
        "peru",
        [
            Datacenter("lima", associated_api_id="Peru", l10n_key_title=LK.dc_peru_lima),
        ],
        "🇵🇪",
        LK.dc_peru,
        LK.dc_peru_title
    )

    HONGKONG = Datacenter(
        "hongkong",
        associated_api_id="Hong Kong",
        symbol="🇭🇰",
        l10n_key_name=LK.dc_hongkong,
        l10n_key_title=LK.dc_hongkong_title
    )

    INDIA = DatacenterRegion(
        "india",
        [
            # Datacenter("bombay", associated_api_id="India Bombay", l10n_key_title=LK.dc_india_bombay),
            Datacenter("chennai", associated_api_id="India Chennai", l10n_key_title=LK.dc_india_chennai),
            # Datacenter("madras", associated_api_id="India Madras", l10n_key_title=LK.dc_india_madras),
            Datacenter("mumbai", associated_api_id="India Mumbai", l10n_key_title=LK.dc_india_mumbai),
        ],
        "🇮🇳",
        LK.dc_india,
        LK.dc_india_title
    )

    CHINA = DatacenterRegion(
        "china",
        [
            # Datacenter("tianjin", associated_api_id="China Tianjin", l10n_key_title=LK.dc_china_tianjin),
            # Datacenter("guangzhou", associated_api_id="China Guangzhou", l10n_key_title=LK.dc_china_guangzhou),
            Datacenter("beijing", associated_api_id="China Beijing", l10n_key_title=LK.dc_china_beijing),
            Datacenter("chengdu", associated_api_id="China Chengdu", l10n_key_title=LK.dc_china_chengdu),
            Datacenter("pudong", associated_api_id="China Pudong", l10n_key_title=LK.dc_china_pudong),
            Datacenter("guangdong", associated_api_id="China Guangdong", l10n_key_title=LK.dc_china_guangdong)
        ],
        "🇨🇳",
        LK.regions_china,
        LK.dc_china_title
    )

    SOUTH_KOREA = DatacenterRegion(
        "south_korea",
        [
            Datacenter("seoul", associated_api_id="South Korea", l10n_key_title=LK.dc_southkorea_seoul),
        ],
        symbol="🇰🇷",
        l10n_key_name=LK.dc_southkorea,
        l10n_key_title=LK.dc_southkorea_title
    )

    SINGAPORE = Datacenter(
        "singapore",
        associated_api_id="Singapore",
        symbol="🇸🇬",
        l10n_key_name=LK.dc_singapore,
        l10n_key_title=LK.dc_singapore_title
    )

    EMIRATES = DatacenterRegion(
        "emirates",
        [
            Datacenter("dubai", associated_api_id="Emirates", l10n_key_title=LK.dc_emirates_dubai),
        ],
        "🇦🇪",
        LK.dc_emirates,
        LK.dc_emirates_title
    )

    JAPAN = DatacenterRegion(
        "japan",
        [
            Datacenter("tokyo", associated_api_id="Japan", l10n_key_title=LK.dc_japan_tokyo),
        ],
        "🇯🇵",
        LK.dc_japan,
        LK.dc_japan_title
    )
