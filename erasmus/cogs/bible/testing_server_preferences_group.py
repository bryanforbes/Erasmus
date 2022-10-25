from __future__ import annotations

from typing import TYPE_CHECKING

from botus_receptus.app_commands import test_guilds_only
from discord import app_commands

from .daily_bread.daily_bread_preferences_group import DailyBreadPreferencesGroup

if TYPE_CHECKING:
    from ...erasmus import Erasmus
    from ...l10n import GroupLocalizer
    from .types import ParentCog


@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
@test_guilds_only
class TestingServerPreferencesGroup(
    app_commands.Group, name='test-server-prefs', description='Testing group'
):
    bot: Erasmus
    localizer: GroupLocalizer

    daily_bread = DailyBreadPreferencesGroup()

    def initialize_from_parent(self, parent: ParentCog, /) -> None:
        self.bot = parent.bot
        self.localizer = parent.localizer.for_group(self)

        self.daily_bread.initialize_from_parent(self)
