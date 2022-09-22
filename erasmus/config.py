from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from botus_receptus import Config as BaseConfig

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class ServiceConfig(TypedDict):
    api_key: NotRequired[str]


class Config(BaseConfig):
    services: dict[str, ServiceConfig]
