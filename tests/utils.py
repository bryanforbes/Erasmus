from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from unittest.mock import NonCallableMock

    from .types import MockerFixture


def create_context_manager(
    mocker: MockerFixture, context_value: Any, /, exit_value: bool = False
) -> NonCallableMock:
    return mocker.NonCallableMock(
        **{  #  pyright: ignore[reportGeneralTypeIssues]
            '__enter__.return_value': context_value,
            '__exit__.return_value': exit_value,
        }
    )


def create_async_context_manager(
    mocker: MockerFixture, context_value: Any, /, exit_value: bool = False
) -> NonCallableMock:
    return mocker.NonCallableMock(
        __aenter__=mocker.AsyncMock(return_value=context_value),
        __aexit__=mocker.AsyncMock(return_value=exit_value),
    )
