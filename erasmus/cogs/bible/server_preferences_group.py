from __future__ import annotations

from typing import TYPE_CHECKING

from discord import app_commands

from .daily_bread import DailyBreadPreferencesGroup
from .version_preferences_group import VersionPreferencesGroup

if TYPE_CHECKING:

    from ...erasmus import Erasmus
    from ...l10n import GroupLocalizer
    from .types import ParentCog


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
class ServerPreferencesGroup(
    app_commands.Group, name='serverprefs', description='Server preferences'
):
    bot: Erasmus
    localizer: GroupLocalizer

    version = VersionPreferencesGroup()
    daily_bread = DailyBreadPreferencesGroup()

    def initialize_from_parent(self, parent: ParentCog, /) -> None:
        self.bot = parent.bot
        self.localizer = parent.localizer.for_group(self)

        self.version.initialize_from_parent(self)
        self.daily_bread.initialize_from_parent(self)
