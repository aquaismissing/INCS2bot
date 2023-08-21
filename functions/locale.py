from l10n import Locale, locale as _loc


CIS_LANG_CODES = ('be', 'kk', 'ru')


def locale(lang: str = 'en') -> Locale:
    """Returns a Locale object based of user's language."""

    if lang in CIS_LANG_CODES:
        lang = 'ru'

    return _loc(lang)
