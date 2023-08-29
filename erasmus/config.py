from __future__ import annotations

from typing import NotRequired, TypedDict

from botus_receptus import Config as BaseConfig


class ServiceConfig(TypedDict):
    api_key: NotRequired[str]


class Config(BaseConfig):
    services: dict[str, ServiceConfig]
