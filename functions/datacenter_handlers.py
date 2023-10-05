from babel.dates import format_datetime

from l10n import Locale
from .locale import get_refined_lang_code
from utypes import (DatacenterAtlas,
                    DatacenterVariation,
                    DatacenterState, DatacenterRegionState, DatacenterGroupState,
                    GameServersData, States)


def _format_dc_data(dc: DatacenterVariation, locale: Locale):
    game_servers_datetime = GameServersData.latest_info_update()
    if game_servers_datetime is States.UNKNOWN:
        return States.UNKNOWN

    lang_code = get_refined_lang_code(locale)

    game_servers_datetime = (f'{format_datetime(game_servers_datetime, "HH:mm:ss, dd MMM", locale=lang_code).title()}'
                             f' (UTC)')

    state = DatacenterAtlas.get_state(dc)

    if isinstance(state, DatacenterState):
        header = locale.dc_status_text_title.format(state.dc.symbol,
                                                    locale.get(state.dc.l10n_key_title))
        summary = locale.dc_status_text_summary_city.format(locale.get(state.load.l10n_key),
                                                            locale.get(state.capacity.l10n_key))
        return '\n\n'.join((header, summary, locale.latest_data_update.format(game_servers_datetime)))

    if isinstance(state, DatacenterRegionState):
        header = locale.dc_status_text_title.format(state.region.symbol,
                                                    locale.get(state.region.l10n_key_title))
        summaries = []
        for dc_state in state.states:
            summary = locale.dc_status_text_summary.format(locale.get(dc_state.dc.l10n_key_title),
                                                           locale.get(dc_state.load.l10n_key),
                                                           locale.get(dc_state.capacity.l10n_key))
            summaries.append(summary)
        return '\n\n'.join((header, '\n\n'.join(summaries), locale.latest_data_update.format(game_servers_datetime)))

    if isinstance(state, DatacenterGroupState):
        infos = []
        for region_state in state.region_states:
            header = locale.dc_status_text_title.format(region_state.region.symbol,
                                                        locale.get(region_state.region.l10n_key_title))
            summaries = []
            for dc_state in region_state.states:
                summary = locale.dc_status_text_summary.format(locale.get(dc_state.dc.l10n_key_title),
                                                               locale.get(dc_state.load.l10n_key),
                                                               locale.get(dc_state.capacity.l10n_key))
                summaries.append(summary)
            infos.append(header + '\n\n' + '\n\n'.join(summaries))
        return '\n\n'.join((*infos, locale.latest_data_update.format(game_servers_datetime)))


def africa(locale: Locale):
    return _format_dc_data(DatacenterAtlas.AFRICA, locale)


def australia(locale: Locale):
    return _format_dc_data(DatacenterAtlas.AUSTRALIA, locale)


def austria(locale: Locale):
    return _format_dc_data(DatacenterAtlas.AUSTRIA, locale)


def germany(locale: Locale):
    return _format_dc_data(DatacenterAtlas.GERMANY, locale)


def netherlands(locale: Locale):
    return _format_dc_data(DatacenterAtlas.NETHERLANDS, locale)


def poland(locale: Locale):
    return _format_dc_data(DatacenterAtlas.POLAND, locale)


def spain(locale: Locale):
    return _format_dc_data(DatacenterAtlas.SPAIN, locale)


def sweden(locale: Locale):
    return _format_dc_data(DatacenterAtlas.SWEDEN, locale)


def us_north(locale: Locale):
    return _format_dc_data(DatacenterAtlas.US_NORTH, locale)


def us_south(locale: Locale):
    return _format_dc_data(DatacenterAtlas.US_SOUTH, locale)


def south_america(locale: Locale):
    return _format_dc_data(DatacenterAtlas.SOUTH_AMERICA, locale)


def india(locale: Locale):
    return _format_dc_data(DatacenterAtlas.INDIA, locale)


def japan(locale: Locale):
    return _format_dc_data(DatacenterAtlas.JAPAN, locale)


def china(locale: Locale):
    return _format_dc_data(DatacenterAtlas.CHINA, locale)


def emirates(locale: Locale):
    return _format_dc_data(DatacenterAtlas.EMIRATES, locale)


def singapore(locale: Locale):
    return _format_dc_data(DatacenterAtlas.SINGAPORE, locale)


def hongkong(locale: Locale):
    return _format_dc_data(DatacenterAtlas.HONGKONG, locale)


def south_korea(locale: Locale):
    return _format_dc_data(DatacenterAtlas.SOUTH_KOREA, locale)
