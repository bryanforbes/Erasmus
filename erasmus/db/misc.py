from __future__ import annotations

from botus_receptus.sqlalchemy import Snowflake
from sqlalchemy import Boolean

from .base import Base, Column, Mapped, model


@model
class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[int] = Column(Snowflake, primary_key=True, init=True)
    application_commands: Mapped[bool] = Column(Boolean, nullable=False)
