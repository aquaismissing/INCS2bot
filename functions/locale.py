from babel import Locale as BabelLocale, UnknownLocaleError

from l10n import Locale, locale as _loc, get_available_languages


__all__ = ['locale', 'get_refined_lang_code', 'get_available_languages']


def locale(lang: str = 'en') -> Locale:
    """Returns a Locale object based of user's language."""

    if lang == 'kk' and lang not in get_available_languages():  # todo: Kazakh localization pls
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
