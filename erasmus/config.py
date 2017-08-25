from json import JSONDecoder, load as json_load
from collections import OrderedDict

class ConfigObject(OrderedDict):
    def __getattr__(self, name):
        return self[name]

def load(path):
    with open(path, 'r') as f:
        return json_load(f, object_pairs_hook=lambda pairs: ConfigObject(pairs))

__all__ = [ 'load' ]
