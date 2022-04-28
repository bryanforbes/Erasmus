from __future__ import annotations

from typing import Final

from botus_receptus.sqlalchemy import async_sessionmaker
from sqlalchemy.orm import registry

_mapper_registry: Final = registry()

mapped: Final = _mapper_registry.mapped
Session: Final = async_sessionmaker(expire_on_commit=False)
