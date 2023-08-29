from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    LiteralString,
    Protocol,
    overload,
)
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from unittest import mock

_T = TypeVar('_T', infer_variance=True)


class _Patcher(Protocol):
    @overload
    def object(
        self,
        target: object,
        attribute: str,
        new: None = None,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: None = None,
        **kwargs: Any,
    ) -> mock.MagicMock | mock.AsyncMock:
        ...

    @overload
    def object(
        self,
        target: object,
        attribute: str,
        new: _T,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: None = None,
        **kwargs: Any,
    ) -> _T:
        ...

    @overload
    def object(
        self,
        target: object,
        attribute: str,
        *,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: Callable[..., _T],
        **kwargs: Any,
    ) -> _T:
        ...

    @overload
    def context_manager(
        self,
        target: object,
        attribute: str,
        new: None = None,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: None = None,
        **kwargs: Any,
    ) -> mock.MagicMock | mock.AsyncMock:
        ...

    @overload
    def context_manager(
        self,
        target: object,
        attribute: str,
        new: _T,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: None = None,
        **kwargs: Any,
    ) -> _T:
        ...

    @overload
    def context_manager(
        self,
        target: object,
        attribute: str,
        *,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: Callable[..., _T],
        **kwargs: Any,
    ) -> _T:
        ...

    @overload
    def multiple(
        self,
        target: object,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: None = None,
        **kwargs: Any,
    ) -> dict[str, mock.MagicMock | mock.AsyncMock]:
        ...

    @overload
    def multiple(
        self,
        target: object,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        *,
        new_callable: Callable[[], _T],
        **kwargs: Any,
    ) -> dict[str, _T]:
        ...

    def dict(
        self,
        in_dict: Mapping[Any, Any] | str,
        values: Mapping[Any, Any] | Iterable[tuple[Any, Any]] = (),
        clear: bool = False,
        *kwargs: Any,
    ) -> Any:
        ...

    @overload
    def __call__(
        self,
        target: str,
        new: None = None,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: None = None,
        **kwargs: Any,
    ) -> mock.MagicMock | mock.AsyncMock:
        ...

    @overload
    def __call__(
        self,
        target: str,
        new: _T,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        new_callable: None = None,
        **kwargs: Any,
    ) -> _T:
        ...

    @overload
    def __call__(
        self,
        target: str,
        new: None = ...,
        spec: object | None = None,
        create: bool = False,
        spec_set: object | None = None,
        autospec: object | None = None,
        *,
        new_callable: Callable[..., _T],
        **kwargs: Any,
    ) -> _T:
        ...


_SentinelNameT = TypeVar('_SentinelNameT', bound='LiteralString', infer_variance=True)


class _SentinelObject(Any, Generic[_SentinelNameT]):
    name: _SentinelNameT

    def __init__(self, name: _SentinelNameT) -> None:
        ...


class _Sentinel:
    def __getattr__(self, name: _SentinelNameT) -> _SentinelObject[_SentinelNameT]:
        ...


class MockerFixture(Protocol):
    patch: _Patcher
    Mock: type[mock.Mock]
    MagicMock: type[mock.MagicMock]
    NonCallableMock: type[mock.NonCallableMock]
    NonCallableMagicMock: type[mock.NonCallableMagicMock]
    PropertyMock: type[mock.PropertyMock]
    AsyncMock: type[mock.AsyncMock]
    call: mock._Call
    ANY: Any
    DEFAULT: _SentinelObject[Literal['DEFAULT']]
    sentinel: _Sentinel

    def create_autospec(
        self,
        spec: Any,
        spec_set: Any = ...,
        instance: Any = ...,
        _parent: Any | None = ...,
        _name: Any | None = ...,
        *,
        unsafe: bool = ...,
        **kwargs: Any,
    ) -> Any:
        ...

    def mock_open(self, mock: Any | None = ..., read_data: Any = ...) -> Any:
        ...

    def seal(self, mock: Any) -> None:
        ...

    def resetall(
        self, *, return_value: bool = False, side_effect: bool = False
    ) -> None:
        ...

    def stopall(self) -> None:
        ...

    def stop(self, mock: mock.MagicMock) -> None:
        ...

    def spy(self, obj: object, name: str) -> mock.MagicMock | mock.AsyncMock:
        ...

    def stub(self, name: str | None = None) -> mock.MagicMock:
        ...

    def async_stub(self, name: str | None = None) -> mock.AsyncMock:
        ...
