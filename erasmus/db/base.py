from __future__ import annotations

from typing import Annotated, Any, ClassVar, Final

import pendulum
from botus_receptus.sqlalchemy import (
    Flag,
    Snowflake as _Snowflake,
    TSVector as _TSVector,
)
from sqlalchemy import Text as _Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, mapped_column

from ..data import SectionFlag
from .enums import ConfessionType, NumberingType
from .types import DateTime, Time, Timezone

Session: Final = async_sessionmaker(expire_on_commit=False)


Snowflake = Annotated[int, mapped_column(_Snowflake)]
Text = Annotated[str, mapped_column(_Text)]
TSVector = Annotated[str, mapped_column(_TSVector)]


class Base(MappedAsDataclass, DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        pendulum.DateTime: DateTime(timezone=True),
        pendulum.Time: Time,
        pendulum.Timezone: Timezone,
        SectionFlag: Flag(SectionFlag),
        ConfessionType: ENUM(ConfessionType, name='confession_type'),
        NumberingType: ENUM(NumberingType, name='confession_numbering_type'),
    }
