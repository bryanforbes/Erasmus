from typing import Union, Text, IO, Any
from collections import OrderedDict
import json


class JSONObject(OrderedDict):
    def __getattr__(self, name: str) -> Any:
        return self[name]

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def get(self, key: str, fallback: Any = None) -> Any:
        obj = self
        for part in key.split('.'):
            try:
                if isinstance(obj, list):
                    obj = obj[int(part)]
                elif isinstance(obj, dict):
                    obj = obj[part]
                else:
                    return fallback
            except (KeyError, TypeError):
                return fallback
        return obj


def loads(s: Union[Text, bytes], *args: Any, **kwargs: Any) -> Any:
    kwargs['object_pairs_hook'] = lambda x: JSONObject(x)
    return json.loads(s, *args, **kwargs)


def load(fp: IO[str], *args: Any, **kwargs: Any) -> Any:
    kwargs['object_pairs_hook'] = lambda x: JSONObject(x)
    return json.load(fp, *args, **kwargs)
