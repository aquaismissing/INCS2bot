import json

from sl10n.pimpl import JSONImpl

from l10n import SL10n, Locale


def test_l10n(recwarn):
    """
    Test to check any missing or unexpected locale keys.
    """

    SL10n(Locale, 'data', ignore_filenames=['tags'],
          parsing_impl=JSONImpl(json, indent=4, ensure_ascii=False)).init()

    for r in recwarn:
        print(f'{r.category.__name__}: {r.message}')
    assert len(recwarn) == 0, 'SL10n process raised some warnings.'
