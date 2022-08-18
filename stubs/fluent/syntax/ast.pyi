from collections.abc import Callable
from typing import Any
from typing_extensions import Self

def to_json(value: Any, fn: Callable[[Any], Any] = ...) -> Any: ...
def from_json(value: Any) -> Any: ...
def scalars_equal(node1: Any, node2: Any, ignored_fields: list[str]) -> bool: ...

class BaseNode:
    def clone(self) -> Self: ...
    def equals(self, other: BaseNode, ignored_fields: list[str] = ...) -> bool: ...
    def to_json(self, fn: Callable[[Any], Any] = ...) -> Any: ...

class SyntaxNode(BaseNode):
    span: Span | None
    def __init__(self, span: Span | None = ..., **kwargs: Any) -> None: ...
    def add_span(self, start: int, end: int) -> None: ...

class Resource(SyntaxNode):
    body: list[Any]
    def __init__(self, body: list[Any] = ..., **kwargs: Any) -> None: ...

class Entry(SyntaxNode): ...

class Message(Entry):
    id: Identifier
    value: Pattern | None
    attributes: list[Attribute]
    comment: Comment | GroupComment | ResourceComment | None
    def __init__(
        self,
        id: Identifier,
        value: Pattern | None = ...,
        attributes: list[Attribute] | None = ...,
        comment: Comment | GroupComment | ResourceComment | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...

class Term(Entry):
    id: Identifier
    value: Pattern
    attributes: list[Attribute]
    comment: Comment | GroupComment | ResourceComment | None
    def __init__(
        self,
        id: Identifier,
        value: Pattern,
        attributes: list[Attribute] | None = ...,
        comment: Comment | GroupComment | ResourceComment | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...

class Pattern(SyntaxNode):
    elements: list[Any]
    def __init__(
        self,
        elements: list[Any],
        *,
        span: Span | None = ...,
    ) -> None: ...

class PatternElement(SyntaxNode): ...

class TextElement(PatternElement):
    value: str
    def __init__(
        self,
        value: str,
        *,
        span: Span | None = ...,
    ) -> None: ...

class Placeable(PatternElement):
    expression: Expression
    def __init__(self, expression: Expression, *, span: Span | None = ...) -> None: ...

class Expression(SyntaxNode): ...

class Literal(Expression):
    value: str
    def __init__(self, value: str, *, span: Span | None = ...) -> None: ...
    def parse(self) -> dict[str, Any]: ...

class StringLiteral(Literal):
    def parse(self) -> dict[str, Any]: ...

class NumberLiteral(Literal):
    def parse(self) -> dict[str, Any]: ...

class MessageReference(Expression):
    id: Identifier
    attribute: Identifier | None
    def __init__(
        self,
        id: Identifier,
        attribute: Identifier | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...

class TermReference(Expression):
    id: Identifier
    attribute: Identifier | None
    def __init__(
        self,
        id: Identifier,
        attribute: Identifier | None = ...,
        arguments: CallArguments | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...

class VariableReference(Expression):
    id: Identifier
    def __init__(
        self,
        id: Identifier,
        *,
        span: Span | None = ...,
    ) -> None: ...

class FunctionReference(Expression):
    def __init__(
        self, id: Identifier, arguments: CallArguments, *, span: Span | None = ...
    ) -> None: ...

class SelectExpression(Expression):
    selector: Expression
    variants: list[Identifier | NumberLiteral]
    def __init__(
        self,
        selector: Expression,
        variants: list[Identifier | NumberLiteral],
        *,
        span: Span | None = ...,
    ) -> None: ...

class CallArguments(SyntaxNode):
    positional: list[Expression | NamedArgument]
    named: list[Expression | NamedArgument]
    def __init__(
        self,
        positional: list[Expression | NamedArgument] | None = ...,
        named: list[Expression | NamedArgument] | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...

class Attribute(SyntaxNode):
    id: Identifier
    value: Pattern
    def __init__(
        self,
        id: Identifier,
        value: Pattern,
        *,
        span: Span | None = ...,
    ) -> None: ...

class Variant(SyntaxNode):
    def __init__(
        self,
        key: Identifier | NumberLiteral,
        value: Pattern,
        default: bool = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...

class NamedArgument(SyntaxNode):
    name: Identifier
    value: NumberLiteral | StringLiteral
    def __init__(
        self,
        name: Identifier,
        value: NumberLiteral | StringLiteral,
        *,
        span: Span | None = ...,
    ) -> None: ...

class Identifier(SyntaxNode):
    name: str
    def __init__(self, name: str, *, span: Span | None = ...) -> None: ...

class BaseComment(Entry):
    content: str | None
    def __init__(
        self,
        content: str | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...

class Comment(BaseComment):
    def __init__(
        self, content: str | None = ..., *, span: Span | None = ...
    ) -> None: ...

class GroupComment(BaseComment):
    def __init__(
        self, content: str | None = ..., *, span: Span | None = ...
    ) -> None: ...

class ResourceComment(BaseComment):
    def __init__(
        self, content: str | None = ..., *, span: Span | None = ...
    ) -> None: ...

class Junk(SyntaxNode):
    content: str | None
    annotations: list[Annotation]
    def __init__(
        self,
        content: str | None = ...,
        annotations: list[Annotation] | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...
    def add_annotation(self, annot: Annotation) -> None: ...

class Span(BaseNode):
    start: int
    end: int
    def __init__(self, start: int, end: int, **kwargs: Any) -> None: ...

class Annotation(SyntaxNode):
    code: str
    arguments: list[Any]
    message: str | None
    def __init__(
        self,
        code: str,
        arguments: list[Any] | None = ...,
        message: str | None = ...,
        *,
        span: Span | None = ...,
    ) -> None: ...
