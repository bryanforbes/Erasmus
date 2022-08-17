from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import _pytest
import _pytest.fixtures
import aiohttp
import pytest
import toml

from erasmus.data import Passage, VerseRange
from erasmus.services.apibible import ApiBible

from . import ServiceTest

if TYPE_CHECKING:
    from erasmus.types import Service


class TestApiBible(ServiceTest):
    @pytest.fixture(
        params=[
            {
                'terms': ['Melchizedek'],
                'verses': [
                    Passage(
                        text='And Melchizedek king of Salem brought forth bread and '
                        'wine: and he was the priest of the most high God.',
                        range=VerseRange.from_string('Genesis 14:18'),
                        version='KJV',
                    ),
                    Passage(
                        text='The LORD hath sworn, and will not repent, Thou art a '
                        'priest for ever after the order of Melchizedek.',
                        range=VerseRange.from_string('Psalm 110:4'),
                        version='KJV',
                    ),
                    Passage(
                        text='As he saith also in another place, Thou art a priest '
                        'for ever after the order of Melchisedec.',
                        range=VerseRange.from_string('Hebrews 5:6'),
                        version='KJV',
                    ),
                    Passage(
                        text='Called of God an high priest after the order of '
                        'Melchisedec.',
                        range=VerseRange.from_string('Hebrews 5:10'),
                        version='KJV',
                    ),
                    Passage(
                        text='Whither the forerunner is for us entered, even Jesus, '
                        'made an high priest for ever after the order of Melchisedec.',
                        range=VerseRange.from_string('Hebrews 6:20'),
                        version='KJV',
                    ),
                    Passage(
                        text='For this Melchisedec, king of Salem, priest of the most '
                        'high God, who met Abraham returning from the slaughter of the '
                        'kings, and blessed him;',
                        range=VerseRange.from_string('Hebrews 7:1'),
                        version='KJV',
                    ),
                    Passage(
                        text='For he was yet in the loins of his father, when '
                        'Melchisedec met him.',
                        range=VerseRange.from_string('Hebrews 7:10'),
                        version='KJV',
                    ),
                    Passage(
                        text='If therefore perfection were by the Levitical '
                        'priesthood, (for under it the people received the law,) what '
                        'further need was there that another priest should rise after '
                        'the order of Melchisedec, and not be called after the order '
                        'of Aaron?',
                        range=VerseRange.from_string('Hebrews 7:11'),
                        version='KJV',
                    ),
                    Passage(
                        text='And it is yet far more evident: for that after the '
                        'similitude of Melchisedec there ariseth another priest,',
                        range=VerseRange.from_string('Hebrews 7:15'),
                        version='KJV',
                    ),
                    Passage(
                        text='For he testifieth, Thou art a priest for ever after the '
                        'order of Melchisedec.',
                        range=VerseRange.from_string('Hebrews 7:17'),
                        version='KJV',
                    ),
                    Passage(
                        text='(For those priests were made without an oath; but this '
                        'with an oath by him that said unto him, The Lord sware and '
                        'will not repent, Thou art a priest for ever after the order '
                        'of Melchisedec:)',
                        range=VerseRange.from_string('Hebrews 7:21'),
                        version='KJV',
                    ),
                ],
                'total': 11,
            },
            {
                'terms': ['faith'],
                'verses': [
                    Passage(
                        text='My servant Moses is not so, who is faithful in all mine '
                        'house.',
                        range=VerseRange.from_string('Numbers 12:7'),
                        version='KJV',
                    ),
                    Passage(
                        text='Know therefore that the LORD thy God, he is God, the '
                        'faithful God, which keepeth covenant and mercy with them that '
                        'love him and keep his commandments to a thousand generations;',
                        range=VerseRange.from_string('Deuteronomy 7:9'),
                        version='KJV',
                    ),
                    Passage(
                        text='And he said, I will hide my face from them, I will see '
                        'what their end shall be: for they are a very froward '
                        'generation, children in whom is no faith.',
                        range=VerseRange.from_string('Deuteronomy 32:20'),
                        version='KJV',
                    ),
                    Passage(
                        text='And I will raise me up a faithful priest, that shall do '
                        'according to that which is in mine heart and in my mind: '
                        'and I will build him a sure house; and he shall walk before '
                        'mine anointed for ever.',
                        range=VerseRange.from_string('1 Samuel 2:35'),
                        version='KJV',
                    ),
                    Passage(
                        text='Then Ahimelech answered the king, and said, And who is '
                        'so faithful among all thy servants as David, which is the '
                        'king\u2019s son in law, and goeth at thy bidding, and is '
                        'honourable in thine house?',
                        range=VerseRange.from_string('1 Samuel 22:14'),
                        version='KJV',
                    ),
                    Passage(
                        text='The LORD render to every man his righteousness and his '
                        'faithfulness: for the LORD delivered thee into my hand to '
                        'day, but I would not stretch forth mine hand against the '
                        'LORD\u2019s anointed.',
                        range=VerseRange.from_string('1 Samuel 26:23'),
                        version='KJV',
                    ),
                    Passage(
                        text='I am one of them that are peaceable and faithful in '
                        'Israel: thou seekest to destroy a city and a mother in '
                        'Israel: why wilt thou swallow up the inheritance of the '
                        'LORD ?',
                        range=VerseRange.from_string('2 Samuel 20:19'),
                        version='KJV',
                    ),
                    Passage(
                        text='That I gave my brother Hanani, and Hananiah the ruler '
                        'of the palace, charge over Jerusalem: for he was a faithful '
                        'man, and feared God above many.',
                        range=VerseRange.from_string('Nehemiah 7:2'),
                        version='KJV',
                    ),
                    Passage(
                        text='And foundest his heart faithful before thee, and madest '
                        'a covenant with him to give the land of the Canaanites, the '
                        'Hittites, the Amorites, and the Perizzites, and the '
                        'Jebusites, and the Girgashites, to give it, I say, to his '
                        'seed, and hast performed thy words; for thou art righteous:',
                        range=VerseRange.from_string('Nehemiah 9:8'),
                        version='KJV',
                    ),
                    Passage(
                        text='And I made treasurers over the treasuries, Shelemiah '
                        'the priest, and Zadok the scribe, and of the Levites, '
                        'Pedaiah: and next to them was Hanan the son of Zaccur, the '
                        'son of Mattaniah: for they were counted faithful, and their '
                        'office was to distribute unto their brethren.',
                        range=VerseRange.from_string('Nehemiah 13:13'),
                        version='KJV',
                    ),
                    Passage(
                        text='For there is no faithfulness in their mouth; their '
                        'inward part is very wickedness; their throat is an open '
                        'sepulchre; they flatter with their tongue.',
                        range=VerseRange.from_string('Psalm 5:9'),
                        version='KJV',
                    ),
                    Passage(
                        text='Help, LORD; for the godly man ceaseth; for the faithful '
                        'fail from among the children of men.',
                        range=VerseRange.from_string('Psalm 12:1'),
                        version='KJV',
                    ),
                    Passage(
                        text='O love the LORD, all ye his saints: for the LORD '
                        'preserveth the faithful, and plentifully rewardeth the proud '
                        'doer.',
                        range=VerseRange.from_string('Psalm 31:23'),
                        version='KJV',
                    ),
                    Passage(
                        text='Thy mercy, O LORD, is in the heavens; and thy '
                        'faithfulness reacheth unto the clouds.',
                        range=VerseRange.from_string('Psalm 36:5'),
                        version='KJV',
                    ),
                    Passage(
                        text='I have not hid thy righteousness within my heart; I '
                        'have declared thy faithfulness and thy salvation: I have not '
                        'concealed thy lovingkindness and thy truth from the great '
                        'congregation.',
                        range=VerseRange.from_string('Psalm 40:10'),
                        version='KJV',
                    ),
                    Passage(
                        text='Shall thy lovingkindness be declared in the grave? or '
                        'thy faithfulness in destruction?',
                        range=VerseRange.from_string('Psalm 88:11'),
                        version='KJV',
                    ),
                    Passage(
                        text='I will sing of the mercies of the LORD for ever: with '
                        'my mouth will I make known thy faithfulness to all '
                        'generations.',
                        range=VerseRange.from_string('Psalm 89:1'),
                        version='KJV',
                    ),
                    Passage(
                        text='For I have said, Mercy shall be built up for ever: thy '
                        'faithfulness shalt thou establish in the very heavens.',
                        range=VerseRange.from_string('Psalm 89:2'),
                        version='KJV',
                    ),
                    Passage(
                        text='And the heavens shall praise thy wonders, O LORD: thy '
                        'faithfulness also in the congregation of the saints.',
                        range=VerseRange.from_string('Psalm 89:5'),
                        version='KJV',
                    ),
                    Passage(
                        text='O LORD God of hosts, who is a strong LORD like unto '
                        'thee? or to thy faithfulness round about thee?',
                        range=VerseRange.from_string('Psalm 89:8'),
                        version='KJV',
                    ),
                ],
                'total': 328,
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
                    '**10.** For as many as are of the works of the law are under the '
                    'curse: for it is written, Cursed _is_ every one that continueth '
                    'not in all things which are written in the book of the law to do '
                    'them. **11.** But that no man is justified by the law in the '
                    'sight of God, _it is_ evident: for, The just shall live by faith.',
                    VerseRange.from_string('Gal 3:10-11'),
                    'KJV',
                ),
            },
            {
                'verse': VerseRange.from_string('Mark 5:1'),
                'passage': Passage(
                    '**1.** And they came over unto the other side of the sea, into '
                    'the country of the Gadarenes.',
                    VerseRange.from_string('Mark 5:1'),
                    'KJV',
                ),
            },
        ],
        ids=['Gal 3:10-11 KJV', 'Mark 5:1 KJV'],
    )
    def passage_data(self, request: _pytest.fixtures.SubRequest) -> dict[str, Any]:
        return cast('dict[str, Any]', request.param)

    @pytest.fixture(scope="class")
    def config(self) -> dict[str, str]:
        try:
            config = toml.load(
                str(Path(__file__).resolve().parent.parent.parent / 'config.toml')
            )
            return cast('dict[str, str]', config['bot']['services']['ApiBible'])
        except FileNotFoundError:
            return {'api_key': ''}

    @pytest.fixture
    def default_version(self) -> str:
        return 'de4e12af7f28f599-02'

    @pytest.fixture
    def default_abbr(self) -> str:
        return 'KJV'

    @pytest.fixture
    def service(
        self, config: Any, aiohttp_client_session: aiohttp.ClientSession
    ) -> Service:
        return ApiBible(config=config, session=aiohttp_client_session)
