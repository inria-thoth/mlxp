from collections.abc import MutableMapping

def _flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    return dict(_flatten_dict_gen(d, parent_key, sep))


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v



