from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from botus_receptus.sqlalchemy import Snowflake
from sqlalchemy import Boolean, Column

from .base import mapped

if TYPE_CHECKING:
    from sqlalchemy.orm import Mapped


@mapped
@dataclass
class Notification:
    __tablename__ = 'notifications'
    __sa_dataclass_metadata_key__ = 'sa'

    id: Mapped[int] = field(metadata={'sa': Column(Snowflake, primary_key=True)})
    application_commands: Mapped[bool] = field(
        metadata={'sa': Column(Boolean, nullable=False)}
    )
