from __future__ import annotations
import json
from pathlib import Path
from typing import NamedTuple
import warnings


__all__ = ('Tags', 'TagsKeys', 'dump_tags')

# todo: probably rewrite it cuz it's basically a L10n clone


class UnexpectedTagKey(UserWarning):
    pass


class UndefinedTagKey(UserWarning):
    pass


class PrimaryTagsFileNotFound(UserWarning):
    pass


class Tags(NamedTuple):
    """Object containing all the tags required by Telegram API. Tags
       can be accessed as object attributes or by string keys using
       get(key) method. Can be converted to dict using to_dict() method."""

    dc_africa: list  # South Africa
    dc_australia: list  # Australia

    dc_southamerica: list  # South America
    dc_southamerica_argentina: list  # Argentina
    dc_southamerica_brazil: list  # Brazil
    dc_southamerica_chile: list  # Chile
    dc_southamerica_peru: list  # Peru

    dc_europe: list  # Europe
    dc_europe_austria: list  # Austria
    dc_europe_finland: list  # Finland
    dc_europe_germany: list  # Germany
    dc_europe_netherlands: list  # Netherlands
    dc_europe_poland: list  # Poland
    dc_europe_spain: list  # Spain
    dc_europe_sweden: list  # Sweden

    dc_us: list  # USA
    dc_us_east: list  # East
    dc_us_west: list  # West

    dc_asia: list  # Asia
    dc_asia_india: list  # India
    dc_asia_japan: list  # Japan
    dc_asia_china: list  # China
    dc_asia_emirates: list  # Emirates
    dc_asia_singapore: list  # Singapore
    dc_asia_hongkong: list  # Hong Kong
    dc_asia_southkorea: list  # South Korea

    currencies_usd: list  # U.S. Dollar
    currencies_gbp: list  # British Pound
    currencies_eur: list  # Euro
    currencies_rub: list  # Russian Ruble
    currencies_brl: list  # Brazilian Real
    currencies_jpy: list  # Japanese Yen
    currencies_nok: list  # Norwegian Krone
    currencies_idr: list  # Indonesian Rupiah
    currencies_myr: list  # Malaysian Ringgit
    currencies_php: list  # Philippine Peso
    currencies_sgd: list  # Singapore Dollar
    currencies_thb: list  # Thai Baht
    currencies_vnd: list  # Vietnamese Dong
    currencies_krw: list  # South Korean Won
    currencies_uah: list  # Ukrainian Hryvnia
    currencies_mxn: list  # Mexican Peso
    currencies_cad: list  # Canadian Dollar
    currencies_aud: list  # Australian Dollar
    currencies_nzd: list  # New Zealand Dollar
    currencies_pln: list  # Polish Zloty
    currencies_chf: list  # Swiss Franc
    currencies_aed: list  # U.A.E. Dirham
    currencies_clp: list  # Chilean Peso
    currencies_cny: list  # Chinese Yuan
    currencies_cop: list  # Colombian Peso
    currencies_pen: list  # Peruvian Sol
    currencies_sar: list  # Saudi Riyal
    currencies_twd: list  # Taiwan Dollar
    currencies_hkd: list  # Hong Kong Dollar
    currencies_zar: list  # South African Rand
    currencies_inr: list  # Indian Rupee
    currencies_crc: list  # Costa Rican Colon
    currencies_ils: list  # Israeli Shekel
    currencies_kwd: list  # Kuwaiti Dinar
    currencies_qar: list  # Qatari Riyal
    currencies_uyu: list  # Uruguayan Peso
    currencies_kzt: list  # Kazakhstani Tenge

    def to_dict(self) -> dict[str, list]:
        """Returns a dict converted from a Tags object."""

        return self._asdict()

    def to_set(self) -> set:
        """Returns a set converted from a Tags object."""

        result = set()
        for tags in self._asdict().values():
            result.update(tags)
        return set(result)

    def dcs_to_set(self) -> set:
        """Returns a datacenters set of converted from a Tags object."""

        result = set()
        for k, tags in self._asdict().items():
            if k.startswith('dc'):
                result.update(tags)
        return set(result)

    def to_list(self) -> list:
        """Returns a list converted from a Tags object."""

        result = []
        for tags in self._asdict().values():
            result.extend(tags)
        return result

    def currencies_to_list(self) -> list:
        """Returns a currency list converted from a Tags object."""

        result = []
        for k, tags in self._asdict().items():
            if k.startswith('currencies'):
                result.extend(tags)
        return result

    def currencies_to_dict(self) -> dict:
        """Returns a set converted from a Tags object."""

        result = {}
        for k, tags in self._asdict().items():
            if k.startswith('currencies'):
                result[tags[0]] = tags
        return result

    def get(self, key: str) -> str:
        """Returns tags list associated with the given key (if such
           key exists, otherwise returns the key itself)."""

        if key not in self._fields:
            warnings.warn(f'Got unexpected key "{key}", returned the key', UnexpectedTagKey, stacklevel=2)
            return key
        return getattr(self, key)

    @classmethod
    def sample(cls) -> Tags:
        """Returns a sample Tags object with key names as values"""
        return cls(**{field: field for field in cls._fields})


TagsKeys = Tags.sample()


def dump_tags() -> Tags:
    """Dumps "tags.json" and returns Tags object, containing all defined tags lists.
    """
    path = Path(__file__).parent / 'data' / 'tags.json'
    if not path.exists():
        warnings.warn(f"Can't find tags.json, generating a file...", PrimaryTagsFileNotFound)
        sample = Tags.sample()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({k: [v] for k, v in sample.to_dict().items()}, f, indent=4, ensure_ascii=False)

    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    # Add undefined fields
    found_undefined_fields = False
    for field in Tags._fields:
        if field not in data:
            warnings.warn(f'Found undefined tags field "{field}" in "tags.json"', UndefinedTagKey, stacklevel=2)
            data[field] = [field]
            found_undefined_fields = True

    # Find unexpected fields
    unexpected_fields = []
    for field in tuple(data):
        if field not in Tags._fields:
            warnings.warn(f'Got unexpected tags field "{field}" in "tags.json"', UnexpectedTagKey, stacklevel=2)
            unexpected_fields.append(field)

    # Dump data with undefined and unexpected fields
    if found_undefined_fields or unexpected_fields:
        with open(path, 'w', encoding='utf-8') as f:
            data = {field: data[field] for field in Tags._fields + tuple(unexpected_fields)}  # fixing pairs order
            json.dump(data, f, indent=4, ensure_ascii=False)

    # Remove unexpected fields
    for field in unexpected_fields:
        del data[field]

    for og_field, og_tags in data.items():
        for field, tags in data.items():
            if og_field != field and field.startswith(og_field):
                data[field].extend(og_tags)

    return Tags(**data)
