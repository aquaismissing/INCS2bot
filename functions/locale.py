from l10n import Locale, locale as _loc


CIS_LANG_CODES = ('be', 'kk')


def locale(lang: str = 'en') -> Locale:
    """Returns a Locale object based of user's language."""

    if lang in CIS_LANG_CODES:
        lang = 'ru'

    return _loc(lang)


def get_refined_lang_code(_locale: Locale) -> str:
    """Get refined lang code that Babel can accept."""

    return _locale.lang_code.replace('-', '_')
