import pytest

import toml
from pathlib import Path
from . import ServiceTest, Galatians_3_10_11, Mark_5_1

from erasmus.services import BiblesOrg
from erasmus.data import VerseRange, Passage


class TestBiblesOrg(ServiceTest):
    @pytest.fixture(
        params=[
            {
                'terms': ['Melchizedek'],
                'verses': [
                    VerseRange.from_string('Genesis 14:18'),
                    VerseRange.from_string('Hebrews 5:6'),
                    VerseRange.from_string('Hebrews 5:10'),
                    VerseRange.from_string('Hebrews 6:20'),
                    VerseRange.from_string('Hebrews 7:1'),
                    VerseRange.from_string('Hebrews 7:10'),
                    VerseRange.from_string('Hebrews 7:11'),
                    VerseRange.from_string('Hebrews 7:15'),
                    VerseRange.from_string('Hebrews 7:17'),
                    VerseRange.from_string('Psalm 110:4'),
                ],
                'total': 10,
            },
            {'terms': ['antidisestablishmentarianism'], 'verses': [], 'total': 0},
        ],
        ids=['Melchizedek', 'antidisestablishmentarianism'],
    )
    def search_data(self, request):
        return request.param

    @pytest.fixture(
        params=[
            {
                'verse': VerseRange.from_string('Gal 3:10-11'),
                'passage': Passage(
                    Galatians_3_10_11, VerseRange.from_string('Gal 3:10-11'), 'NASB'
                ),
            },
            {
                'verse': VerseRange.from_string('Mark 5:1'),
                'passage': Passage(
                    Mark_5_1, VerseRange.from_string('Mark 5:1'), 'NASB'
                ),
            },
        ],
        ids=['Gal 3:10-11 NASB', 'Mark 5:1 NASB'],
    )
    def passage_data(self, request):
        return request.param

    @pytest.fixture(scope="class")
    def config(self):
        config = toml.load(
            str(Path(__file__).resolve().parent.parent.parent / 'config.toml')
        )
        return config['bot']['services']['BiblesOrg']

    @pytest.fixture
    def default_version(self):
        return 'eng-NASB'

    @pytest.fixture
    def default_abbr(self):
        return 'NASB'

    @pytest.fixture
    def service(self, config, session):
        return BiblesOrg(config, session)
