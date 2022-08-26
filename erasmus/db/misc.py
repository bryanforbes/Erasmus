from __future__ import annotations

from botus_receptus.sqlalchemy import Snowflake
from sqlalchemy import Boolean

from .base import Base, Mapped, mapped_column, model


@model
class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(Snowflake, primary_key=True, init=True)
    application_commands: Mapped[bool] = mapped_column(Boolean, nullable=False)
