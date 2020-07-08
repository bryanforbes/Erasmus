from pathlib import Path

import pytest
import toml

from erasmus.data import Passage, VerseRange
from erasmus.services import BiblesOrg

from . import Galatians_3_10_11, Mark_5_1, ServiceTest


@pytest.mark.skip()
class TestBiblesOrg(ServiceTest):
    @pytest.fixture(
        params=[
            {
                'terms': ['Melchizedek'],
                'verses': [
                    Passage(
                        text='And **Melchizedek** king of Salem brought out bread and '
                        'wine; now he was a priest of God Most High.',
                        range=VerseRange.from_string('Genesis 14:18'),
                        version='NASB',
                    ),
                    Passage(
                        text='just as He says also in another passage, \u201cYOU ARE A '
                        'PRIEST FOREVER ACCORDING TOTHE ORDER OF **MELCHIZEDEK**.'
                        '\u201d',
                        range=VerseRange.from_string('Hebrews 5:6'),
                        version='NASB',
                    ),
                    Passage(
                        text='being designated by God as a high priest according to '
                        'the order of **Melchizedek**.',
                        range=VerseRange.from_string('Hebrews 5:10'),
                        version='NASB',
                    ),
                    Passage(
                        text='where Jesus has entered as a forerunner for us, having '
                        'become a high priest forever according to the order of '
                        '**Melchizedek**.',
                        range=VerseRange.from_string('Hebrews 6:20'),
                        version='NASB',
                    ),
                    Passage(
                        text='**Melchizedek\u2019s** Priesthood Like Christ\u2019s '
                        'For this **Melchizedek**, king of Salem, priest of the Most '
                        'High God, who met Abraham as he was returning from the '
                        'slaughter of the kings and blessed him,',
                        range=VerseRange.from_string('Hebrews 7:1'),
                        version='NASB',
                    ),
                    Passage(
                        text='for he was still in the loins of his father when '
                        '**Melchizedek** met him.',
                        range=VerseRange.from_string('Hebrews 7:10'),
                        version='NASB',
                    ),
                    Passage(
                        text='Now if perfection was through the Levitical priesthood '
                        '(for on the basis of it the people received the Law), what '
                        'further need was there for another priest to arise according '
                        'to the order of **Melchizedek**, and not be designated '
                        'according to the order of Aaron?',
                        range=VerseRange.from_string('Hebrews 7:11'),
                        version='NASB',
                    ),
                    Passage(
                        text='And this is clearer still, if another priest arises '
                        'according to the likeness of **Melchizedek**,',
                        range=VerseRange.from_string('Hebrews 7:15'),
                        version='NASB',
                    ),
                    Passage(
                        text='For it is attested of Him, \u201cYOU ARE A PRIEST '
                        'FOREVER ACCORDING TO THE ORDER OF **MELCHIZEDEK**.\u201d',
                        range=VerseRange.from_string('Hebrews 7:17'),
                        version='NASB',
                    ),
                    Passage(
                        text='The LORD has sworn and will not change His mind, '
                        '\u201cYou are a priest forever According to the order of '
                        '**Melchizedek**.\u201d',
                        range=VerseRange.from_string('Psalm 110:4'),
                        version='NASB',
                    ),
                ],
                'total': 10,
            },
            {
                'terms': ['faith'],
                'verses': [
                    Passage(
                        text='\u201cKnow therefore that the LORD your God, He is God, '
                        'the **faithful** God, who keeps His covenant and His '
                        'lovingkindness to a thousandth generation with those who love '
                        'Him and keep His commandments;',
                        range=VerseRange.from_string('Deuteronomy 7:9'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cThe Rock! His work is perfect, For all His ways '
                        'are just; A God of **faithfulness** and without injustice, '
                        'Righteous and upright is He.',
                        range=VerseRange.from_string('Deuteronomy 32:4'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cThen He said, \u2018I will hide My face from them, '
                        'I will see what their end shall be; For they are a perverse '
                        'generation, Sons in whom is no **faithfulness**.',
                        range=VerseRange.from_string('Deuteronomy 32:20'),
                        version='NASB',
                    ),
                    Passage(
                        text='because you broke **faith** with Me in the midst of the '
                        'sons of Israel at the waters of Meribah-kadesh, in the '
                        'wilderness of Zin, because you did not treat Me as holy in '
                        'the midst of the sons of Israel.',
                        range=VerseRange.from_string('Deuteronomy 32:51'),
                        version='NASB',
                    ),
                    Passage(
                        text='I am unworthy of all the lovingkindness and of all the '
                        '**faithfulness** which You have shown to Your servant; for '
                        'with my staff only I crossed this Jordan, and now I have '
                        'become two companies.',
                        range=VerseRange.from_string('Genesis 32:10'),
                        version='NASB',
                    ),
                    Passage(
                        text='When the time for Israel to die drew near, he called his '
                        'son Joseph and said to him, \u201cPlease, if I have found '
                        'favor in your sight, place now your hand under my thigh and '
                        'deal with me in kindness and **faithfulness**. Please do not '
                        'bury me in Egypt,',
                        range=VerseRange.from_string('Genesis 47:29'),
                        version='NASB',
                    ),
                    Passage(
                        text='So the men said to her, \u201cOur life for yours if you '
                        'do not tell this business of ours; and it shall come about '
                        'when the LORD gives us the land that we will deal kindly and '
                        '**faithfully** with you.\u201d The Promise to Rahab',
                        range=VerseRange.from_string('Joshua 2:14'),
                        version='NASB',
                    ),
                    Passage(
                        text='Israel Is Defeated at Ai But the sons of Israel acted '
                        '**unfaithfully** in regard to the things under the ban, for '
                        'Achan, the son of Carmi, the son of Zabdi, the son of Zerah, '
                        'from the tribe of Judah, took some of the things under the '
                        'ban, therefore the anger of the LORD burned against the sons '
                        'of Israel.',
                        range=VerseRange.from_string('Joshua 7:1'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cThus says the whole congregation of the LORD, '
                        '\u2018What is this **unfaithful** act which you have '
                        'committed against the God of Israel, turning away from '
                        'following the LORD this day, by building yourselves an altar, '
                        'to rebel against the LORD this day?',
                        range=VerseRange.from_string('Joshua 22:16'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u2018Did not Achan the son of Zerah act '
                        '**unfaithfully** in the things under the ban, and wrath fall '
                        'on all the congregation of Israel? And that man did not '
                        'perish alone in his iniquity.\u2019\u201d',
                        range=VerseRange.from_string('Joshua 22:20'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cThe Mighty One, God, the LORD, the Mighty One, '
                        'God, the LORD! He knows, and may Israel itself know. If it '
                        'was in rebellion, or if in an **unfaithful** act against the '
                        'LORD do not save us this day!',
                        range=VerseRange.from_string('Joshua 22:22'),
                        version='NASB',
                    ),
                    Passage(
                        text='And Phinehas the son of Eleazar the priest said to the '
                        'sons of Reuben and to the sons of Gad and to the sons of '
                        'Manasseh, \u201cToday we know that the LORD is in our midst, '
                        'because you have not committed this **unfaithful** act '
                        'against the LORD; now you have delivered the sons of Israel '
                        'from the hand of the LORD.\u201d',
                        range=VerseRange.from_string('Joshua 22:31'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cIf a person acts **unfaithfully** and sins '
                        'unintentionally against the LORD\u2019S holy things, then he '
                        'shall bring his guilt offering to the LORD: a ram without '
                        'defect from the flock, according to your valuation in silver '
                        'by shekels, in terms of the shekel of the sanctuary, for a '
                        'guilt offering.',
                        range=VerseRange.from_string('Leviticus 5:15'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cWhen a person sins and acts **unfaithfully** '
                        'against the LORD, and deceives his companion in regard to a '
                        'deposit or a security entrusted to him, or through robbery, '
                        'or if he has extorted from his companion,',
                        range=VerseRange.from_string('Leviticus 6:2'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u2018If they confess their iniquity and the iniquity of '
                        'their forefathers, in their **unfaithfulness** which they '
                        'committed against Me, and also in their acting with hostility '
                        'against Me\u2014',
                        range=VerseRange.from_string('Leviticus 26:40'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cSpeak to the sons of Israel, \u2018When a man or '
                        'woman commits any of the sins of mankind, acting '
                        '**unfaithfully** against the LORD, and that person is guilty,',
                        range=VerseRange.from_string('Numbers 5:6'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cSpeak to the sons of Israel and say to them, '
                        '\u2018If any man\u2019s wife goes astray and is '
                        '**unfaithful** to him,',
                        range=VerseRange.from_string('Numbers 5:12'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u2018When he has made her drink the water, then it '
                        'shall come about, if she has defiled herself and has been '
                        '**unfaithful** to her husband, that the water which brings a '
                        'curse will go into her and cause bitterness, and her abdomen '
                        'will swell and her thigh will waste away, and the woman will '
                        'become a curse among her people.',
                        range=VerseRange.from_string('Numbers 5:27'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u201cNot so, with My servant Moses, He is **faithful** '
                        'in all My household;',
                        range=VerseRange.from_string('Numbers 12:7'),
                        version='NASB',
                    ),
                    Passage(
                        text='\u2018Your sons shall be shepherds for forty years in '
                        'the wilderness, and they will suffer for your '
                        '**unfaithfulness**, until your corpses lie in the wilderness.',
                        range=VerseRange.from_string('Numbers 14:33'),
                        version='NASB',
                    ),
                ],
                'total': 417,
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
        try:
            config = toml.load(
                str(Path(__file__).resolve().parent.parent.parent / 'config.toml')
            )
            return config['bot']['services']['BiblesOrg']
        except FileNotFoundError:
            return {'api_key': ''}

    @pytest.fixture
    def default_version(self):
        return 'eng-NASB'

    @pytest.fixture
    def default_abbr(self):
        return 'NASB'

    @pytest.fixture
    def service(self, config, session):
        return BiblesOrg(config=config, session=session)
