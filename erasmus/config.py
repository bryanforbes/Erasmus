from typing import Any, Dict
from botus_receptus import Config as BaseConfig


class Config(BaseConfig):
    services: Dict[str, Any]
