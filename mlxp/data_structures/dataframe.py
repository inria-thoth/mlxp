"""Data structures returned by Reader object."""

from __future__ import annotations

import json
import marshal
import os
import types
from collections.abc import ItemsView, KeysView, Mapping, MutableMapping
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd
import yaml

from mlxp.data_structures.artifacts import Artifact, Artifact_types
from mlxp.enumerations import Directories
from mlxp.errors import InvalidArtifactError, InvalidKeyError, InvalidMapError

LAZYDATA = "METRIC"
LAZYARTIFACT = "ARTIFACT"

map_types = ["Generic", "Columnwise", "Rowwise", "Pointwise"]
Map = Tuple[Callable, Tuple[str, ...], Optional[Tuple[str, ...]]]


class DataDict(Mapping):
    """A dictionary of key values pairs where some values are loaded lazyly from a
    specific path whenever they are accessed."""

    def __init__(self, flattened_dict, parent_dir=None):
        self.config = {"flattened": flattened_dict, "lazy": _LazyDict(flattened_dict)}

        self.parent_dir = parent_dir

        self._make_lazydict()
        self._make_artifact()

    def _flattened(self):
        return self.config["flattened"]

    def _lazy(self):
        return self.config["lazy"]

    def __getitem__(self, key):
        """Get item corresponding to a key."""
        return self._lazy()[key]

    def __iter__(self):
        """Iterate over elements of the dictionary."""
        return iter(self._lazy())

    def __len__(self):
        """Return the number of items in the dictionary."""
        return len(self._lazy())

    def __repr__(self):
        """Return a view of the dictionary."""
        return repr(self._flattened())

    def _repr_html_(self):
        """Return a view of the dictionary compatible with html."""
        import pandas as pd

        df = pd.DataFrame([self._flattened()])
        return df._repr_html_()

    def keys(self):
        """Return keys of the dictionary."""
        return self._flattened().keys()

    def items(self):
        """Return items of the dictionary."""
        return self._lazy().items()

    def _make_lazydict(self):
        if self.parent_dir:
            all_keys = [key for key, value in self._flattened().items() if value == LAZYDATA]
            parent_keys = set([key.split(".")[0] for key in all_keys])
            metrics_dir = os.path.join(self.parent_dir, Directories.Metrics.value)
            # try:
            self.lazydata_dict = {
                parent_key: _LazyData(metrics_dir, parent_key) for parent_key in parent_keys
            }
            # except:
            #    pass

            self._lazy().update({key: self.lazydata_dict[key.split(".")[0]].get_data for key in all_keys})

    def _make_artifact(self):
        if self.parent_dir:
            all_keys = [key for key, value in self._flattened().items() if value == LAZYARTIFACT]
            artifacts_dir = os.path.join(self.parent_dir, Directories.Artifacts.value)
            artifact_types = set([key.split(".")[1] for key in all_keys])

            self.lazyartifact_dict = {
                artifact_type: _LazyArtifact(artifacts_dir, artifact_type) for artifact_type in artifact_types
            }

            self._lazy().update({key: self.lazyartifact_dict[key.split(".")[1]].get_data for key in all_keys})

    def update(self, new_dict):
        """Update the dictionary with values from another dictionary."""
        copy_dict = {key: LAZYDATA if callable(value) else value for key, value in new_dict.items()}
        self._lazy().update(new_dict)
        self._flattened().update(copy_dict)

    def _free_unused(self):
        if self.parent_dir:
            for key, data in self.lazydata_dict.items():
                data._free_unused()


class _LazyDict(MutableMapping):
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

    def __delitem__(self, key):
        del self._raw_dict[key]

    def __setitem__(self, key, value):
        self._raw_dict[key] = value


class _LazyData(object):
    def __init__(self, parent_dir, file_name, extension=".json"):
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

    def _free_unused(self):
        if self._data:
            all_keys = set(self._data.keys())
            unused_keys = all_keys.difference(self.used_keys)
            for key in unused_keys:
                del self._data[key]


class _LazyArtifact(object):
    def __init__(self, artifacts_dir, artifact_type):
        self.artifact_type = artifact_type
        self.artifacts_dir = artifacts_dir
        if artifact_type in Artifact_types:
            self.load = Artifact_types[artifact_type]["load"]
            self.save = Artifact_types[artifact_type]["save"]
        else:

            types_file = os.path.join(artifacts_dir, ".keys/custom_types.yaml")
            try:
                with open(types_file, "r") as f:
                    types_dict_marshal = yaml.safe_load(f)
                code = marshal.loads(types_dict_marshal[artifact_type]["load"])
                self.load = types.FunctionType(code, globals(), "load")
                code = marshal.loads(types_dict_marshal[artifact_type]["save"])
                self.save = types.FunctionType(code, globals(), "save")
            except:
                raise InvalidArtifactError
        artifacts_dict_name = os.path.join(artifacts_dir, ".keys/artifacts.yaml")

        lazydata_dict = {}
        try:
            with open(artifacts_dict_name, "r") as f:
                keys_dict = yaml.safe_load(f)
            if keys_dict:
                self.artifacts = keys_dict[artifact_type]
        except:
            raise InvalidArtifactError

        self.used_keys = set()
        self._data = {}

    def get_data(self, key):
        splitted_key = key.split(".")[2:]
        parent_key = ".".join(splitted_key)
        if not self._data or parent_key not in self.used_keys:
            parent_dir = os.path.join(*tuple(splitted_key))
            parent_dir = os.path.join(self.artifacts_dir, self.artifact_type, parent_dir)
            self._data[parent_key] = {
                name: Artifact(name, parent_dir, self.load, self.save) for name in self.artifacts[parent_key]
            }
            self.used_keys.add(parent_key)
        return self._data[parent_key]

    def _free_unused(self):
        if self._data:
            all_keys = set(self._data.keys())
            unused_keys = all_keys.difference(self.used_keys)
            for key in unused_keys:
                del self._data[key]


class _MyListProxy:
    def __init__(self, list_of_dicts):
        self.list_of_dicts = list_of_dicts

    def __getitem__(self, key):
        return [d[key] for d in self.list_of_dicts]


class DataFrame(list):
    """A list of elements of type DataDict.

    This list can be viewed as a dataframe where each row represents a given entry of type
    DataDict and columns represent the keys of the DataDict objects.  This structure allows to
    load some columns lazyly: the content of these columns is loaded from their
    corresponding file only when that column is explicitly accessed.

    It is displayed as a pandas dataframe and can be converted to it using the method
    toPandas.
    """

    def __init__(self, iterable: List[DataDict]):
        if iterable:
            for config in iterable:
                assert isinstance(config, DataDict)

        super().__init__(item for item in iterable)
        self.pandas_lazy = None
        self.pandas = None
        self._keys = None

    def __repr__(self):
        """Display the DataFrame object as a pandas dataframe."""
        return str(self.toPandas())

    def _repr_html_(self):
        """Display the DataFrame object as a pandas dataframe for html."""
        return self.toPandas()._repr_html_()

    def __getitem__(self, index):
        """Return the item at a given index."""
        if isinstance(index, slice):
            return _MyListProxy([d for d in super().__getitem__(index)])
        else:
            return super().__getitem__(index)

    def diff(self, start_key: str = "config") -> List[str]:
        """Return a list of colums keys starting with 'start_key' and whose value varies
        in the dataframe.

        :param start_key: A string with which all column names to be considered must
            start.
        :type start_key: str (default 'config')
        :return: A list of strings containing the column names starting with 'start_key'
            and whose values vary in the dataframe.
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
                        if key not in ref_dict and key.startswith(start_key):
                            diff_keys.append(key)

        return diff_keys

    def toPandas(self, lazy: bool = True) -> pd.DataFrame:
        """Convert the list into a pandas dataframe.

        :param lazy: If true the pandas dataframe does not contain the results of data
            loaded lazyly.
        :return: A panda dataframe containing logs (configs and data) of the DataFrame
            object
        :rtype: pd.DataFrame
        """
        if lazy:
            if self.pandas_lazy is None:
                self.pandas_lazy = pd.DataFrame([config._flattened() for config in self])
            return self.pandas_lazy
        else:
            if self.pandas is None:
                self.pandas = pd.DataFrame([config._lazy() for config in self])
            return self.pandas

    def keys(self) -> List[str]:
        """Return a list of column names of the dataframe.

        :return: List of strings containing the column names of the dataframe
        :rtype: List[str]
        """
        if self._keys is None:
            self._keys = list(self.toPandas().keys())
        return self._keys

    def groupby(self, group_keys: Union[str, List[str]]) -> GroupedDataFrame:
        """Perform a groupby operation on the dataframe according to a list of colum
        names (group_keys).

        Returns an object of the class GroupedDataFrame

        :params group_keys: A string or list of strings containing the names of the
            columns to be grouped.
        :type group_keys: Union[str,List[str]]
        :return: A dictionary of dataframes grouped by the values of the columns
            provided to group_keys. Each key of the dictionary is a tuple of values
            taken by the columns in group_keys.
        :rtype: GroupedDataFrame
        :raises InvalidKeyError: if one of the provided keys does not match any column
            of the dataframe.
        """
        # Check if keys are valid
        group_keys = _to_list_str(group_keys)
        _check_valid_keys(group_keys, self.keys())

        # Need to handle the case when keys are empty
        collection_dict, group_vals = _group_by(self, group_keys)
        return GroupedDataFrame(group_keys, collection_dict)

    def aggregate(self, maps: Union[Map, List[Map]]) -> DataFrame:
        """Perform aggregation of of columns of a dataframe according to some
        aggregation maps and returns a new dataframe with a single row.

        This function returns a DataFrame object with a single row containing the results of the aggregation maps.

        :params maps: Either an element of type Map or a list of elements of type Map.
            A Map is a tuple with signature Tuple[Callable, Tuple[str, ...], Optional[Tuple[str, ...]]].
            - The first element is a Callable[[List[Any]], Union[Any,Tuple[Any,...]]] that must take a list of all values of a given column in the dataframe.
            It must reduce the list into a single element of arbitrary type which is stored as the value of a single output column in a dataframe with a single row.
            - The second element of the Map tuple represents the list of columns in the dataframe on which the map is applied columnwise.
            - The third element reprensents the optional name of the output columns.
        :type maps: Union[Map, List[Map]]
        :return: A DataFrame object containing the result of the aggregation maps.
        :rtype: DataFrame
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """
        maps = format_apply_map(maps, "Columnwise")
        res = _apply_column_wise_map(self, maps)
        return DataFrame([DataDict(res)])
        # return _aggregate(self, aggregation_maps)

    def apply(self, maps: Union[Map, List[Map]], map_type="Generic") -> DataFrame:
        """Applies a generic map or list of maps to a dataframe.

        This function returns a DataFrame object containing the results of applying the maps to the dataframe.

        :params maps: Either an element of type Map or a list of elements of type Map.
            A Map is a tuple with signature Tuple[Callable, Tuple[str, ...], Optional[Tuple[str, ...]]].
            - The first element of a Map is a callable to be applied to the dataframe.
            - The second element of the Map represents the list of columns in the dataframe to provide as input to the callable.
            - The third element reprensents the optional name of the output columns.
        :type maps: Union[Map, List[Map]]
        :params map_type: Specifies the types of maps to be applied: 'Generic', 'Columnwise', 'Rowwise', 'Pointwise':
            - 'Pointwise': In this case, the apply method is equivalent to the method map. It applied the maps pointwise on each value corresponding to a row and selected column.
            - 'Columnwise': In this case, the apply method is equivalent to either tranform or aggregate method. It applies the maps columnwise and expects the output to either preserve the same number of rows as the initial dataframe (as the tranform method) or to reduce it to a single value (like the aggregate method).
            - 'Rowwise': Applied a map rowise. In that case, the apply method returns a dataframe with the same number of rows as the initial one. The signature of the callable (the first element of the tuple Map) must be Callable[[Union[Any,Tuple[Any,...]]], Any]. It takes the values of some specific columns at a single row and returns an output for that row. The column names on which the map operates are provided as the second element of the Map tuple.
            - 'Generic': Extends the transform and aggregate methods to support operations that are not columnwise. The input to the callable (the first element of the tuple Map) must be either List[Any] or Tuple[List[Any],...].
            The callable must have the same return type as the callables used in a transform or aggregate methods: either Union[Any,Tuple[Any,...]] or  Union[List[Any],Tuple[List[Any],...]].
            It takes lists of values of some specific columns applies the map to them and returns transformed outputs that can be either lists of values (as in the tranform method) or single values (as in the aggregate method).
        :return: A DataFrame object containing the result of the maps.
        :rtype: DataFrame
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """

        assert map_type in map_types
        if map_type == "Columnwise":
            res, _ = self._apply_column_wise_map(maps)
        elif map_type == "Rowwise":
            res, _ = self._apply_row_wise_map(maps)
        elif map_type == "Pointwise":
            res, _ = self._apply_pointwise_map(maps)
        elif map_type == "Generic":
            res, _ = self._apply_generic_map(maps)

        return res

    def transform(self, maps: Union[Map, List[Map]]) -> DataFrame:
        """Applies a map columnwise to a dataframe while preserving the number of rows.

        This function returns a DataFrame object containing the results of the tranformation maps.
        The new dataframe has the same number of rows as the initial dataframe on which the transform is applied.
        This method extends the map method to support operation that are not pointwise and can depend on values from different rows of the same column.

        :params maps: Either an element of type Map or a list of elements of type Map.
            A Map is a tuple with signature Tuple[Callable, Tuple[str, ...], Optional[Tuple[str, ...]]].
            - The first element is a Callable[[List[Any]], Union[List[Any],Tuple[List[Any],...]]] that must take a list of all values of a given column in the dataframe.
            It must return a list or a tuple of lists of elements of arbitrary types.
            The size of the returned lists must be the same as the input list.
            Each element of the returned lists corresponds to a transformation of the value at a given row and columns of the original dataframe.
            - The second element of the Map tuple represents the list of columns in the dataframe on which the map is applied columnwise.
            - The third element reprensents the optional name of the output columns.
        :type maps: Union[Map, List[Map]]
        :return: A DataFrame object containing the result of the columnwise maps.
        :rtype: DataFrame
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """

        res, reducing = self._apply_column_wise_map(maps)
        assert not reducing
        return res

    def map(self, maps: Union[Map, List[Map]]) -> DataFrame:
        """Applies a map pointwise to each value corresponsing to specified columns of
        the dataframe.

        This function returns a DataFrame object containing the results of the pointwise maps.
        The new dataframe has the same number of rows as the initial dataframe on which the transform is applied.
        Each row is processed independtly from the others.

        :params maps: Either an element of type Map or a list of elements of type Map.
            A Map is a tuple with signature Tuple[Callable, Tuple[str, ...], Optional[Tuple[str, ...]]].
            - The first element is a Callable[[Any], Any] that must take a value corresponding to a given row and column in the dataframe and tranforms it.
            - The second element of the Map tuple represents the list of columns in the dataframe on which the map is applied columnwise.
            - The third element reprensents the optional name of the output columns.
        :type maps: Union[Map, List[Map]]
        :return: A DataFrame object containing the result of the pointwise map.
        :rtype: DataFrame
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """
        res, reducing = self._apply_pointwise_map(maps)
        assert not reducing
        return res

    def filter(self, filter_map: Map, bygroups: Union[None, str, List[str]] = None) -> DataFrame:
        """Returns a new dataframe containing a subset of rows of the initial dataframe
        that pass a given filter.

        :params filter_map: An element of type Map.
            A Map is a tuple with signature Tuple[Callable, Tuple[str, ...], Optional[Tuple[str, ...]]].
            - The first element of the filter map is a function with signature Callable[[Union[List[Any], Tuple[List[Any],...]]], List[Any]] that can take a list or a tuple of lists.
            Each input list contains all values of some columns of the dataframe defined in the second element of the Map tuple.
            The filter map must return a list of booleans of the same size as the initial lists, each boolean value corresponding to an element of the initial lists at the same location.
            Only rows of the dataframe for whicht the returned boolean value is true pass the filter.
            - The second element of the Map tuple represents the list of columns that the filter map takes as input.
            - The third element of the Map tuple is never used.
        :type filter_map: Union[Map, List[Map]]
        :params bygroups: Optionally apply the filter by groups when bygroups is either a column name or list of column names by which the dataframe must be grouped.
            Once the filter is applied by group, the groups are merged together into a single ungrouped dataframe. This is equivalent to performing self.groupby(bygroups).filter(filter_map).ungroup()
        :type bygroups: Union[None,str,List[str]]
        :return: A DataFrame object containing a filtered version of the initial dataframe.
        :rtype: DataFrame
        :raises InvalidMapError: if the filter map are not of type List[Map] or Map.
        """

        filter_map = format_apply_map(filter_map, "Generic")

        if bygroups:
            return self.groupby(bygroups).filter(filter_map).ungroup()
        else:
            res, reducing = self._apply_generic_map(filter_map)
            keys = res.keys()
            conditions = [bool(r[keys[0]]) for r in res]
            _check_filter(len(keys), len(filter_map), reducing)
            filtered = [el for el, cond in zip(self, conditions) if cond]

        return DataFrame(filtered)

    def sort(self, by: Union[str, List[str]], ascending: bool = True) -> DataFrame:
        """Returns a sorted dataframe according to a list of columns.

        :params by: Either column name or a list of column names by which the dataframe
            must be sorted with.
        :type maps: Union[str,List[str]]
        :params ascending: Sorting either by increasing values (ascending=True) or
            descreasing values (ascending=False) of the specified columns.
        :type ascending: bool
        :return: A sorted DataFrame object.
        :rtype: DataFrame
        """
        by = _to_list_str(by)

        # Sort the data by the given column(s)
        sorted_data = sorted(self, key=lambda x: tuple(x[key] for key in by), reverse=not ascending)

        return DataFrame(sorted_data)

    def _apply_row_wise_map(self, maps: Union[Map, List[Map]]) -> DataFrame:
        maps = format_apply_map(maps, "Rowwise")
        output = _apply_row_wise_map(self, maps)
        return DataFrame([DataDict(res) for res in output]), False

    def _apply_column_wise_map(self, maps: Union[Map, List[Map]]) -> DataFrame:

        maps = format_apply_map(maps, "Columnwise")
        output = _apply_column_wise_map(self, maps)
        output, reducing = _format_reducing(output, len(self))
        if reducing:
            return DataFrame([DataDict(output)]), reducing
        else:
            return DataFrame([DataDict(res) for res in output]), reducing

    def _apply_generic_map(self, maps: Union[Map, List[Map]]) -> DataFrame:
        maps = format_apply_map(maps, "Generic")
        output = _apply_generic_map(self, maps)
        output, reducing = _format_reducing(output, len(self))
        if reducing:
            return DataFrame([DataDict(output)]), reducing
        else:
            return DataFrame([DataDict(res) for res in output]), reducing

    def _apply_pointwise_map(self, maps: Union[Map, List[Map]]) -> DataFrame:
        maps = format_apply_map(maps, "Pointwise")
        output = _apply_pointwise_map(self, maps)
        return DataFrame([DataDict(res) for res in output]), False


class GroupedDataFrame:
    """A dictionary where each key represents the tuple of values taken by the grouped
    column of some processed dataframe.

    The values corresponsing to each key are objects of type DataFrame containing a group.
    This object is usually obtained as the output of the group_by method of the class  DataFrame.
    It is displayed as a hierarchical pandas dataframe and
    can be converted to it using toPandas method.

    .. py:attribute:: group_keys
        :type: List[str]

        A list of string containing the column names used for grouping.

    .. note:: It is possible to directly access the keys and values of self.grouped_dict
            by identifying self with self.grouped_dict:

            - Using self[key] instead of self.grouped_dict[key] to access the value of self.grouped_dict at a given key

            - Using self.keys() to get all keys of self.grouped_dict.

            - Using self.items() to iterate over the key/value pairs of self.grouped_dict.
    """

    def __init__(
        self, group_keys: List[str], grouped_dict: Dict[Tuple[str, ...], Union[GroupedDataFrame, DataFrame]]
    ):
        """Create an GroupedDataFrame object.

        :param group_keys: A list of string containing the column names used for grouping.
        :param grouped_dict: A dictionary where each key represents the tuple of values
        taken by the grouped column of some processed dataframe.
        The values corresponsing to each key are objects of type DataFrame containing a group.

        :type group_keys: List[str]
        :type grouped_dict: Dict[Tuple[str, ...], DataFrame]
        """
        self.group_keys = group_keys
        self.grouped_dict = grouped_dict
        self.group_vals = list(self.grouped_dict.keys())
        self._current_index = 0
        self.groups_size = len(self.group_vals)
        self.pandas = None
        self.pandas_lazy = None

    def __iter__(self):
        """Iterate over the groups of the GroupedDataFrame object."""
        return iter(self.grouped_dict)

    def __getitem__(self, key: Tuple[str, ...]) -> Union[GroupedDataFrame, DataFrame]:
        """Return the group corresponding to a given group key."""
        return self.grouped_dict[key]

    def __repr__(self):
        """Display the GroupedDataFrame object as a pandas dataframe."""
        return str(self.toPandas())

    def items(self) -> ItemsView:
        """Return the items of the grouped dictionary.

        :return: items of the dictionary
        :rtype: ItemsView
        """
        return self.grouped_dict.items()

    def keys(self) -> KeysView:
        """Return the keys of the grouped dictionary.

        :return: keys of the dictionary
        :rtype: KeysView
        """
        return self.grouped_dict.keys()

    def ungroup(self) -> DataFrame:
        """Concatenates the dataframes representing each group into a single dataframe.
        The group keys are added as columns to the resulting dataframe.

        :return: A dataframe representing the ungrouped version of the groupped
            dictionary.
        :rtype: DataFrame
        """
        data_list = []
        try:
            assert all(isinstance(config_list, GroupedDataFrame) for keys, config_list in self.items())
            ungrouped_dict = {keys: config_list.ungroup() for keys, config_list in self.items()}
            return GroupedDataFrame(self.group_keys, ungrouped_dict)
        except:
            assert all(isinstance(config_list, DataFrame) for keys, config_list in self.items())
            for keys, config_list in self.items():
                group_dict = {key_name: key for key_name, key in zip(self.group_keys, list(keys))}
                for data_dict in config_list:
                    data_dict.update(group_dict)
                data_list += [data_dict for data_dict in config_list]
            return DataFrame(data_list)

    def toPandas(self, lazy=True) -> pd.DataFrame:
        """Convert. the list into a pandas dataframe.

        :param: If true the pandas dataframe does not contain the results of data loaded
            lazyly.
        :return: A panda dataframe containing logs (configs and data) of the DataFrame
            object
        :rtype: pd.DataFrame
        """
        if lazy:
            if self.pandas_lazy is None:
                self.pandas_lazy = _groups_toPandas(self.grouped_dict, self.group_keys, True)
            return self.pandas_lazy
        else:
            if self.pandas is None:
                self.pandas = _groups_toPandas(self.grouped_dict, self.group_keys, False)
            return self.pandas

    def _apply_to_groups(
        self, maps, operation, kwargs, ungroup: bool = False
    ) -> Union[GroupedDataFrame, DataFrame]:
        grouped_res = {}
        for keys, config_list in self.items():
            method = getattr(config_list, operation)
            grouped_res[keys] = method(maps, **kwargs)
        if ungroup:
            return GroupedDataFrame(self.group_keys, grouped_res).ungroup()
        return GroupedDataFrame(self.group_keys, grouped_res)

    def apply(
        self, maps: Union[Map, List[Map]], map_type="Generic", ungroup: bool = False
    ) -> GroupedDataFrame:
        """Applies a generic tranformation to each dataframe representing each group.
        see DataDictsList.apply. Returns a groupped dataframe of type GroupedDataFrame
        that is optionally ungroupped into a dataframe object of type DataFrame.

        :params maps: Either a single instance of tuple Map or a list of tuple of type
            Map.
        :type maps: Union[Map, List[Map]]
        :params map_type: Type of the transformation to apply (see DataDictsList.apply):
            'Generic', 'Columnwise', 'Rowwise' or 'Pointwise'.
        :type map_type: str
        :params ungroup: Optionally returns a ungroupped version of the result.
        :type ungroup: bool
        :return: An object containing the result of the applied transformations.
        :rtype: Union[GroupedDataFrame,DataFrame]
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """
        return self._apply_to_groups(maps, "apply", {"map_type": map_type})

    def aggregate(
        self, maps: Union[Map, List[Map]], ungroup: bool = False
    ) -> Union[GroupedDataFrame, DataFrame]:
        """Perform aggregation of the dataframe corresponding to each group. see
        DataDictsList.aggregate. Returns a groupped dataframe of type GroupedDataFrame
        that is optionally ungroupped into a dataframe object of type DataFrame.

        :params maps: Either a single instance of tuple Map or a list of tuple of type
            Map.
        :type maps: Union[Map, List[Map]]
        :params ungroup: Optionally returns a ungroupped version of the result.
        :type ungroup: bool
        :return: An object containing the result of the aggregation.
        :rtype: Union[GroupedDataFrame,DataFrame]
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """
        return self._apply_to_groups(maps, "aggregate", {}, ungroup=ungroup)

    def filter(
        self, filter_map: Map, bygroups: Union[None, str, List[str]] = None, ungroup: bool = False
    ) -> Union[GroupedDataFrame, DataFrame]:
        """Filters the dataframe of each group. see DataDictsList.filter. Returns a
        groupped dataframe of type GroupedDataFrame that is optionally ungroupped into a
        dataframe object of type DataFrame.

        :params filter_map: An instance of tuple Map.
        :type filter_map: Map
        :params ungroup: Optionally returns a ungroupped version of the result.
        :type ungroup: bool
        :params bygroups: Optionally apply the filter by groups when bygroups is either a column name or list of column names by which the dataframe must be grouped.
            Once the filter is applied by group, the groups are merged together into a single ungrouped dataframe. This is equivalent to performing self.groupby(bygroups).filter(filter_map).ungroup()
        :type bygroups: Union[None,str,List[str]]
        :return: An object containing the result of the filtering.
        :rtype: Union[GroupedDataFrame,DataFrame]
        :raises InvalidMapError: if the map is not of type Map.
        """
        if bygroups:
            filtered = self.ungroup().groupby(bygroups).filter(filter_map, ungroup=True)
            if ungroup:
                return filtered
            return filtered.groupby(self.group_keys)
        else:
            return self._apply_to_groups(filter_map, "filter", {}, ungroup=ungroup)

    def transform(
        self, maps: Union[Map, List[Map]], ungroup: bool = False
    ) -> Union[GroupedDataFrame, DataFrame]:
        """Applies a columnwise tranformation to the dataframe corresponding to each
        group. see DataDictsList.transform. Returns a groupped dataframe of type
        GroupedDataFrame that is optionally ungroupped into a dataframe object of type
        DataFrame.

        :params maps: Either a single instance of tuple Map or a list of tuple of type
            Map.
        :type maps: Union[Map, List[Map]]
        :params ungroup: Optionally returns a ungroupped version of the result.
        :type ungroup: bool
        :return: An object containing the result of the transformation.
        :rtype: Union[GroupedDataFrame,DataFrame]
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """

        return self._apply_to_groups(maps, "transform", {}, ungroup=ungroup)

    def map(self, maps: Union[Map, List[Map]], ungroup: bool = False) -> Union[GroupedDataFrame, DataFrame]:
        """Applies a pointwise tranformation to the dataframe corresponding to each
        group. see DataDictsList.map. Returns a groupped dataframe of type
        GroupedDataFrame that is optionally ungroupped into a dataframe object of type
        DataFrame.

        :params maps: Either a single instance of tuple Map or a list of tuple of type
            Map.
        :type maps: Union[Map, List[Map]]
        :params ungroup: Optionally returns a ungroupped version of the result.
        :type ungroup: bool
        :return: An object containing the result of the pointwise transformation.
        :rtype: Union[GroupedDataFrame,DataFrame]
        :raises InvalidMapError: if the maps are not of type List[Map] or Map.
        """
        return self._apply_to_groups(maps, "map", {}, ungroup=ungroup)

    def select(self, key_list: List[Tuple[str, ...]]) -> GroupedDataFrame:
        """Extracts subgroups from a group object that corresponding to specific values
        of the group keys.

        :params key_list: List of keys representing the groups to select.
        :type key_list: List[Tuple[str,...]]
        :return: An object containing the selected groups
        :rtype: GroupedDataFrame
        """
        grouped_dict = {key: value for key, value in self.grouped_dict.items() if key in key_list}
        return GroupedDataFrame(self.group_keys, grouped_dict)

    def sort(
        self, by: List[str], ascending: bool = True, ungroup: bool = False
    ) -> Union[GroupedDataFrame, DataFrame]:
        """Returns a grouped object where the dataframe of each group is sorted
        according to a list of columns. (see DataFrame.sort) optionally ungroupps the
        grouped object into a single dataframe of type DataFrame.

        :params by: Either column name or a list of column names by which the dataframe
            must be sorted with.
        :type maps: Union[str,List[str]]
        :params ascending: Sorting either by increasing values (ascending=True) or
            descreasing values (ascending=False) of the specified columns.
        :type ascending: bool
        :params ungroup: Optionally returns a ungroupped version of the result.
        :type ungroup: bool
        :return: A sorted object.
        :rtype: Union[GroupedDataFrame,DataFrame]
        """
        return self._apply_to_groups(by, "sort", {"ascending": ascending}, ungroup=ungroup)

    def groupby(self, group_keys: Union[str, List[str]]) -> GroupedDataFrame:

        return self._apply_to_groups(group_keys, "groupby", {}, ungroup=False)


def _groups_toPandas(grouped_dict, group_keys, lazy):
    all_configs = []
    # df_dict = {key: value.toPandas(lazy=lazy) for key,value in grouped_dict.items()}
    group_dfs = []

    # Iterate over groups and store group dataframes
    for key, value in grouped_dict.items():
        group_dfs.append(value.toPandas(lazy=lazy))

    # Concatenate group dataframes
    return pd.concat(group_dfs, keys=grouped_dict.keys(), names=group_keys).sort_index(axis=0)


################ Grouping


def _group_by(config_dicts, list_group_keys):
    collection_dict = {}
    group_vals = set()
    # group_keys = tuple(list_group_keys)
    for config_dict in config_dicts:
        pkey_list = [config_dict._flattened()[group_key] for group_key in list_group_keys]
        # pkey_val = [str(pkey) for pkey in pkey_list if pkey is not None]
        pkey_val = [pkey for pkey in pkey_list if pkey is not None]
        group_vals.add(tuple(pkey_val))
        _add_nested_keys_val(collection_dict, pkey_val, [config_dict])
    group_vals = list(group_vals)

    grouped_dict = {key: DataFrame(reduce(dict.get, key, collection_dict)) for key in group_vals}

    return grouped_dict, group_vals


def _add_nested_keys_val(dictionary, keys, val):
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
    except TypeError:
        parent[key] = val


################### maps


def _apply_pointwise_map(dataframe, apply_maps):
    all_input_keys, input_key_list = _extract_input_keys(apply_maps)

    input_dict = {key: [] for key in all_input_keys}
    outputs = []
    for row in dataframe:
        outputs_dict = {}
        for apply_map, input_keys in zip(apply_maps, input_key_list):
            output = tuple([apply_map[0](row[key]) for key in input_keys])
            outputs_dict.update(_output_apply_map_as_dict(apply_map, output))
        outputs.append(outputs_dict)
        row._free_unused()
    return outputs


def _apply_column_wise_map(dataframe, apply_maps):
    all_input_keys, input_key_list = _extract_input_keys(apply_maps)

    data = {key: dataframe[:][key] for key in all_input_keys}
    for row in dataframe:
        row._free_unused()

    data_dict = {}
    for i, (apply_map, input_keys) in enumerate(zip(apply_maps, input_key_list)):
        outputs = tuple([apply_map[0](data[key]) for key in input_keys])
        data_dict.update(_output_apply_map_as_dict(apply_map, outputs))

    return data_dict


def _apply_row_wise_map(dataframe, apply_maps):
    all_input_keys, input_key_list = _extract_input_keys(apply_maps)

    input_dict = {key: [] for key in all_input_keys}
    outputs = []
    for row in dataframe:
        outputs_dict = {}
        for apply_map, input_keys in zip(apply_maps, input_key_list):
            inputs = tuple([row[key] for key in input_keys])
            output = apply_map[0](*inputs)
            outputs_dict.update(_output_apply_map_as_dict(apply_map, output))
        outputs.append(outputs_dict)
        row._free_unused()
    return outputs


def _apply_generic_map(dataframe, apply_maps):
    all_input_keys, input_key_list = _extract_input_keys(apply_maps)

    data = {key: [] for key in all_input_keys}
    for row in dataframe:
        for key in all_input_keys:
            data[key].append(row[key])
        row._free_unused()

    data_dict = {}
    for apply_map, input_keys in zip(apply_maps, input_key_list):
        inputs = tuple([data[key] for key in input_keys])
        outputs = apply_map[0](*inputs)
        data_dict.update(_output_apply_map_as_dict(apply_map, outputs))
    return data_dict


def _format_reducing(data_dict, dataframe_size):

    reducing = [not len(value) == dataframe_size for key, value in data_dict.items()]

    assert all(red == True for red in reducing) or all(red == False for red in reducing)
    if not reducing[0]:
        outputs = [{key: value[i] for key, value in data_dict.items()} for i in range(dataframe_size)]
        return outputs, False
    else:
        return data_dict, True


########################## Output maps


def _output_apply_map_as_dict(apply_map, outputs):
    if isinstance(outputs, tuple):
        assert len(outputs) == len(apply_map[2])
        return {key: value for key, value in zip(apply_map[2], outputs)}
    else:
        assert len(apply_map[2]) == 1
        return {apply_map[2][0]: outputs}


###################### Assertions


def _check_filter(len_keys, len_maps, reducing):
    try:
        assert len_maps == 1
    except:
        message = "Only a single filter can be applied at a time."
        raise InvalidMapError(message)

    try:
        assert not reducing
    except:
        message = f"Invalid filter map: Should keep the same size as the dataframe"
        raise InvalidMapError(message)
    try:
        assert len_keys == 1
    except:
        message = f"Invalid filter map: Should have a single boolean output"
        raise InvalidMapError(message)


def _check_valid_keys(list_group_keys, valid_keys):
    for key in list_group_keys:
        try:
            assert key in valid_keys
        except AssertionError:
            message = f"The provided key {key} is invalid! Valid keys are: {str(valid_keys)}"
            raise InvalidKeyError(message)


################### Loading data


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


###################### Extracting keys


def _extract_input_keys(agg_maps):
    all_input_keys = []
    input_key_list = []
    for agg_map in agg_maps:
        if isinstance(agg_map[1], str):
            all_input_keys.append(agg_map[1])
            input_key_list.append((agg_map[1],))
        elif isinstance(agg_map[1], tuple):
            all_input_keys += list(agg_map[1])
            input_key_list.append(agg_map[1])
    return set(all_input_keys), input_key_list


################################# Format


def _to_list_str(inputs: Union[str, List[str, ...]]) -> List[str, ...]:

    if not isinstance(inputs, list):
        inputs = [inputs]
    assert all(isinstance(element, str) for element in inputs)
    return inputs


def _to_tuple_str(inputs: Union[str, Tuple[str, ...]]) -> Tuple[str, ...]:

    if not isinstance(inputs, tuple):
        inputs = tuple([inputs])
    assert all(isinstance(element, str) for element in inputs)
    return inputs


def _to_list_tuple(inputs: Union[Tuple, List[Tuple, ...]]) -> List[Tuple, ...]:

    if not isinstance(inputs, list):
        inputs = [inputs]
    assert all(isinstance(element, tuple) for element in inputs)
    return inputs


def format_apply_map(maps, map_type):
    maps = _to_list_tuple(maps)
    for i, func_tuple in enumerate(maps):
        assert callable(func_tuple[0])
        assert len(func_tuple) in [2, 3]
        func_tuple_input = _to_tuple_str(func_tuple[1])
        new_func_tuple = (func_tuple[0], func_tuple_input)
        if len(func_tuple) == 2:
            func_tuple_output = _infer_output_name(new_func_tuple, map_type)
        else:
            func_tuple_output = _to_tuple_str(func_tuple[2])
        _check_output_format(map_type, func_tuple_input, func_tuple_output)
        maps[i] = new_func_tuple + (func_tuple_output,)
    return maps


def _infer_output_name(func_tuple, map_type):

    if map_type in ["Generic", "Rowwise"]:
        func_name = func_tuple[0].__name__
        keys = "_".join(func_tuple[1])
        return tuple(["f" + func_name + "." + keys])
    elif map_type in ["Columnwise", "Pointwise"]:
        func_name = func_tuple[0].__name__
        return tuple(["f" + func_name + "." + key for key in func_tuple[1]])


def _check_output_format(map_type, func_tuple_input, func_tuple_output):

    if map_type in ["Columnwise", "Pointwise"]:
        assert len(func_tuple_input) == len(func_tuple_output)
