from babel.dates import format_datetime

from utypes import (
    States, DatacenterAtlas, DatacenterState,
    DatacenterRegionState, DatacenterGroupState,
    GameServersData)
from l10n import Locale


def _format_dc_data(state: DatacenterState | DatacenterRegionState | DatacenterGroupState, loc: Locale):
    if isinstance(state, DatacenterState):
        header = loc.dc_status_text_title.format(state.dc.symbol,
                                                 loc.get(state.dc.l10n_key_title))
        summary = loc.dc_status_text_summary_city.format(loc.get(state.load.l10n_key),
                                                         loc.get(state.capacity.l10n_key))
        return '\n\n'.join((header, summary))

    if isinstance(state, DatacenterRegionState):
        header = loc.dc_status_text_title.format(state.region.symbol,
                                                 loc.get(state.region.l10n_key_title))
        summaries = []
        for dc_state in state.states:
            summary = loc.dc_status_text_summary.format(loc.get(dc_state.dc.l10n_key_title),
                                                        loc.get(dc_state.load.l10n_key),
                                                        loc.get(dc_state.capacity.l10n_key))
            summaries.append(summary)
        return '\n\n'.join((header, '\n\n'.join(summaries)))
    
    if isinstance(state, DatacenterGroupState):
        infos = []
        for region_state in state.region_states:
            header = loc.dc_status_text_title.format(region_state.region.symbol,
                                                     loc.get(region_state.region.l10n_key_title))
            summaries = []
            for dc_state in region_state.states:
                summary = loc.dc_status_text_summary.format(loc.get(dc_state.dc.l10n_key_title),
                                                            loc.get(dc_state.load.l10n_key),
                                                            loc.get(dc_state.capacity.l10n_key))
                summaries.append(summary)
            infos.append(header + '\n\n' + '\n\n'.join(summaries))
        return '\n\n'.join(infos)


def africa(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.AFRICA), loc)


def australia(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.AUSTRALIA), loc)


def eu_north(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.EU_NORTH), loc)


def eu_west(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.EU_WEST), loc)


def eu_east(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.EU_EAST), loc)


def us_north(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.US_NORTH), loc)


def us_south(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.US_SOUTH), loc)


def south_america(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.SOUTH_AMERICA), loc)


def india(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.INDIA), loc)


def japan(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.JAPAN), loc)


def china(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.CHINA), loc)


def emirates(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.EMIRATES), loc)


def singapore(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.SINGAPORE), loc)


def hongkong(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.HONGKONG), loc)


def south_korea(loc: Locale):
    return _format_dc_data(DatacenterAtlas.get_data(DatacenterAtlas.SOUTH_KOREA), loc)
