from json import load as json_load
from collections import OrderedDict


class ConfigObject(OrderedDict):
    def __getattr__(self, name):
        return self[name]


def object_pairs_hook(pairs) -> ConfigObject:
    return ConfigObject(pairs)


def load(path) -> ConfigObject:
    with open(path, 'r') as f:
        return json_load(f, object_pairs_hook=object_pairs_hook)


__all__ = ['load']
