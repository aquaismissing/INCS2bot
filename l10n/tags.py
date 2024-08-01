from __future__ import annotations
import json
from pathlib import Path
from typing import NamedTuple
import warnings


__all__ = ('Tags', 'TagsKeys', 'load_tags')

# todo: probably rewrite it cuz it's basically a L10n clone


class UnexpectedTagKey(UserWarning):
    pass


class UndefinedTagKey(UserWarning):
    pass


class PrimaryTagsFileNotFound(UserWarning):
    pass


class Tags(NamedTuple):
    """Object containing all the tags required for inline search. Tags
       can be accessed as object attributes or by string keys using
       get(key) method. Can be converted to dict using to_dict() method."""

    dc_africa: set  # South Africa
    dc_australia: set  # Australia

    dc_southamerica: set  # South America
    dc_southamerica_argentina: set  # Argentina
    dc_southamerica_brazil: set  # Brazil
    dc_southamerica_chile: set  # Chile
    dc_southamerica_peru: set  # Peru

    dc_europe: set  # Europe
    dc_europe_austria: set  # Austria
    dc_europe_finland: set  # Finland
    dc_europe_germany: set  # Germany
    dc_europe_netherlands: set  # Netherlands
    dc_europe_poland: set  # Poland
    dc_europe_spain: set  # Spain
    dc_europe_sweden: set  # Sweden
    dc_europe_uk: set  # United Kingdom

    dc_us: set  # USA
    dc_us_east: set  # East
    dc_us_west: set  # West

    dc_asia: set  # Asia
    dc_asia_india: set  # India
    dc_asia_japan: set  # Japan
    dc_asia_china: set  # China
    dc_asia_emirates: set  # Emirates
    dc_asia_singapore: set  # Singapore
    dc_asia_hongkong: set  # Hong Kong
    dc_asia_southkorea: set  # South Korea

    currencies_usd: set  # U.S. Dollar
    currencies_gbp: set  # British Pound
    currencies_eur: set  # Euro
    currencies_rub: set  # Russian Ruble
    currencies_brl: set  # Brazilian Real
    currencies_jpy: set  # Japanese Yen
    currencies_nok: set  # Norwegian Krone
    currencies_idr: set  # Indonesian Rupiah
    currencies_myr: set  # Malaysian Ringgit
    currencies_php: set  # Philippine Peso
    currencies_sgd: set  # Singapore Dollar
    currencies_thb: set  # Thai Baht
    currencies_vnd: set  # Vietnamese Dong
    currencies_krw: set  # South Korean Won
    currencies_uah: set  # Ukrainian Hryvnia
    currencies_mxn: set  # Mexican Peso
    currencies_cad: set  # Canadian Dollar
    currencies_aud: set  # Australian Dollar
    currencies_nzd: set  # New Zealand Dollar
    currencies_pln: set  # Polish Zloty
    currencies_chf: set  # Swiss Franc
    currencies_aed: set  # U.A.E. Dirham
    currencies_clp: set  # Chilean Peso
    currencies_cny: set  # Chinese Yuan
    currencies_cop: set  # Colombian Peso
    currencies_pen: set  # Peruvian Sol
    currencies_sar: set  # Saudi Riyal
    currencies_twd: set  # Taiwan Dollar
    currencies_hkd: set  # Hong Kong Dollar
    currencies_zar: set  # South African Rand
    currencies_inr: set  # Indian Rupee
    currencies_crc: set  # Costa Rican Colon
    currencies_ils: set  # Israeli Shekel
    currencies_kwd: set  # Kuwaiti Dinar
    currencies_qar: set  # Qatari Riyal
    currencies_uyu: set  # Uruguayan Peso
    currencies_kzt: set  # Kazakhstani Tenge

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
            if k.startswith('currencies_'):
                result[k.removeprefix('currencies_')] = tags
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


def load_tags() -> Tags:
    """Loads "tags.json" and returns Tags object, containing all defined tags lists."""

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

    # Turn arrays into sets
    data = {field: set(value) for field, value in data.items()}

    for parent_field, parent_tags in data.items():
        for field, tags in data.items():
            if parent_field != field and field.startswith(parent_field):
                data[field].update(parent_tags)

    return Tags(**data)


if __name__ == '__main__':
    load_tags()
