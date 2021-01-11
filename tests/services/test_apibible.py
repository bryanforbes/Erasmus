from pathlib import Path

import pytest
import toml

from erasmus.data import Passage, VerseRange
from erasmus.services.apibible import ApiBible

from . import ServiceTest


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
                        text='As he saith also in another place , Thou art a priest '
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
                        text='And he said, I will hide my face from them, I will see '
                        'what their end shall be: for they are a very froward '
                        'generation, children in whom is no faith.',
                        range=VerseRange.from_string('Deuteronomy 32:20'),
                        version='KJV',
                    ),
                    Passage(
                        text='Behold, his soul which is lifted up is not upright in '
                        'him: but the just shall live by his faith.',
                        range=VerseRange.from_string('Habakkuk 2:4'),
                        version='KJV',
                    ),
                    Passage(
                        text='Wherefore, if God so clothe the grass of the field, '
                        'which to day is, and to morrow is cast into the oven, shall '
                        'he not much more clothe you, O ye of little faith?',
                        range=VerseRange.from_string('Matthew 6:30'),
                        version='KJV',
                    ),
                    Passage(
                        text='When Jesus heard it , he marvelled, and said to them '
                        'that followed, Verily I say unto you, I have not found so '
                        'great faith, no, not in Israel.',
                        range=VerseRange.from_string('Matthew 8:10'),
                        version='KJV',
                    ),
                    Passage(
                        text='And he saith unto them, Why are ye fearful, O ye of '
                        'little faith? Then he arose, and rebuked the winds and the '
                        'sea; and there was a great calm.',
                        range=VerseRange.from_string('Matthew 8:26'),
                        version='KJV',
                    ),
                    Passage(
                        text='And, behold, they brought to him a man sick of the '
                        'palsy, lying on a bed: and Jesus seeing their faith said unto '
                        'the sick of the palsy; Son, be of good cheer; thy sins be '
                        'forgiven thee.',
                        range=VerseRange.from_string('Matthew 9:2'),
                        version='KJV',
                    ),
                    Passage(
                        text='But Jesus turned him about, and when he saw her, he '
                        'said, Daughter, be of good comfort; thy faith hath made thee '
                        'whole. And the woman was made whole from that hour.',
                        range=VerseRange.from_string('Matthew 9:22'),
                        version='KJV',
                    ),
                    Passage(
                        text='Then touched he their eyes, saying, According to your '
                        'faith be it unto you.',
                        range=VerseRange.from_string('Matthew 9:29'),
                        version='KJV',
                    ),
                    Passage(
                        text='And immediately Jesus stretched forth his hand, and '
                        'caught him, and said unto him, O thou of little faith, '
                        'wherefore didst thou doubt?',
                        range=VerseRange.from_string('Matthew 14:31'),
                        version='KJV',
                    ),
                    Passage(
                        text='Then Jesus answered and said unto her, O woman, great is '
                        'thy faith: be it unto thee even as thou wilt. And her '
                        'daughter was made whole from that very hour.',
                        range=VerseRange.from_string('Matthew 15:28'),
                        version='KJV',
                    ),
                    Passage(
                        text='Which when Jesus perceived, he said unto them, O ye of '
                        'little faith, why reason ye among yourselves, because ye have '
                        'brought no bread?',
                        range=VerseRange.from_string('Matthew 16:8'),
                        version='KJV',
                    ),
                    Passage(
                        text='And Jesus said unto them, Because of your unbelief: for '
                        'verily I say unto you, If ye have faith as a grain of mustard '
                        'seed, ye shall say unto this mountain, Remove hence to yonder '
                        'place; and it shall remove; and nothing shall be impossible '
                        'unto you.',
                        range=VerseRange.from_string('Matthew 17:20'),
                        version='KJV',
                    ),
                    Passage(
                        text='Jesus answered and said unto them, Verily I say unto '
                        'you, If ye have faith, and doubt not, ye shall not only do '
                        'this which is done to the fig tree, but also if ye shall say '
                        'unto this mountain, Be thou removed, and be thou cast into '
                        'the sea; it shall be done.',
                        range=VerseRange.from_string('Matthew 21:21'),
                        version='KJV',
                    ),
                    Passage(
                        text='Woe unto you, scribes and Pharisees, hypocrites! for ye '
                        'pay tithe of mint and anise and cummin, and have omitted the '
                        'weightier matters of the law, judgment, mercy, and faith: '
                        'these ought ye to have done, and not to leave the other '
                        'undone.',
                        range=VerseRange.from_string('Matthew 23:23'),
                        version='KJV',
                    ),
                    Passage(
                        text='When Jesus saw their faith, he said unto the sick of the '
                        'palsy, Son, thy sins be forgiven thee.',
                        range=VerseRange.from_string('Mark 2:5'),
                        version='KJV',
                    ),
                    Passage(
                        text='And he said unto them, Why are ye so fearful? how is it '
                        'that ye have no faith?',
                        range=VerseRange.from_string('Mark 4:40'),
                        version='KJV',
                    ),
                    Passage(
                        text='And he said unto her, Daughter, thy faith hath made '
                        'thee whole; go in peace, and be whole of thy plague.',
                        range=VerseRange.from_string('Mark 5:34'),
                        version='KJV',
                    ),
                    Passage(
                        text='And Jesus said unto him, Go thy way; thy faith hath '
                        'made thee whole. And immediately he received his sight, and '
                        'followed Jesus in the way.',
                        range=VerseRange.from_string('Mark 10:52'),
                        version='KJV',
                    ),
                    Passage(
                        text='And Jesus answering saith unto them, Have faith in God.',
                        range=VerseRange.from_string('Mark 11:22'),
                        version='KJV',
                    ),
                    Passage(
                        text='And when he saw their faith, he said unto him, Man, thy '
                        'sins are forgiven thee.',
                        range=VerseRange.from_string('Luke 5:20'),
                        version='KJV',
                    ),
                ],
                'total': 231,
            },
            {'terms': ['antidisestablishmentarianism'], 'verses': [], 'total': 0},
        ],
        ids=['Melchizedek', 'faith', 'antidisestablishmentarianism'],
    )
    def search_data(self, request):
        return request.param

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
    def passage_data(self, request):
        return request.param

    @pytest.fixture(scope="class")
    def config(self):
        try:
            config = toml.load(
                str(Path(__file__).resolve().parent.parent.parent / 'config.toml')
            )
            return config['bot']['services']['ApiBible']
        except FileNotFoundError:
            return {'api_key': ''}

    @pytest.fixture
    def default_version(self):
        return 'de4e12af7f28f599-02'

    @pytest.fixture
    def default_abbr(self):
        return 'KJV'

    @pytest.fixture
    def service(self, config):
        return ApiBible(config=config)
