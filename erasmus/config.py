from typing import Any

from botus_receptus import Config as BaseConfig


class Config(BaseConfig):
    services: dict[str, Any]
