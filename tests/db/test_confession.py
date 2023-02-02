from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy.dialects import postgresql

from erasmus.db.confession import Confession
from erasmus.db.enums import ConfessionType, NumberingType
from erasmus.exceptions import NoSectionError

if TYPE_CHECKING:
    from unittest.mock import NonCallableMagicMock, NonCallableMock

    from pytest_mock import MockerFixture


class TestConfession:
    @pytest.fixture
    def confession(self) -> Confession:
        confession = Confession(
            command='asdf',
            name='A Confession',
            type=ConfessionType.SECTIONS,
            numbering=NumberingType.ARABIC,
            _subsection_numbering=None,
        )
        confession.id = 42
        return confession

    @pytest.fixture
    def mock_scalar_result(self, mocker: MockerFixture) -> NonCallableMagicMock:
        scalar_result = mocker.NonCallableMagicMock()
        scalar_result.first.return_value = (  # pyright: ignore
            mocker.sentinel.first_scalar_result
        )
        scalar_result.__iter__.side_effect = lambda: iter(  # pyright: ignore
            [mocker.sentinel.scalar_result_one, mocker.sentinel.scalar_result_two]
        )
        return scalar_result

    @pytest.fixture
    def mock_session(
        self, mocker: MockerFixture, mock_scalar_result: NonCallableMagicMock
    ) -> NonCallableMock:
        scalars = mocker.AsyncMock(return_value=mock_scalar_result)
        session = mocker.NonCallableMock()
        session.attach_mock(scalars, 'scalars')
        return session

    def test_subsection_numbering(self, confession: Confession) -> None:
        assert confession.subsection_numbering == NumberingType.ARABIC
        confession._subsection_numbering = NumberingType.ROMAN
        assert confession.subsection_numbering == NumberingType.ROMAN

    async def test_search(
        self,
        mocker: MockerFixture,
        confession: Confession,
        mock_session: NonCallableMock,
    ) -> None:
        results = await confession.search(mock_session, 'light of nature')
        assert results == [
            mocker.sentinel.scalar_result_one,
            mocker.sentinel.scalar_result_two,
        ]
        assert str(
            mock_session.scalars.call_args.args[0].compile(  # pyright: ignore
                dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}
            )
        ) == (
            "SELECT anon_1.id, anon_1.confession_id, anon_1.number, "
            "anon_1.subsection_number, anon_1.title, anon_1.text, "
            "anon_1.text_stripped, anon_1.search_vector \n"
            "FROM (SELECT anon_2.id AS id, anon_2.confession_id AS confession_id, "
            "anon_2.number AS number, anon_2.subsection_number AS "
            "subsection_number, anon_2.text AS text, "
            "ts_headline('english', anon_2.title, plainto_tsquery('english', "
            "'light of nature'), 'HighlightAll=true, StartSel=*, StopSel=*') "
            "AS title, ts_headline('english', anon_2.text_stripped, "
            "plainto_tsquery('english', 'light of nature'), 'StartSel=**, "
            "StopSel=**') AS text_stripped, anon_2.search_vector AS "
            "search_vector \n"
            "FROM (SELECT confession_sections.id AS id, "
            "confession_sections.confession_id AS confession_id, "
            "confession_sections.number AS number, "
            "confession_sections.subsection_number AS subsection_number, "
            "confession_sections.title AS title, "
            "confession_sections.text AS text, confession_sections.text_stripped "
            "AS text_stripped, confession_sections.search_vector AS "
            "search_vector \n"
            "FROM confession_sections \n"
            "WHERE confession_sections.confession_id = 42 AND "
            "(confession_sections.search_vector @@ plainto_tsquery('english', "
            "'light of nature')) ORDER BY confession_sections.number ASC, "
            "confession_sections.subsection_number ASC NULLS FIRST) AS anon_2) AS "
            "anon_1"
        )

    @pytest.mark.parametrize(
        'number,subsection_number,expected',
        [
            (
                2,
                None,
                "SELECT confession_sections.id, confession_sections.confession_id, "
                "confession_sections.number, confession_sections.subsection_number, "
                "confession_sections.title, confession_sections.text, "
                "confession_sections.text_stripped, "
                "confession_sections.search_vector \n"
                "FROM confession_sections \n"
                "WHERE confession_sections.confession_id = 42 AND "
                "confession_sections.number = 2 \n"
                " LIMIT 1",
            ),
            (
                4,
                10,
                "SELECT confession_sections.id, confession_sections.confession_id, "
                "confession_sections.number, confession_sections.subsection_number, "
                "confession_sections.title, confession_sections.text, "
                "confession_sections.text_stripped, "
                "confession_sections.search_vector \n"
                "FROM confession_sections \n"
                "WHERE confession_sections.confession_id = 42 AND "
                "confession_sections.number = 4 AND "
                "confession_sections.subsection_number = 10 \n"
                " LIMIT 1",
            ),
        ],
        ids=['number only', 'with subsection number'],
    )
    async def test_get_section(
        self,
        mocker: MockerFixture,
        confession: Confession,
        mock_session: NonCallableMock,
        number: int,
        subsection_number: int | None,
        expected: str,
    ) -> None:
        assert (
            await confession.get_section(mock_session, number, subsection_number)
        ) == mocker.sentinel.first_scalar_result
        assert (
            str(
                mock_session.scalars.call_args.args[0].compile(  # pyright: ignore
                    dialect=postgresql.dialect(), compile_kwargs={'literal_binds': True}
                )
            )
            == expected
        )

    @pytest.mark.parametrize(
        'number,subsection_number,confession_type,expected_section,expected_type',
        [
            (2, None, ConfessionType.ARTICLES, '2', 'ARTICLES'),
            (10, 4, ConfessionType.QA, '10.4', 'QA'),
        ],
    )
    async def test_get_section_no_result_raises(
        self,
        confession: Confession,
        mock_scalar_result: NonCallableMagicMock,
        mock_session: NonCallableMock,
        number: int,
        subsection_number: int | None,
        confession_type: ConfessionType,
        expected_section: str,
        expected_type: str,
    ) -> None:
        confession.type = confession_type
        mock_scalar_result.first.return_value = None  # pyright: ignore

        with pytest.raises(NoSectionError) as exc_info:
            await confession.get_section(mock_session, number, subsection_number)

        assert exc_info.value.confession == 'A Confession'
        assert exc_info.value.section == expected_section
        assert exc_info.value.section_type == expected_type
