from babel.dates import format_datetime

from utypes import (DatacenterAtlas,
                    DatacenterVariation,
                    DatacenterState, DatacenterRegionState, DatacenterGroupState,
                    GameServersData, States)


def _format_dc_data(dc: DatacenterVariation, lang_code: str):
    from functions import locale

    game_servers_datetime = GameServersData.latest_info_update()
    if game_servers_datetime == States.UNKNOWN:
        return States.UNKNOWN

    game_servers_datetime = (f'{format_datetime(game_servers_datetime, "HH:mm:ss, dd MMM", locale=lang_code).title()}'
                             f' (UTC)')

    state = DatacenterAtlas.get_state(dc)
    loc = locale(lang_code)

    if isinstance(state, DatacenterState):
        header = loc.dc_status_text_title.format(state.dc.symbol,
                                                 loc.get(state.dc.l10n_key_title))
        summary = loc.dc_status_text_summary_city.format(loc.get(state.load.l10n_key),
                                                         loc.get(state.capacity.l10n_key))
        return '\n\n'.join((header, summary, loc.latest_data_update.format(game_servers_datetime)))

    if isinstance(state, DatacenterRegionState):
        header = loc.dc_status_text_title.format(state.region.symbol,
                                                 loc.get(state.region.l10n_key_title))
        summaries = []
        for dc_state in state.states:
            summary = loc.dc_status_text_summary.format(loc.get(dc_state.dc.l10n_key_title),
                                                        loc.get(dc_state.load.l10n_key),
                                                        loc.get(dc_state.capacity.l10n_key))
            summaries.append(summary)
        return '\n\n'.join((header, '\n\n'.join(summaries), loc.latest_data_update.format(game_servers_datetime)))
    
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
        return '\n\n'.join((*infos, loc.latest_data_update.format(game_servers_datetime)))


def africa(lang_code: str):
    return _format_dc_data(DatacenterAtlas.AFRICA, lang_code)


def australia(lang_code: str):
    return _format_dc_data(DatacenterAtlas.AUSTRALIA, lang_code)


def eu_north(lang_code: str):
    return _format_dc_data(DatacenterAtlas.EU_NORTH, lang_code)


def eu_west(lang_code: str):
    return _format_dc_data(DatacenterAtlas.EU_WEST, lang_code)


def eu_east(lang_code: str):
    return _format_dc_data(DatacenterAtlas.EU_EAST, lang_code)


def us_north(lang_code: str):
    return _format_dc_data(DatacenterAtlas.US_NORTH, lang_code)


def us_south(lang_code: str):
    return _format_dc_data(DatacenterAtlas.US_SOUTH, lang_code)


def south_america(lang_code: str):
    return _format_dc_data(DatacenterAtlas.SOUTH_AMERICA, lang_code)


def india(lang_code: str):
    return _format_dc_data(DatacenterAtlas.INDIA, lang_code)


def japan(lang_code: str):
    return _format_dc_data(DatacenterAtlas.JAPAN, lang_code)


def china(lang_code: str):
    return _format_dc_data(DatacenterAtlas.CHINA, lang_code)


def emirates(lang_code: str):
    return _format_dc_data(DatacenterAtlas.EMIRATES, lang_code)


def singapore(lang_code: str):
    return _format_dc_data(DatacenterAtlas.SINGAPORE, lang_code)


def hongkong(lang_code: str):
    return _format_dc_data(DatacenterAtlas.HONGKONG, lang_code)


def south_korea(lang_code: str):
    return _format_dc_data(DatacenterAtlas.SOUTH_KOREA, lang_code)
