from typing import TypeVar, AsyncContextManager, AsyncIterable

_ACMT = TypeVar('_ACMT')
AIContextManager = AsyncContextManager[AsyncIterable[_ACMT]]
