from babel import Locale as BabelLocale, UnknownLocaleError

from l10n import Locale, locale as _loc, get_available_languages as _gal


CIS_LANG_CODES = ('kk',)


def locale(lang: str = 'en') -> Locale:
    """Returns a Locale object based of user's language."""

    if lang in CIS_LANG_CODES and lang not in get_available_languages():
        lang = 'ru'

    return _loc(lang)


def get_refined_lang_code(_locale: Locale) -> str:
    """Get refined lang code that Babel can accept."""
    lang_code = _locale.lang_code.replace('-', '_')

    try:
        BabelLocale.parse(lang_code)
    except UnknownLocaleError:
        lang_code = 'en'

    return lang_code


def get_available_languages() -> dict[str, str]:
    """Returns a dictionary with lang codes as keys and lang names as values."""

    return _gal()
