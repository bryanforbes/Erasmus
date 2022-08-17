from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import _pytest
import _pytest.fixtures
import aiohttp
import pytest

from erasmus.data import Passage, VerseRange
from erasmus.services.biblegateway import BibleGateway

from . import Galatians_3_10_11, Mark_5_1, ServiceTest

if TYPE_CHECKING:
    from erasmus.types import Service

Psalm_53_1_ESV = (
    '**To the choirmaster: according to Mahalath. A Maskil of David.** **1.** The fool '
    'says in his heart, “There is no God.” They are corrupt, doing abominable '
    'iniquity; there is none who does good.'
)


class TestBibleGateway(ServiceTest):
    @pytest.fixture(
        params=[
            {
                'terms': ['Melchizedek'],
                'verses': [
                    Passage(
                        text='And **Melchizedek** king of Salem brought out bread and '
                        'wine; now he was a priest of God Most High.',
                        range=VerseRange.from_string('Genesis 14:18'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='The LORD has sworn and will not change His mind, '
                        '\u201CYou are a priest forever According to the order of '
                        '**Melchizedek**.\u201D',
                        range=VerseRange.from_string('Psalm 110:4'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='just as He says also in another _passage_, \u201CYOU ARE '
                        'A PRIEST FOREVER ACCORDING TO THE ORDER OF **MELCHIZEDEK**.'
                        '\u201D',
                        range=VerseRange.from_string('Hebrews 5:6'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='being designated by God as a high priest according to '
                        'the order of **Melchizedek**.',
                        range=VerseRange.from_string('Hebrews 5:10'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='where Jesus has entered as a forerunner for us, having '
                        'become a high priest forever according to the order of '
                        '**Melchizedek**.',
                        range=VerseRange.from_string('Hebrews 6:20'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='_**Melchizedek**\u2019s Priesthood Like Christ\u2019s_'
                        ' For this **Melchizedek**, king of Salem, priest of the '
                        'Most High God, who met Abraham as he was returning from the '
                        'slaughter of the kings and blessed him,',
                        range=VerseRange.from_string('Hebrews 7:1'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='for he was still in the loins of his father when '
                        '**Melchizedek** met him.',
                        range=VerseRange.from_string('Hebrews 7:10'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='Now if perfection was through the Levitical priesthood '
                        '(for on the basis of it the people received the Law), what '
                        'further need _was there_ for another priest to arise '
                        'according to the order of **Melchizedek**, and not be '
                        'designated according to the order of Aaron?',
                        range=VerseRange.from_string('Hebrews 7:11'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='And this is clearer still, if another priest arises '
                        'according to the likeness of **Melchizedek**,',
                        range=VerseRange.from_string('Hebrews 7:15'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='For it is attested _of Him_, \u201CYOU ARE A PRIEST '
                        'FOREVER ACCORDING TO THE ORDER OF **MELCHIZEDEK**.\u201D',
                        range=VerseRange.from_string('Hebrews 7:17'),
                        version='NASB1995',
                    ),
                ],
                'total': 10,
            },
            {
                'terms': ['faith'],
                'verses': [
                    Passage(
                        text='I am unworthy of all the lovingkindness and of all '
                        'the **faith**fulness which You have shown to Your '
                        'servant; for with my staff _only_ I crossed this Jordan, '
                        'and now I have become two companies.',
                        range=VerseRange.from_string('Genesis 32:10'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='When the time for Israel to die drew near, he called his '
                        'son Joseph and said to him, \u201CPlease, if I have found '
                        'favor in your sight, place now your hand under my thigh and '
                        'deal with me in kindness and **faith**fulness. Please do not '
                        'bury me in Egypt,',
                        range=VerseRange.from_string('Genesis 47:29'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='\u201CNot so, with My servant Moses, He is **faith**'
                        'ful in all My household;',
                        range=VerseRange.from_string('Numbers 12:7'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='Know therefore that the LORD your God, He is God, the '
                        '**faith**ful God, who keeps His covenant and His '
                        'lovingkindness to a thousandth generation with those who love '
                        'Him and keep His commandments;',
                        range=VerseRange.from_string('Deuteronomy 7:9'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='\u201CThe Rock! His work is perfect, For all His ways '
                        'are just; A God of **faith**fulness and without injustice, '
                        'Righteous and upright is He.',
                        range=VerseRange.from_string('Deuteronomy 32:4'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='\u201CThen He said, \u2018I will hide My face from them, '
                        'I will see what their end _shall be_; For they are a perverse '
                        'generation, Sons in whom is no **faith**fulness.',
                        range=VerseRange.from_string('Deuteronomy 32:20'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='because you broke **faith** with Me in the midst of the '
                        'sons of Israel at the waters of Meribah-kadesh, in the '
                        'wilderness of Zin, because you did not treat Me as holy in '
                        'the midst of the sons of Israel.',
                        range=VerseRange.from_string('Deuteronomy 32:51'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='So the men said to her, \u201COur life for yours if you '
                        'do not tell this business of ours; and it shall come about '
                        'when the LORD gives us the land that we will deal kindly and '
                        '**faith**fully with you.\u201D',
                        range=VerseRange.from_string('Joshua 2:14'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='But I will raise up for Myself a **faith**ful priest who '
                        'will do according to what is in My heart and in My soul; and '
                        'I will build him an enduring house, and he will walk before '
                        'My anointed always.',
                        range=VerseRange.from_string('1 Samuel 2:35'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='Then Ahimelech answered the king and said, \u201CAnd who '
                        'among all your servants is as **faith**ful as David, even the '
                        'king\u2019s son-in-law, who is captain over your guard, and '
                        'is honored in your house?',
                        range=VerseRange.from_string('1 Samuel 22:14'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='The LORD will repay each man _for_ his righteousness and '
                        'his **faith**fulness; for the LORD delivered you into _my_ '
                        'hand today, but I refused to stretch out my hand against the '
                        'LORD\u2019S anointed.',
                        range=VerseRange.from_string('1 Samuel 26:23'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='I am of those who are peaceable _and_ **faith**ful in '
                        'Israel. You are seeking to destroy a city, even a mother in '
                        'Israel. Why would you swallow up the inheritance of the '
                        'LORD?\u201D',
                        range=VerseRange.from_string('2 Samuel 20:19'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='Moreover, they did not require an accounting from the '
                        'men into whose hand they gave the money to pay to those who '
                        'did the work, for they dealt **faith**fully.',
                        range=VerseRange.from_string('2 Kings 12:15'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='Only no accounting shall be made with them for the money '
                        'delivered into their hands, for they deal **faith**fully.'
                        '\u201D',
                        range=VerseRange.from_string('2 Kings 22:7'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='Then he charged them saying, \u201CThus you shall do in '
                        'the fear of the LORD, **faith**fully and wholeheartedly.',
                        range=VerseRange.from_string('2 Chronicles 19:9'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='_**Faith**less Priests_ Now it came about after this '
                        'that Joash decided to restore the house of the LORD.',
                        range=VerseRange.from_string('2 Chronicles 24:4'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='They **faith**fully brought in the contributions and the '
                        'tithes and the consecrated things; and Conaniah the Levite '
                        '_was_ the officer in charge of them and his brother Shimei '
                        '_was_ second.',
                        range=VerseRange.from_string('2 Chronicles 31:12'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='Under his authority _were_ Eden, Miniamin, Jeshua, '
                        'Shemaiah, Amariah and Shecaniah in the cities of the priests, '
                        'to distribute **faith**fully _their portions_ to their '
                        'brothers by divisions, whether great or small,',
                        range=VerseRange.from_string('2 Chronicles 31:15'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='The genealogical enrollment _included_ all their little '
                        'children, their wives, their sons and their daughters, for '
                        'the whole assembly, for they consecrated themselves '
                        '**faith**fully in holiness.',
                        range=VerseRange.from_string('2 Chronicles 31:18'),
                        version='NASB1995',
                    ),
                    Passage(
                        text='_Sennacherib Invades Judah_ After these acts of '
                        '**faith**fulness Sennacherib king of Assyria came and invaded '
                        'Judah and besieged the fortified cities, and thought to break '
                        'into them for himself.',
                        range=VerseRange.from_string('2 Chronicles 32:1'),
                        version='NASB1995',
                    ),
                ],
                'total': 378,
            },
            {'terms': ['antidisestablishmentarianism'], 'verses': [], 'total': 0},
        ],
        ids=['Melchizedek', 'faith', 'antidisestablishmentarianism'],
    )
    def search_data(self, request: _pytest.fixtures.SubRequest) -> dict[str, Any]:
        return cast('dict[str, Any]', request.param)

    @pytest.fixture(
        params=[
            {
                'verse': VerseRange.from_string('Gal 3:10-11'),
                'passage': Passage(
                    Galatians_3_10_11, VerseRange.from_string('Gal 3:10-11'), 'NASB1995'
                ),
            },
            {
                'verse': VerseRange.from_string('Mark 5:1'),
                'passage': Passage(
                    Mark_5_1, VerseRange.from_string('Mark 5:1'), 'NASB1995'
                ),
            },
            {
                'verse': VerseRange.from_string('Psalm 53:1'),
                'passage': Passage(
                    Psalm_53_1_ESV, VerseRange.from_string('Psalm 53:1'), 'ESV'
                ),
                'version': 'ESV',
                'abbr': 'ESV',
            },
        ],
        ids=['Gal 3:10-11 NASB1995', 'Mark 5:1 NASB1995', 'Psalm 53:1 ESV'],
    )
    def passage_data(self, request: _pytest.fixtures.SubRequest) -> dict[str, Any]:
        return cast('dict[str, Any]', request.param)

    @pytest.fixture
    def default_version(self) -> str:
        return 'NASB1995'

    @pytest.fixture
    def default_abbr(self) -> str:
        return 'NASB1995'

    @pytest.fixture
    def service(self, aiohttp_client_session: aiohttp.ClientSession) -> Service:
        return BibleGateway(config={}, session=aiohttp_client_session)
