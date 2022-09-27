from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define
from discord import app_commands

from ...utils import AutoCompleter

if TYPE_CHECKING:
    from typing_extensions import Self

    from ...db.bible import BibleVersion


@define(frozen=True)
class _BibleOption:
    name: str
    name_lower: str
    command: str
    command_lower: str
    abbreviation: str
    abbreviation_lower: str

    @property
    def key(self) -> str:
        return self.command

    def matches(self, text: str, /) -> bool:
        return (
            self.command_lower.startswith(text)
            or text in self.name_lower
            or text in self.abbreviation_lower
        )

    def choice(self) -> app_commands.Choice[str]:
        return app_commands.Choice(name=self.name, value=self.command)

    @classmethod
    def create(cls, version: BibleVersion, /) -> Self:
        return cls(
            name=version.name,
            name_lower=version.name.lower(),
            command=version.command,
            command_lower=version.command.lower(),
            abbreviation=version.abbr,
            abbreviation_lower=version.abbr.lower(),
        )


bible_lookup: AutoCompleter[_BibleOption] = AutoCompleter()
