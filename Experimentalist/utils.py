



import json
import os
from functools import reduce
import numpy as np
from collections import defaultdict
from collections.abc import MutableMapping


class ConfigsList(object):
    def __init__(self,list_configs):
        self.list_configs = list_configs
    def __getitem__(self,items):
        return self.list_configs[items]
    def __add__(self,conflist):
        list_configs = self.list_configs +conflist.list_configs 
        return ConfigsList(list_configs)
    def __iter__(self):
        return iter(self.list_configs)
    def __len__(self):
        return len(self.list_configs)
    def append(self,val):
        self.list_configs.append(val)
    def group_by(self,list_group_keys):
        return group_by(self.list_configs,list_group_keys)
    def aggregate(self,list_group_keys,aggregation_maps,as_collection_list=True):
        group_dict = self.group_by(list_group_keys)
        agg_dict = aggregate(group_dict,aggregation_maps)
        if as_collection_list:
            return {key: reduce_collectionDict_to_list(value) for key,value in agg_dict.items()}
        else:
            return agg_dict
    def apply_function(self,function,group_key='metadata.logs.path'):
        return [ Collection( {'config':ConfigsList([config_dict]),
                              'value': function.apply(extract_data_from_config(config_dict,function.value_keys)),
                              'group_keys_val': [ config_dict['flattened'][group_key]],
                              'group_keys': [group_key] }) 
                for config_dict in self  ]
    def get_data(self,value_keys, group_key='metadata.logs.path'):
        def func(data, value_keys):
            return {key:data[key] for key in value_keys}
        function = Map(func,value_keys,name='')
        return self.apply_function(function,group_key=group_key)
    def add_to_config(self,function,parent_key,group_key='metadata.logs.path'):
        collection_list= self.apply_function(function,group_key=group_key)
        for collection in  collection_list:
                #collection['config']['hierarchical'][key].update(collection['value'])
            for key, value in collection['value'].items():
                collection['config']['flattened'][parent_key+'.'+key] = value
        

class CollectionList(list):
    def append_data(self,value_keys):
        return CollectionList([coll.append_data(value_keys) for coll in self]) 
    def apply(self,function):
        return CollectionList([coll.apply(function) for coll in self]) 
         
class Collection(dict):
    def append_data(self,value_keys):
        new_collection = Collection(self.copy())
        new_value_keys = get_new_value_keys(value_keys)
        if not new_value_keys:
            return new_collection
        data = extract_data_from_collection(self['config'],new_value_keys)
        if not 'value' in self:
            new_collection['value']=data
            return new_collection
        new_collection['value'].update(data)
        return new_collection
    def apply(self,function):
        ### TODO: Need to support multiple functions to extract all data at once
        new_collection = Collection(self.copy())
        new_value_keys = get_new_value_keys(function.value_keys)
        if not new_value_keys:
            return new_collection
        if isinstance(function,Map):
            list_data = [function.apply(extract_data_from_config(config,new_value_keys)) for config in self['config']]
            data = defaultdict(list)
            for key in list_data[0].keys():
                data[key] = [d[key] for d in list_data] ### Need to use a reserved structure for this list
        elif isinstance(function,AggMap):
            data = extract_data_from_collection(self['config'],new_value_keys)
            data,index = function.apply(data)
            config = ConfigsList([self['config'][index]]) if index else self['config']
            new_collection['config']=config
        if not 'value' in self:
            new_collection['value']=data
            return new_collection
        new_collection['value'].update(data)
        return new_collection
    def get_new_value_keys(self,value_keys):
        ### TODO: Need to ensure keys are unique
        if not 'value' in self:
            return value_keys
        return [ key if not key in self.['value'] for key in value_keys]


class CollectionDict(dict):
    def to_config_list(self):
        return reduce_collectionDict_to_list(self)        
    def aggregate(self,aggregation_maps):
        return aggregate(self,aggregation_maps)



class Map:
    def __init__(self, func, value_keys, args = {},name=None ):
        self.func = func
        self.value_keys=value_keys
        self.args = args
        if not name:
            name = '_'.join(value_keys)
        self.name = name
    def apply(self,data):
        ### takes a dict of list where each list contains data corresponding to a config
        ### returns a list of 
        return self.func(data,self.value_keys,**self.args)
    def make_name(self):
        return NotImplementedError

class AggMap:
    def __init__(self, func, value_keys, args = {},name=None ):
        self.func = func
        self.value_keys=value_keys
        self.args = args
        if not name:
            name = '_'.join(value_keys)
        self.name = name
    def apply(self,data):
        ### takes a dict of list where each list contains data corresponding to a config
        ### returns a dict of outputs
        return self.func(data,self.value_keys,**self.args)
    def make_name(self):
        return NotImplementedError


def group_by(config_dicts,list_group_keys):
    # list_group_keys: list of list of tuples hierarchical keys
    # Returns a hierarchical dictionary whose leafs are lists of config dicts  
    collection_dict= CollectionDict({})
    for config_dict in config_dicts:

        pkey_list = [[config_dict['flattened'][key] for key in group_keys ] for group_keys in list_group_keys]
        pkey_list = [[str(v) for v in pkey if v is not None] for pkey in pkey_list]
        pkey_val = ['_'.join(pkey) for pkey in pkey_list]
        
        safe_hierarchical_append(collection_dict,config_dict,pkey_val,list_group_keys)
        
    return collection_dict 


def aggregate(collection_dict,aggregation_maps):
        
    agg_dict = {}
    if not isinstance(collection_dict, Collection):
        for pkey_val, next_collection in collection_dict.items():
            agg_dict[pkey_val] = aggregate(next_collection,aggregation_maps)
        agg_dict = permute_keys(agg_dict)
        agg_dict = {key:CollectionDict(value) for key,value in agg_dict.items()}   

    else:
        agg_dict = aggregate_collection(collection_dict,aggregation_maps)
    return agg_dict


def permute_keys(dictionary):
    permuted_dict = {}
    for outer_key,outer_value in dictionary.items():
        for inner_key,inner_value in outer_value.items():
            if inner_key not in permuted_dict:
                permuted_dict[inner_key] = {}
            permuted_dict[inner_key][outer_key] = inner_value
    return permuted_dict


def aggregate_collection(collection,agg_maps):
    value_keys = extract_keys_from_maps(agg_maps)
    val_array = extract_data_from_collection(collection,value_keys)
    agg_collection = {}
    for agg_map in agg_maps:
        agg_val,index = agg_map.apply(val_array)
        config = ConfigsList([collection['config'][index]]) if index else collection['config']
        agg_collection[agg_map.name] = Collection({'config': config, 
                                        'value':agg_val,
                                        'name': agg_map.name,
                                        'agg_map': agg_map,
                                        'group_keys_val': collection['group_keys_val'],
                                        'group_keys': collection['group_keys']
                                        })
    return agg_collection

def extract_data_from_collection(collection,value_keys):
    ### returns a dict (value_key: list[obj] ) where 
    ### the size of the list matches the size of the collection 

    out_dict = defaultdict(list)
    for config_dict in collection['config']:
        data = extract_data_from_config(config_dict,value_keys)
        for key in value_keys:
            out_dict[key].append(data[key])

    return out_dict




def extract_data_from_config(config_dict,value_keys):
    group_keys = defaultdict(list)
    for key in value_keys:
        path = key.split('.')[0]
        group_keys[path].append(key)

    data_dict = {}
    for key_path, key_list in group_keys.items():
        data = load_data_from_config(config_dict,key_path)
        data_dict.update({key:data[key] for key in key_list})
    return data_dict

# def eval_hkey(key,data):
#     tuple_key = tuple(key.keyString.split('.'))
#     return reduce(dict.get,tuple_key,data)

def extract_keys_from_maps(agg_maps):
    seen = set()
    extracted_keys = []
    for agg_map in agg_maps:
        extracted_keys += [key for key in agg_map.value_keys if key not in seen and not seen.add(key)]
    
    return extracted_keys


def reduce_collectionDict_to_list(collection):
    assert isinstance(collection, CollectionDict) or isinstance(collection, Collection)
    list_config = []
    if not isinstance(collection, Collection):
        for pkey_val, next_collection in collection.items():
            list_config += reduce_collectionDict_to_list(next_collection)
    else:
        list_config = [collection]
    return list_config


def safe_hierarchical_append(dictionary,val,keys,list_group_keys):
    dico = dictionary
    parent = None
    for key in keys:
        parent = dico
        try:
            dico = dico[key]
        except:
            dico[key] = {}
            dico = dico[key]
    try:
        dico['config'].append(val)
    except:
        parent[key] = Collection({'config':ConfigsList([val]),
                        'group_keys_val': keys,
                        'group_keys': list_group_keys})



def load_dict_from_json(json_file_name, prefix='metrics'):
    out_dict = {}
    try:
        with open(json_file_name) as f:
            for line in f:
                cur_dict = json.loads(line)
                keys = cur_dict.keys()
                for key in keys:
                    if key in out_dict:
                        out_dict[prefix+'.'+key].append(cur_dict[key])
                    else:
                        out_dict[prefix+'.'+key] = [cur_dict[key]]
    except Exception as e:
        print(str(e))
    return out_dict

def load_data_from_config(config_dict,file_name):
    if file_name=='metadata':
        return config_dict['flattened']
    path= os.path.join(config_dict['flattened']['metadata.logs.path'],file_name+'.json')
    return load_dict_from_json(path, prefix=file_name)


def _flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.'):
    return dict(_flatten_dict_gen(d, parent_key, sep))


