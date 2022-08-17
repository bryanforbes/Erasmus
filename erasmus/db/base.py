from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from botus_receptus.sqlalchemy import async_sessionmaker
from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import registry
from sqlalchemy.types import TypeEngine

_mapper_registry: Final = registry()

mapped: Final = _mapper_registry.mapped
Session: Final = async_sessionmaker(expire_on_commit=False)

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

    _TSVectorBase = TypeDecorator[str]
    _ComparatorBase = TypeEngine.Comparator['TSVector']
else:
    _TSVectorBase = TypeDecorator
    _ComparatorBase = TSVECTOR.Comparator


class TSVector(_TSVectorBase):
    impl = TSVECTOR
    cache_ok = True

    class Comparator(_ComparatorBase):  # type: ignore
        def match(self, other: Any, **kwargs: Any) -> Any:
            if 'postgresql_regconfig' not in kwargs:
                if 'regconfig' in self.type.options:
                    kwargs['postgresql_regconfig'] = self.type.options['regconfig']
            return TSVECTOR.Comparator.match(self, other, **kwargs)  # type: ignore

        def __or__(self, other: Any) -> ColumnElement[TSVector]:
            return self.op('||')(other)  # type: ignore

    comparator_factory = Comparator  # type: ignore

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initializes new TSVectorType

        :param *args: list of column names
        :param **kwargs: various other options for this TSVectorType
        """
        self.columns = args
        self.options = kwargs

        super().__init__()
