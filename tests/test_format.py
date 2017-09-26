import pytest
from erasmus.format import pluralizer


@pytest.mark.parametrize('args,count,expected', [
    (['ham'], 0, '0 hams'),
    (['ham'], 1, '1 ham'),
    (['ham'], 2, '2 hams'),
    (['fish', 'es'], 0, '0 fishes'),
    (['fish', 'es'], 1, '1 fish'),
    (['fish', 'es'], 2, '2 fishes'),
])
def test_pluralizer(args, count, expected):
    pluralize = pluralizer(*args)

    assert callable(pluralize) is True
    assert pluralize(count) == expected
