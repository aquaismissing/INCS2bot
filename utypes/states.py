from __future__ import annotations

from typing import NamedTuple

# noinspection PyPep8Naming
from l10n import LocaleKeys as LK


__all__ = ('State', 'States')


class State(NamedTuple):
    literal: str
    l10n_key: str


class States:
    LOW = State('low', LK.states_low)
    MEDIUM = State('medium', LK.states_medium)
    HIGH = State('high', LK.states_high)
    FULL = State('full', LK.states_full)
    NORMAL = State('normal', LK.states_normal)
    SURGE = State('surge', LK.states_surge)
    DELAYED = State('delayed', LK.states_delayed)
    IDLE = State('idle', LK.states_idle)
    OFFLINE = State('offline', LK.states_offline)
    CRITICAL = State('critical', LK.states_critical)
    INTERNAL_SERVER_ERROR = State('internal server error', LK.states_internal_server_error)
    INTERNAL_BOT_ERROR = State('internal bot error', LK.states_internal_bot_error)
    RELOADING = State('reloading', LK.states_reloading)
    INTERNAL_STEAM_ERROR = State('internal Steam error', LK.states_internal_steam_error)
    UNKNOWN = State('unknown', LK.states_unknown)

    @classmethod
    def get(cls, data: str) -> State | None:
        data = data.replace(' ', '_').upper()
        try:
            return getattr(cls, data)
        except KeyError:
            return

    @classmethod
    def sget(cls, data: str | None) -> State:
        """Same as States.get(), but returns States.UNKNOWN if there's no such state or `data is None`."""
        if data is None:
            return States.UNKNOWN
        st = cls.get(data)

        return st if st is not None else States.UNKNOWN
