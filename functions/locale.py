from l10n import Locale, locale as _loc, get_available_languages as _gal


CIS_LANG_CODES = ('be', 'kk')


def locale(lang: str = 'en') -> Locale:
    """Returns a Locale object based of user's language."""

    if lang in CIS_LANG_CODES:
        lang = 'ru'

    return _loc(lang)


def get_refined_lang_code(_locale: Locale) -> str:
    """Get refined lang code that Babel can accept."""

    return _locale.lang_code.replace('-', '_')


def get_available_languages() -> dict[str, str]:
    """Returns a dictionary with lang codes as keys and lang names as values."""

    return _gal()
