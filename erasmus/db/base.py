from __future__ import annotations

from typing import Final

from botus_receptus.sqlalchemy import sessionmaker
from sqlalchemy.orm import registry

mapper_registry: Final = registry()
Session: Final = sessionmaker(expire_on_commit=False)
