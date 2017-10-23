import pytest
from erasmus.format import pluralizer


@pytest.mark.parametrize('pluralizer_args,pluralize_args,pluralize_kwargs,expected', [
    (['ham'], [0], {}, '0 hams'),
    (['ham'], [1], {}, '1 ham'),
    (['ham'], [2], {}, '2 hams'),
    (['fish', 'es'], [0], {}, '0 fishes'),
    (['fish', 'es'], [1], {}, '1 fish'),
    (['fish', 'es'], [2], {}, '2 fishes'),
    (['fish', 'es'], [0], {'include_number': False}, 'fishes'),
    (['fish', 'es'], [1], {'include_number': False}, 'fish'),
    (['fish', 'es'], [2], {'include_number': False}, 'fishes'),
])
def test_pluralizer(pluralizer_args, pluralize_args, pluralize_kwargs, expected):
    pluralize = pluralizer(*pluralizer_args)

    assert callable(pluralize) is True
    assert pluralize(*pluralize_args, **pluralize_kwargs) == expected
