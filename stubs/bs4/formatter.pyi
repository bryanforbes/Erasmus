from typing import Any, ClassVar, Literal, Protocol, type_check_only

from .dammit import EntitySubstitution as EntitySubstitution
from .element import Tag

# TODO: remove this comment when a new version of black comes out
@type_check_only
class _EntitySubstitutionCallback(Protocol):
    def __call__(self, __value: str) -> str: ...

class Formatter(EntitySubstitution):
    XML_FORMATTERS: ClassVar[dict[str, Formatter]]
    HTML_FORMATTERS: ClassVar[dict[str, Formatter]]
    HTML: ClassVar[Literal['html']]
    XML: ClassVar[Literal['xml']]
    HTML_DEFAULTS: dict[str, set[str]]
    language: Literal['html', 'xml'] | None
    entity_substitution: _EntitySubstitutionCallback | None
    void_element_close_prefix: Any = ...
    cdata_containing_tags: Any = ...
    def __init__(
        self,
        language: Literal['html', 'xml'] | None = ...,
        entity_substitution: _EntitySubstitutionCallback | None = ...,
        void_element_close_prefix: str = ...,
        cdata_containing_tags: list[str] | None = ...,
    ) -> None: ...
    def substitute(self, ns: str) -> str: ...
    def attribute_value(self, value: str) -> str: ...
    def attributes(self, tag: Tag) -> list[tuple[str, str]]: ...

class HTMLFormatter(Formatter):
    REGISTRY: ClassVar[dict[str, HTMLFormatter]]
    def __init__(
        self,
        entity_substitution: _EntitySubstitutionCallback | None = ...,
        void_element_close_prefix: str = ...,
        cdata_containing_tags: list[str] | None = ...,
    ) -> None: ...

class XMLFormatter(Formatter):
    REGISTRY: ClassVar[dict[str, XMLFormatter]]
    def __init__(
        self,
        entity_substitution: _EntitySubstitutionCallback | None = ...,
        void_element_close_prefix: str = ...,
        cdata_containing_tags: list[str] | None = ...,
    ) -> None: ...
