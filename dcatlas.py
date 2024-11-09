from l10n import LocaleKeys as LK
from utypes import Datacenter, DatacenterRegion


__all__ = ['DatacenterAtlas']


class DatacenterAtlas:
    AFRICA = DatacenterRegion(
        "south_africa",
        [
            Datacenter("johannesburg", l10n_key_title=LK.dc_africa_johannesburg),
        ],
        "🇿🇦",
        LK.regions_africa,
        LK.dc_africa_title
    )

    AUSTRALIA = DatacenterRegion(
        "australia",
        [
            Datacenter("sydney", l10n_key_title=LK.dc_australia_sydney),
        ],
        "🇦🇺",
        LK.regions_australia,
        LK.dc_australia_title
    )

    AUSTRIA = DatacenterRegion(
        "austria",
        [
            Datacenter("vienna", l10n_key_title=LK.dc_austria_vienna),
        ],
        "🇦🇹",
        LK.dc_austria,
        LK.dc_austria_title
    )

    FINLAND = DatacenterRegion(
        "finland",
        [
            Datacenter("helsinki", l10n_key_title=LK.dc_finland_helsinki),
        ],
        "🇫🇮",
        LK.dc_finland,
        LK.dc_finland_title
    )

    GERMANY = DatacenterRegion(
        "germany",
        [
            Datacenter("frankfurt", l10n_key_title=LK.dc_germany_frankfurt),
        ],
        "🇩🇪",
        LK.dc_germany,
        LK.dc_germany_title
    )

    # NETHERLANDS = DatacenterRegion(
    #     "netherlands",
    #     [
    #         Datacenter("amsterdam", l10n_key_title=LK.dc_netherlands_amsterdam),
    #     ],
    #     "🇳🇱",
    #     LK.dc_netherlands,
    #     LK.dc_netherlands_title
    # )

    POLAND = DatacenterRegion(
        "poland",
        [
            Datacenter("warsaw", l10n_key_title=LK.dc_poland_warsaw),
        ],
        "🇵🇱",
        LK.dc_poland,
        LK.dc_poland_title
    )

    SPAIN = DatacenterRegion(
        "spain",
        [
            Datacenter("madrid", l10n_key_title=LK.dc_spain_madrid),
        ],
        "🇪🇸",
        LK.dc_spain,
        LK.dc_spain_title
    )

    SWEDEN = DatacenterRegion(
        "sweden",
        [
            Datacenter("stockholm", l10n_key_title=LK.dc_sweden_stockholm),
        ],
        "🇸🇪",
        LK.dc_sweden,
        LK.dc_sweden_title
    )

    UK = DatacenterRegion(
        "uk",
        [
            Datacenter("london", l10n_key_title=LK.dc_uk_london),
        ],
        "🇬🇧",
        LK.dc_uk,
        LK.dc_uk_title
    )

    US_EAST = DatacenterRegion(
        "us_east",
        [
            Datacenter("chicago", l10n_key_title=LK.dc_us_chicago),
            Datacenter("sterling", l10n_key_title=LK.dc_us_sterling),
            # Datacenter(
            #     "new_york",
            #     l10n_key_title=LK.dc_us_new_york
            # ),
            Datacenter("atlanta", l10n_key_title=LK.dc_us_atlanta)
        ],
        "🇺🇸",
        LK.dc_east,
        LK.dc_us_east_title
    )

    US_WEST = DatacenterRegion(
        "us_west",
        [
            Datacenter("los_angeles", l10n_key_title=LK.dc_us_los_angeles),
            Datacenter("seattle", l10n_key_title=LK.dc_us_seattle)
        ],
        "🇺🇸",
        LK.dc_west,
        LK.dc_us_west_title
    )

    ARGENTINA = DatacenterRegion(
        "argentina",
        [
            Datacenter("buenos_aires", l10n_key_title=LK.dc_argentina_buenos_aires),
        ],
        "🇦🇷",
        LK.dc_argentina,
        LK.dc_argentina_title
    )

    BRAZIL = DatacenterRegion(
        "brazil",
        [
            Datacenter("sao_paulo", l10n_key_title=LK.dc_brazil_sao_paulo),
        ],
        "🇧🇷",
        LK.dc_brazil,
        LK.dc_brazil_title
    )

    CHILE = DatacenterRegion(
        "chile",
        [
            Datacenter("santiago", l10n_key_title=LK.dc_chile_santiago),
        ],
        "🇨🇱",
        LK.dc_chile,
        LK.dc_chile_title
    )

    PERU = DatacenterRegion(
        "peru",
        [
            Datacenter("lima", l10n_key_title=LK.dc_peru_lima),
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
            # Datacenter(
            #     "bombay",
            #     l10n_key_title=LK.dc_india_bombay
            # ),
            Datacenter("chennai", l10n_key_title=LK.dc_india_chennai),
            # Datacenter(
            #     "madras",
            #     l10n_key_title=LK.dc_india_madras
            # ),
            Datacenter("mumbai", l10n_key_title=LK.dc_india_mumbai),
        ],
        "🇮🇳",
        LK.dc_india,
        LK.dc_india_title
    )

    CHINA = DatacenterRegion(
        "china",
        [
            Datacenter("tianjin", l10n_key_title=LK.dc_china_tianjin),
            Datacenter("guangzhou", l10n_key_title=LK.dc_china_guangzhou),
            Datacenter("chengdu", l10n_key_title=LK.dc_china_chengdu),
            Datacenter("pudong", l10n_key_title=LK.dc_china_pudong),
        ],
        "🇨🇳",
        LK.regions_china,
        LK.dc_china_title
    )

    SOUTH_KOREA = DatacenterRegion(
        "south_korea",
        [
            Datacenter("seoul", l10n_key_title=LK.dc_southkorea_seoul),
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
            Datacenter("dubai", l10n_key_title=LK.dc_emirates_dubai),
        ],
        "🇦🇪",
        LK.dc_emirates,
        LK.dc_emirates_title
    )

    JAPAN = DatacenterRegion(
        "japan",
        [
            Datacenter("tokyo", l10n_key_title=LK.dc_japan_tokyo),
        ],
        "🇯🇵",
        LK.dc_japan,
        LK.dc_japan_title
    )

    @classmethod
    def available_dcs(cls):
        return (v for k, v in vars(DatacenterAtlas).items()
                if not (k.startswith('__') or callable(v)))
