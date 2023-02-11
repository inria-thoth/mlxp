import os
import json
import yaml
from collections import defaultdict
from copy import deepcopy
from experimentalist.maps import Map, AggMap
from experimentalist.utils import _flatten_dict, LazyDict
from pathlib import Path
import itertools
from functools import reduce

from collections.abc import Mapping, MutableSequence




class Config(Mapping):

    def __init__(self,config_dict,parent_key=""):
        flattened_dict = _flatten_dict(config_dict, parent_key=parent_key) 
        self.config = {"hierarchical": config_dict, 
                        "flattened": flattened_dict,
                        "lazy": flattened_dict}
        self.parent_key = parent_key
        self.all_data = {}
        if self.parent_key:
            self.parent_key += "."
        self._load_keys()
        self._raw_dict = self.config["lazy"]

    def __getitem__(self,key):
        return self.config['lazy'][key]
    def __iter__(self):
        return iter(self.config['lazy'])

    def __len__(self):
        return len(self.config['lazy'])
    def __repr__(self):
        return repr(self.config['flattened'])

    def _repr_html_(self):
        import pandas as pd
        df = pd.DataFrame([self.config['flattened']])
        return df._repr_html_() 
    def flattened(self):
        return self.config['flattened']
    def hierarchical(self):
        return self.config['hierarchical']
    def lazy(self):
        return self.config['lazy']
    def update(self, new_dict):
        copy_dict = {key: "Lazy eval" if callable(value) 
                        else value 
                        for key,value in new_dict.items()  }
        lazy_dict = LazyDict(new_dict)
        lazy_dict.update(self.config["lazy"])
        self.config["lazy"] = lazy_dict
        #flat_dict = { file+'.'+key: "Lazy loading"  for key in keys_dict.keys()}
        self.config["flattened"].update(copy_dict)        
        
    def _load_keys(self):
        path = os.path.join(self.config["flattened"][self.parent_key+"logs.path"], ".keys" )
        files = []
        try:
            files = [
                Path(d).stem
                for d in os.listdir(path)
                if d.endswith('.yaml')
            ]
            self.all_data = {file: Data(self,file) for file in files }
        except:
            pass 
        
        for file in files:
            file_name = os.path.join(path, file+'.yaml')
            with open(file_name, "r") as f:
                keys_dict = yaml.safe_load(f)
            flat_dict = { file+'.'+key: self.all_data[file].get_data for key in keys_dict.keys()}
            self.update(flat_dict)
    def add_data(self, data):
        self.config["flattened"].update(data)

    def free_unused(self):
        for key, data in self.all_data.items():
            data.free_unused()


class Data(object):
    def __init__(self,config, file_name):
        self.config = config
        self.file_name = file_name
        self._data = None
        self.used_keys = set()
    def get_data(self, key):
        if self._data is None or key not in self.used_keys:
            if self.file_name == "metadata":
                self._data = self.config.flattened()
            else:
                path = os.path.join(self.config.flattened()["metadata.logs.path"], 
                                    self.file_name + ".json")
                self._data = _load_dict_from_json(path, prefix=self.file_name)
            self.used_keys.add(key)
        return self._data[key]
    def free_unused(self):
        all_keys = set(self._data.keys())
        unused_keys = all_keys.difference(self.used_keys)
        for key in unused_keys:
            del self._data[key]


class ConfigList(list):
    # List of configs
    def __init__(self, iterable):
        if iterable:
            for config in iterable:
                assert isinstance(config, Config) 
        super().__init__(item for item in iterable)
        self.pandas=None


    def __repr__(self):
        return str(self.toPandasDF())

    def _repr_html_(self):
        return self.toPandasDF()._repr_html_()  

    def toPandasDF(self):
        import pandas as pd
        if self.pandas is None:
            self.pandas = pd.DataFrame([config.flattened() for config in self])
        return self.pandas
    def keys(self):
        return self.toPandasDF().keys()

    def groupBy(self, list_group_keys=[]):
        # Need to handle the case when keys are empty
        collection_dict, group_keys, group_vals = _group_by(self, list_group_keys)
        #pandas_grouped_df = deepcopy(self.toPandasDF()).set_index(list_group_keys)
        grouped_config = GroupedConfigs(collection_dict, group_keys, group_vals)
        #grouped_config.pandas = pandas_grouped_df
        return grouped_config

    def config_diff(self):
        diff_keys = []
        ref_dict = self[0].hierarchical()["custom"]
        ref_dict = _flatten_dict(ref_dict, parent_key="metadata")
        
        for config in self:
            config_dict = config.hierarchical()["custom"]
            config_dict = _flatten_dict(config_dict, parent_key="metadata")
            for key in config_dict.keys():
                if key in ref_dict:
                    if ref_dict[key] != config_dict[key]:
                        if key not in diff_keys:
                            diff_keys.append(key)
                else:
                    if key not in diff_keys:
                        diff_keys.append(key)
        return diff_keys

class GroupedConfigs:
    # a hierarchical dictionary whose leafs are instances of ConfigList

    def __init__(self, grouped_configs, group_keys, group_vals):   
        #self.grouped_configs = grouped_configs
        #self.group_vals = group_vals
        self.group_keys = group_keys
        self.grouped_dict = { key: ConfigList(reduce(dict.get, key, grouped_configs)) 
                                for key in group_vals }
        self.group_vals = list(self.grouped_dict.keys())
        self._current_index = 0
        self.groups_size = len(self.group_vals)
        self.pandas = None
    def __iter__(self):
            return self
    def __next__(self):
        if self._current_index < self.groups_size:
            keys = self.group_vals[self._current_index]
            # key_dict = dict(zip(self.group_keys, keys))
            dict_val = self.__getitem__(keys)
            self._current_index += 1
            return keys, dict_val
        self._current_index = 0
        raise StopIteration

    def toPandasDF(self):
        if self.pandas is None:
            all_configs = []
            for key, value in self.grouped_dict.items():
                all_configs+=[el for el in value ]
            self.pandas = ConfigList(all_configs).toPandasDF().set_index(list(self.group_keys))
        return self.pandas

    def __getitem__(self, keys):
        #key_dict = dict(zip(self.group_keys, keys))
        return self.grouped_dict[keys]
    def items(self):
        return self.grouped_dict.items()
    def keys(self):
        return self.group_vals  
    def __repr__(self):
        
        return str(self.toPandasDF())

    def aggregate(self, aggregation_maps):
        return aggregate(self, aggregation_maps)

    def apply(self, map):
        raise NotImplementedError


def _group_by(config_dicts, list_group_keys):
    # list_group_keys: list of flattened keys
    # Returns a hierarchical dictionary whose leafs are instances of ConfigList
    #collection_dict = GroupedConfigs({})
    collection_dict = {}
    group_vals = set()
    group_keys = tuple(list_group_keys)
    for config_dict in config_dicts:

        pkey_list = [ config_dict.flattened()[group_key] 
            for group_key in list_group_keys
        ]
        pkey_val = [str(pkey) for pkey in pkey_list if pkey is not None]
        group_vals.add(tuple(pkey_val))
        add_nested_keys_val(
            collection_dict,  pkey_val, [config_dict]
        )
    group_vals = list(group_vals)
    
    return collection_dict, group_keys, group_vals
    




def add_nested_keys_val(dictionary,keys,val):
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
        parent[key] = dico + val
    except TypeError as e:
        #print(e)
        parent[key] = val
     

def aggregate(groupedconfigs, aggregation_maps):
    # Returns a hierarchical dictionary whose leafs are instances of ConfigList

    #agg_dict = AggregatedConfigs({})
    agg_config_dict = {agg_map.name: {} for agg_map in  aggregation_maps}
    for keys, config_list in groupedconfigs.items():
        
        agg_config = aggregate_collection(config_list, aggregation_maps)
        #keys = list(keys_vals.values())
        for agg_map in aggregation_maps:
            add_nested_keys_val(agg_config_dict[agg_map.name], keys, agg_config[agg_map.name])

            
    return {agg_map.name : GroupedConfigs(agg_config_dict[agg_map.name], 
                                        groupedconfigs.group_keys, 
                                        groupedconfigs.group_vals) for agg_map in aggregation_maps}


def aggregate_collection(collection, agg_maps):
    value_keys = _extract_keys_from_maps(agg_maps)
    agg_collection = {}

    val_array = []
    for config_dict in collection:
        data = {key: config_dict[key] for key in value_keys}
        val_array.append(data)
        config_dict.free_unused()

    for agg_map in agg_maps:
        agg_val, index = agg_map.apply(val_array)
        if index is not None:
            new_collection= ConfigList([deepcopy(collection[index])])
        else:
            new_collection = deepcopy(collection)
        for config_dict in new_collection:
            config_dict.update(agg_val)
        agg_collection[agg_map.name] = new_collection

    return agg_collection


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

def _extract_keys_from_maps(agg_maps):
    seen = set()
    extracted_keys = []
    for agg_map in agg_maps:
        extracted_keys += [
            key for key in agg_map.keys if key not in seen and not seen.add(key)
        ]

    return extracted_keys




