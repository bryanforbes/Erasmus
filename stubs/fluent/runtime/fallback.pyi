from _typeshed import SupportsItems, SupportsKeysAndGetItem
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Any

from ..syntax.ast import Resource
from . import FluentBundle
from .builtins import _FluentFunction

class FluentLocalization:
    locales: Sequence[str]
    resource_ids: Iterable[str]
    resource_loader: AbstractResourceLoader
    use_isolating: bool
    bundle_class: type[FluentBundle]
    functions: SupportsKeysAndGetItem[str, _FluentFunction]
    _bundle_cache: list[FluentBundle]
    _bundle_it: Iterator[FluentBundle]
    def __init__(
        self,
        locales: Sequence[str],
        resource_ids: Iterable[str],
        resource_loader: AbstractResourceLoader,
        use_isolating: bool = ...,
        bundle_class: type[FluentBundle] | None = ...,
        functions: SupportsKeysAndGetItem[str, _FluentFunction] | None = ...,
    ) -> None: ...
    def format_value(
        self, msg_id: str, args: SupportsItems[str, Any] | None = ...
    ) -> str: ...
    def _create_bundle(self, locales: Sequence[str]) -> FluentBundle: ...
    def _bundles(self) -> Iterator[FluentBundle]: ...
    def _iterate_bundles(self) -> Iterator[FluentBundle]: ...

class AbstractResourceLoader:
    def resources(
        self, locale: str, resource_ids: Iterable[str]
    ) -> Iterator[list[Resource]]: ...

class FluentResourceLoader(AbstractResourceLoader):
    roots: Iterable[str]
    Resource: Callable[[str], Resource]
    def __init__(self, roots: str | Iterable[str]) -> None: ...
    def resources(
        self, locale: str, resource_ids: Iterable[str]
    ) -> Iterator[list[Resource]]: ...
    def localize_path(self, path: str, locale: str) -> str: ...
