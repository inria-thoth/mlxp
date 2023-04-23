from __future__ import annotations
import os
import json
import yaml
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import itertools
from functools import reduce
import pandas as pd
from collections.abc import Mapping, MutableSequence, MutableMapping, KeysView, ItemsView

from typing import List, Dict, Tuple

from mlxpy.logger import Directories
from mlxpy.errors import InvalidKeyError, InvalidAggregationMapError

LAZYDATA="LAZYDATA" 


class AggregationMap:
    """
    An abstract class whose children can perform aggregations on arrays. 
    
    """

    def __init__(self, keys, func=None, args={}, map_name=""):
        self.func = func
        self.keys = keys
        self.args = args
        self.map_name = map_name
        self.name = self.make_name()
    def make_name(self):
        return self.map_name + "(" + ",".join(self.keys) + ")"
    
    def apply(self, data):
        # Input: List of dicts where each entry of the list
        # contains data corresponding to a config.
        # Output: Dict of outputs
        raise NotImplementedError


class DataDict(Mapping):
    """
    A dictionary of key values pairs where some values are loaded lazyly 
    from a specific path whenever they are accessed.


    """

    def __init__(self,flattened_dict, parent_dir =None):
        self.config = { "flattened": flattened_dict,
                        "lazy": LazyDict(flattened_dict)}
      
        self.parent_dir = parent_dir
        if self.parent_dir:
            self._make_lazydict()

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
    def keys(self):

        return self.config['flattened'].keys()

    def items(self):

        return self.config['lazy'].items()

    def flattened(self):
        return self.config['flattened']
    def lazy(self):
        return self.config['lazy']
    def _make_lazydict(self):
        all_keys = [ key for key,value in self.config["flattened"].items() 
                            if value==LAZYDATA ]
        parent_keys = set([key.split('.')[0] for  key in all_keys]) 
        #try:
        self.lazydata_dict = {parent_key: LazyData(self.parent_dir,parent_key) 
                                    for parent_key in parent_keys }
        #except:
        #    pass
        
        self.config['lazy'].update({ key: self.lazydata_dict[key.split('.')[0]].get_data 
                                    for key in all_keys})

    def update(self, new_dict):
        copy_dict = {key: LAZYDATA if callable(value) 
                        else value 
                        for key,value in new_dict.items()}
        self.config["lazy"].update(new_dict)
        self.config["flattened"].update(copy_dict)        
        

    def free_unused(self):
        for key, data in self.lazydata_dict.items():
            data.free_unused()


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


class LazyData(object):
    def __init__(self,parent_dir, 
                      file_name, 
                      extension = '.json'):
        self.file_name = file_name
        self.parent_dir = parent_dir
        self.path = os.path.join(self.parent_dir, self.file_name + extension)
        self.used_keys = set()
        self._data = None
    def get_data(self, key):
        if self._data is None or key not in self.used_keys:
            self._data = _load_dict_from_json(self.path, self.file_name)
            self.used_keys.add(key)
        return self._data[key]
    def free_unused(self):
        all_keys = set(self._data.keys())
        unused_keys = all_keys.difference(self.used_keys)
        for key in unused_keys:
            del self._data[key]

class _MyListProxy:
    def __init__(self, list_of_dicts):
        self.list_of_dicts = list_of_dicts

    def __getitem__(self, key):
        return [d[key] for d in self.list_of_dicts]

class DataDictList(list):
    """
    A list of elements of type DataDict. This list can be viewed as a dataframe 
    where each row represents a given entry (a DataDict) and columns represent 
    the keys of the DataDicts.  This structure allows to load some columns lazyly. 
    the content of some columns is loaded from its corresponding file 
    only when that column is explicitly accessed.
    
    It is displayed as a pandas dataframe and 
    can be converted to it using the method toPandasDF.


    """    


    def __init__(self, iterable: List[DataDict]):
        if iterable:
            for config in iterable:
                assert isinstance(config, DataDict) 
        
        super().__init__(item for item in iterable)
        self.pandas_lazy=None
        self.pandas=None
        self._keys=None

    def __repr__(self):
        return str(self.toPandasDF())
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            return _MyListProxy([d for d in super().__getitem__(index)])
        else:
            return super().__getitem__(index)


    def _repr_html_(self):
        return self.toPandasDF()._repr_html_()  

    def toPandasDF(self,lazy=True)->pd.DataFrame:
        """
        Converts the list into a pandas dataframe.
        
        :param lazy: If true the pandas dataframe does not contain the results of data loaded lazyly. 
        :return: A panda dataframe containing logs (configs and data) 
        of the DataDictList object
        :rtype: pd.DataFrame

        """
        if lazy:
            if self.pandas_lazy is None:
                self.pandas_lazy = pd.DataFrame([config.flattened() for config in self])
            return self.pandas_lazy
        else:
            if self.pandas is None:
                self.pandas = pd.DataFrame([config.lazy() for config in self])
            return self.pandas
    
    def keys(self)->List[str]:
        """
        Returns a list of column names of the dataframe. 

        :return: List of strings containing the column names of the dataframe
        :rtype: List[str]
        """
        if self._keys is None:
            self._keys = list(self.toPandasDF().keys())
        return self._keys

    def groupBy(self, list_group_keys:List[str] )->GroupedDataDicts:

        """
            Performs a groupby operation on the dataframe 
            according to a list of colum names (list_group_keys). 
            Returns an object of the class GroupedDataDicts 

            :params list_group_keys: a list of strings containing the names of the columns to be grouped.
            :type list_group_keys: List[str]
            :return: A hierarchical dataframe grouped by the values of the columns provided to list_group_keys.
            :rtype: GroupedDataDicts
            :raises InvalidKeyError: if one of the provided keys does not match any columns of the dataframe.

        """
        # Check if keys are valid
        valid_keys = self.keys()
        for key in list_group_keys:
            try:
                assert key in valid_keys
            except AssertionError:
                message = f"The provided key {key} is invalid! Valid keys are: {str(valid_keys)}"
                raise InvalidKeyError(message)


        # Need to handle the case when keys are empty
        collection_dict, group_keys, group_vals = _group_by(self, list_group_keys)
        # pandas_grouped_df = deepcopy(self.toPandasDF()).set_index(list_group_keys)
        grouped_config = GroupedDataDicts(group_keys, collection_dict)
        #grouped_config.pandas = pandas_grouped_df
        return grouped_config

    def config_diff(self, start_key="config")->List[str]:
        """
            Returns a list of colums keys starting with 'start_key' 
            and whose value varies in the dataframe.
            
            :param start_key: A string with which all column names to be considered must start. 
            :type start_key: str (default 'config')
            :return: A list of strings containing the column names 
            starting with 'start_key' and whose values vary in the dataframe.
            :rtype: List[str]
        """
        


        diff_keys = []
        ref_dict = None
        
        for item in self:
            if ref_dict is None:
                ref_dict = item
            else:
                for key in item.keys():
                    if key in ref_dict and key.startswith(start_key):
                        if ref_dict[key] != item[key]:
                            if key not in diff_keys:
                                diff_keys.append(key)
                    else:
                        if key not in diff_keys:
                            diff_keys.append(key)
        return diff_keys

class GroupedDataDicts:
    """
    A dictionary where each key represents the tuple of values taken by the grouped column of some processed dataframe. 
    The values corresponsing to each key are objects of type DataDictList containing a group. 
    This object is usually obtained as the output of the group_by method of the class  DataDictList.
    It is displayed as a hierarchical pandas dataframe and 
    can be converted to it using toPandasDF method.

    .. py:attribute:: group_keys
        :type: List[str]

        A list of string containing the column names used for grouping.
    
    .. note:: It is possible to directly access the keys and values of self.grouped_dict 
            by identifying self with self.grouped_dict:
            
            - Using self[key] instead of self.grouped_dict[key] to access the value of self.grouped_dict at a given key  
            
            - Using self.keys() to get all keys of self.grouped_dict.
            
            - Using self.items() to iterate over the key/value pairs of self.grouped_dict.
    """  


    def __init__(self, group_keys:List[str], 
                        grouped_dict:Dict[Tuple[str, ...], DataDictList]):   
        """
        Constructor
        :param group_keys: A list of string containing the column names used for grouping.
        :param grouped_dict: A dictionary where each key represents the tuple of values 
        taken by the grouped column of some processed dataframe. 
        The values corresponsing to each key are objects of type DataDictList containing a group. 

        :type group_keys: List[str]
        :type grouped_dict: Dict[Tuple[str, ...], DataDictList]

        """

        self.group_keys = group_keys
        self.grouped_dict = grouped_dict
        self.group_vals = list(self.grouped_dict.keys())
        self._current_index = 0
        self.groups_size = len(self.group_vals)
        self.pandas = None
    def __iter__(self):
            return iter(self.grouped_dict)

    def __getitem__(self, key:Tuple[str, ...])->DataDictList:
        """
        Returns the value of the dictionary at a given key
        """
        
        
        return self.grouped_dict[key]

    def __repr__(self):

        return str(self.toPandasDF())
    
    def items(self)->ItemsView:
        """
        Return the items of the grouped dictionary
            
        :return: items of the dictionary
        :rtype: ItemsView
        """

        return self.grouped_dict.items()
    
    def keys(self)->KeysView:
        """
        Return the keys of the grouped dictionary
        
        :return: keys of the dictionary    
        :rtype: KeysView
        """


        return self.grouped_dict.keys()


    def toPandasDF(self)->pd.DataFrame:
        """
        Converts the list into a pandas dataframe.

        :return: A panda dataframe containing logs (configs and data) 
        of the DataDictList object
        :rtype: pd.DataFrame

        """
        if self.pandas is None:
            all_configs = []
            for key, value in self.grouped_dict.items():
                data_dict = value[0].flattened()
                for name_key, val_key in zip(self.group_keys, list(key)):
                    if name_key not in data_dict.keys(): 
                        data_dict[name_key] = val_key
                if len(value)==1:
                    value = [DataDict(data_dict)]
                all_configs+=[el for el in value ]
            self.pandas = DataDictList(all_configs).toPandasDF().set_index(list(self.group_keys))
        return self.pandas

    def aggregate(self, aggregation_maps: List[AggregationMap])->Dict[str,GroupedDataDicts]:
        """
        Performs aggregation of the leaf dataframes according to some aggregation maps provided as input. 
        It returns a DataDictList object where each row represents a group 
        and each column consist of one of the following:
            - The results of the aggregation maps.
            - The original group keys of the current GroupedDataDicts object.
        
        :params aggregation_maps: A list of aggregation maps. 
            Each map must be an instance of class inheriting from the abstract class AggregationMap. 
        :type aggregation_maps: List[AggregationMap]
        :return: A DataDictList object containing the result of the aggregation. 
        :rtype: DataDictList
        :raises InvalidAggregationMapError: if one of the aggregation map is not an instance of a class 
        inheriting from the abstract class AggregationMap.
        """
        for agg_map in aggregation_maps:
            _assert_valid_map(agg_map)

        return _aggregate(self, aggregation_maps)







def _group_by(config_dicts, list_group_keys):

    collection_dict = {}
    group_vals = set()
    group_keys = tuple(list_group_keys)
    for config_dict in config_dicts:

        pkey_list = [ config_dict.flattened()[group_key] 
            for group_key in list_group_keys
        ]
        pkey_val = [str(pkey) for pkey in pkey_list if pkey is not None]
        group_vals.add(tuple(pkey_val))
        _add_nested_keys_val(
            collection_dict,  pkey_val, [config_dict]
        )
    group_vals = list(group_vals)
    
    grouped_dict = { key: DataDictList(reduce(dict.get, key, collection_dict)) 
                                for key in group_vals }

    return grouped_dict, group_keys, group_vals
    




def _add_nested_keys_val(dictionary,keys,val):
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
     

def _aggregate(groupedconfigs, aggregation_maps):
    # Returns a hierarchical dictionary whose leafs are instances of DataDictList

    agg_config_list = []
    for keys, config_list in groupedconfigs.items():
        
        agg_config = _aggregate_collection(config_list, aggregation_maps)
        for key_name, key in zip(groupedconfigs.group_keys, list(keys)):
            agg_config.update({key_name:key})
        agg_config_list.append(DataDict(agg_config))

    return  DataDictList(agg_config_list) 


def _aggregate_collection(collection, agg_maps):
    value_keys = _extract_keys_from_maps(agg_maps)
    agg_collection = {}

    val_array = []
    for config_dict in collection:
        data = {key: config_dict[key] for key in value_keys}
        val_array.append(data)
        config_dict.free_unused()

    data_dict = {}
    for agg_map in agg_maps:
        agg_val, index = agg_map.apply(val_array)
        data_dict.update(agg_val)
    return data_dict



def _load_dict_from_json(json_file_name, file_name):
    out_dict = {}
    try:
        with open(json_file_name) as f:
            for line in f:
                cur_dict = json.loads(line)
                keys = cur_dict.keys()
                for key in keys:
                    full_key = file_name + "." + key
                    if full_key in out_dict:
                        out_dict[full_key].append(cur_dict[key])
                    else:
                        out_dict[full_key] = [cur_dict[key]]
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



def _assert_valid_map(agg_map):
    try:
        assert issubclass(type(agg_map), AggregationMap)
    except AssertionError:
        message = f"The map {str(agg_map)} must be an instance of a child class of  {str(AggregationMap)}"
        raise InvalidAggregationMapError(message)


