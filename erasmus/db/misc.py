from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, Snowflake


class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[Snowflake] = mapped_column(primary_key=True, init=True)
    application_commands: Mapped[bool] = mapped_column()
