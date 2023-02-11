from collections.abc import MutableMapping, Mapping
import omegaconf
import importlib


class LazyDict(MutableMapping):
    def __init__(self, *args, **kw):
        self._raw_dict = dict(*args, **kw)

    def __getitem__(self, key):
        obj = self._raw_dict.__getitem__(key)
        if callable(obj):
            return obj(key)
        else:
            return obj

    def __iter__(self):
        return iter(self._raw_dict)

    def __len__(self):
        return len(self._raw_dict)

    def __delitem__(self,key):
        del self._raw_dict[key]
    def __setitem__(self,key,value):
        self._raw_dict[key]=value

def _flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    return dict(_flatten_dict_gen(d, parent_key, sep))


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from _flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v

class Config(dict):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.__dict__ = self

    # def to_instance(self,**opt_config):
    #     all_config = {**self, opt_config}
    #     module_name = self.pop("name")
    #     attr = import_module(module_name)
    #     if all_config:
    #         attr = attr(**all_config)
    #     return attr

def config_to_dict(config):
    done = False
    out_dict = {}
    for key, value in config.items():
        if isinstance(value, omegaconf.dictconfig.DictConfig):
            out_dict[key] = config_to_dict(value)
        else:
            out_dict[key] = value
    return Config(out_dict)




def import_module(module_name):
    module, attr = os.path.splitext(module_name)
    try:
        module = importlib.import_module(module)
        return getattr(module, attr[1:])
    except:
        module = import_module(module)
        return getattr(module, attr[1:])

