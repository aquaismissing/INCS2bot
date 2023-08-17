from l10n import L10n


def test_l10n(recwarn):
    """
    Test to check any missing or unexpected locale keys.
    """

    L10n('data')

    for r in recwarn:
        print(f'{r.category.__name__}: {r.message}')
    assert len(recwarn) == 0, 'L10n process raised some warnings.'
