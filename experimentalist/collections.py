import os
import json

from collections import defaultdict
from copy import deepcopy
from experimentalist.maps import Map, AggMap
from experimentalist.utils import _flatten_dict



class ConfigList(object):
    # List of configs

    def __init__(self, config, root_name="", group_keys_val="", group_keys=[]):
        if "hierarchical" in config[0]:
            self.config = config
        else:
            self.config = [
                {"hierarchical": r, "flattened": _flatten_dict(r, parent_key=root_name)}
                for r in config
            ]

        self.group_keys_val = group_keys_val
        self.group_keys = group_keys
    def __repr__(self):
        return self.toPandasDF()

    def append(self, val):
        self.config.append(val)

    def toPandasDF(self):
        import pandas as pd

        return pd.DataFrame([config["flattened"] for config in self.config])

    def groupBy(self, list_group_keys=[]):
        # Need to handle the case when keys are empty
        return group_by(self.config, list_group_keys)

    def add_data(self, keys_or_maps):
        all_keys = set()
        for el in keys_or_maps:
            if isinstance(el, Map) or isinstance(el, AggMap):
                all_keys.add(*el.keys)
            elif isinstance(el, str):
                all_keys.add(el)
        all_keys = list(all_keys)
        all_data = extract_data_from_collection(self, all_keys)
        for el in keys_or_maps:
            if isinstance(el, AggMap):
                out_data, _ = el.apply(all_data)
                for config in self.config:
                    config["flattened"].update(out_data)
            elif isinstance(el, Map):
                for data, config in zip(all_data, self.config):
                    config["flattened"].update(el.apply(data))
            elif isinstance(el, str):
                for data, config in zip(all_data, self.config):
                    config["flattened"].update({el: data[el]})

    def get_data(self, keys):
        protected = ["group_keys_val", "group_keys"]
        out = {
            key: self.config[0]["flattened"][key]
            for key in keys
            if key not in protected
        }
        if "group_keys_val" in keys:
            out["group_keys_val"] = '-'.join(self.group_keys_val)
        if "group_keys" in keys:
            key_name = "-".join(
                ["-".join([el.split(".")[-1] for el in key]) for key in self.group_keys]
            )
            out["group_keys"] = key_name
        return out


class ConfigCollection(object):
    def __init__(self, collection_list):
        self.collection_list = collection_list
        self.pandas = None

    def __getitem__(self, items):
        return self.collection_list[items]

    def __add__(self, coll_list):
        collection_list = self.collection_list + coll_list.collection_list
        return ConfigCollection(collection_list)

    def __len__(self):
        return len(self.collection_list)
    def __repr__(self):
        if self.pandas is None:
            self.pandas = self.toPandasDF()
        # representation = self.pandas._repr_html_()
        # if representation is None:
        #     representation = self.pandas.__repr__()
        return repr(self.pandas)

    def _repr_html_(self):
        if self.pandas is None:
            self.pandas = self.toPandasDF()
        return self.pandas._repr_html_()    

    def add(self, keys_or_maps):
        for collection in self.collection_list:
            collection.add_data(keys_or_maps)

    def get(self, keys):
        return [collection.get_data(keys) for collection in self.collection_list]

    def groupBy(self, list_group_keys=[]):
        val_dict = defaultdict(list)
        for collection in self.collection_list:
            val_dict[collection.group_keys_val] += collection.config
        groups = {
            key: ConfigList(value).groupBy(list_group_keys)
            for key, value in val_dict.items()
        }
        all_group_keys = list(groups.keys())
        if len(all_group_keys) == 1:
            return groups[all_group_keys[0]]
        else:
            return groups

    def toPandasDF(self):
        import pandas as pd

        all_configs = []
        for collection in self.collection_list:
            all_configs += collection.config
        return pd.DataFrame([config["flattened"] for config in all_configs])


class GroupedConfigs(dict):
    # a hierarchical dictionary whose leafs are instances of ConfigList

    def toConfigCollection(self):
        collection_list = GroupedConfigs_to_ConfigList(self)
        return ConfigCollection(collection_list)

    def agg(self, aggregation_maps):
        return aggregate(self, aggregation_maps)

    def apply(self, map):
        raise NotImplementedError


class AggregatedConfigs(dict):
    def toConfigCollection(self):
        return {key: value.toConfigCollection() for key, value in self.items()}


def group_by(config_dicts, list_group_keys):
    # list_group_keys: list of list of tuples hierarchical keys
    # Returns a hierarchical dictionary whose leafs are instances of ConfigCollection
    collection_dict = GroupedConfigs({})
    for config_dict in config_dicts:

        pkey_list = [
            [config_dict["flattened"][key] for key in group_keys]
            for group_keys in list_group_keys
        ]
        pkey_list = [[str(v) for v in pkey if v is not None] for pkey in pkey_list]
        pkey_val = ["_".join(pkey) for pkey in pkey_list]

        safe_hierarchical_append(
            collection_dict, config_dict, pkey_val, list_group_keys
        )

    return collection_dict


def safe_hierarchical_append(dictionary, val, keys, list_group_keys):
    dico = dictionary
    parent = None
    for key in keys:
        parent = dico
        try:
            dico = dico[key]
        except KeyError:
            dico[key] = {}
            dico = dico[key]
    try:
        dico.config.append(val)
    except AttributeError:
        collection = ConfigList([val], group_keys_val=keys, group_keys=list_group_keys)
        parent[key] = ConfigCollection([collection])


def aggregate(collection_dict, aggregation_maps):
    # Returns a hierarchical dictionary whose leafs are instances of ConfigList

    agg_dict = AggregatedConfigs({})
    if not isinstance(collection_dict, ConfigCollection):
        for pkey_val, next_collection in collection_dict.items():
            agg_dict[pkey_val] = aggregate(next_collection, aggregation_maps)
        agg_dict = permute_keys(agg_dict)
        agg_dict = AggregatedConfigs(
            {key: GroupedConfigs(value) for key, value in agg_dict.items()}
        )
    else:
        agg_dict = aggregate_collection(collection_dict, aggregation_maps)
    return agg_dict


def aggregate_collection(collection_list, agg_maps):
    value_keys = extract_keys_from_maps(agg_maps)
    agg_collection = {}
    for collection in collection_list:

        val_array = extract_data_from_collection(collection, value_keys)

        for agg_map in agg_maps:
            agg_val, index = agg_map.apply(val_array)
            config = (
                [deepcopy(collection.config[index])]
                if index >= 0
                else deepcopy(collection.config)
            )
            for config_dict in config:
                config_dict["flattened"].update(agg_val)

            collection = ConfigList(
                config,
                group_keys_val=collection.group_keys_val,
                group_keys=collection.group_keys,
            )
            if agg_map.name not in agg_collection:
                agg_collection[agg_map.name] = [collection]
            else:
                agg_collection[agg_map.name].append(collection)

    for key in agg_collection.keys():
        agg_collection[key] = ConfigCollection(agg_collection[key])
    return AggregatedConfigs(agg_collection)


def permute_keys(dictionary):
    permuted_dict = {}
    for outer_key, outer_value in dictionary.items():
        for inner_key, inner_value in outer_value.items():
            if inner_key not in permuted_dict:
                permuted_dict[inner_key] = {}
            permuted_dict[inner_key][outer_key] = inner_value
    return permuted_dict


def GroupedConfigs_to_ConfigList(collection):
    assert isinstance(collection, GroupedConfigs) or isinstance(
        collection, ConfigCollection
    )
    list_config = []
    if not isinstance(collection, ConfigCollection):
        for pkey_val, next_collection in collection.items():
            list_config += GroupedConfigs_to_ConfigList(next_collection)
    else:
        list_config = collection
    return list_config


def extract_data_from_collection(collection, value_keys):
    # returns a dict (value_key: list[obj] ) where
    # the size of the list matches the size of the collection

    out = []
    for config_dict in collection.config:
        data = extract_data_from_config(config_dict, value_keys)
        out.append(data)
    return out


def extract_data_from_config(config_dict, value_keys):
    group_keys = defaultdict(list)
    for key in value_keys:
        path = key.split(".")[0]
        group_keys[path].append(key)

    data_dict = {}
    for key_path, key_list in group_keys.items():
        data = load_data_from_config(config_dict, key_path)
        data_dict.update({key: data[key] for key in key_list})
    return data_dict


def load_data_from_config(config_dict, file_name):
    if file_name == "metadata":
        return config_dict["flattened"]
    path = os.path.join(
        config_dict["flattened"]["metadata.logs.path"], file_name + ".json"
    )
    return _load_dict_from_json(path, prefix=file_name)

def _load_dict_from_json(json_file_name, prefix="metrics"):
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

def extract_keys_from_maps(agg_maps):
    seen = set()
    extracted_keys = []
    for agg_map in agg_maps:
        extracted_keys += [
            key for key in agg_map.keys if key not in seen and not seen.add(key)
        ]

    return extracted_keys




