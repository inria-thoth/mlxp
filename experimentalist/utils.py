import json
from collections.abc import MutableMapping

def flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    return dict(_flatten_dict_gen(d, parent_key, sep))


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def load_dict_from_json(json_file_name, prefix="metrics"):
    out_dict = {}
    try:
        with open(json_file_name) as f:
            for line in f:
                cur_dict = json.loads(line)
                keys = cur_dict.keys()
                for key in keys:
                    if prefix + "." + key in out_dict:
                        out_dict[prefix + "." + key].append(cur_dict[key])
                    else:
                        out_dict[prefix + "." + key] = [cur_dict[key]]
    except Exception as e:
        print(str(e))
    return out_dict