from l10n import Locale, locale as _loc


CIS_LANG_CODES = 'ru', 'uk', 'be', 'uz', 'kk'


def locale(lang: str | None) -> Locale:
    """Returns a Locale object based of user's language."""

    if lang in CIS_LANG_CODES:
        lang = 'ru'
    return _loc(lang)
