from typing import ContextManager, AsyncContextManager


class Typing(ContextManager['Typing'], AsyncContextManager['Typing']):
    async def do_typing(self) -> None: ...
