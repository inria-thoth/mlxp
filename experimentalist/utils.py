from collections.abc import MutableMapping
import importlib
import os
import mlxpy
import copy

def _flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    return dict(_flatten_dict_gen(d, parent_key, sep))


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from _flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v



def import_module(module_name):
    module, attr = os.path.splitext(module_name)
    if not attr:
        return  getattr(mlxpy, module)
    else:
        try:
            module = importlib.import_module(module)
            return getattr(module, attr[1:])
        except:
            try:
                module = import_module(module)
                return getattr(module, attr[1:])
            except:
                return eval(module+attr[1:])


def config_to_instance(config_module_name="name",**config):
    config = copy.deepcopy(config)
    module_name = config.pop(config_module_name)
    attr = import_module(module_name)
    if config:
        attr = attr(**config)
    else:
        attr = attr()
    return attr



