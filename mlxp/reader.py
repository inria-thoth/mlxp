"""The reader allows queryring the logs of several experiments and performing operations
on the content of these logs (e.g. grouping and aggregation)."""

import os
from collections.abc import MutableMapping
from typing import Optional, Union

import pandas as pd
import yaml
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.table import Document

from mlxp.data_structures.dataframe import LAZYARTIFACT, LAZYDATA, DataDict, DataFrame
from mlxp.enumerations import DataFrameType, Directories
from mlxp.parser import DefaultParser, Parser, _is_searchable


class Reader:
    """A class for exploiting the results stored in several runs contained in a same
    parent directory 'src_dir'.

    Once, created, it is possible to query the database using the method 'filter'
    to get the results matching a specific configuration setting.
    The result of the query is returned either as a DataFrame object or a pandas dataframe.
    The queries are processed using a parser inheriting form the abstract class Parser.
    By default, the parser is DefaultParser.
    However, the user can provide a custom parser with a custom syntax
    inheriting from the class Parser.

    .. py:attribute:: src_dir
        :type: str

        The absolute path of the source/parent directory
        containing logs of the runs.
        It must contain sub-directories 'src_dir/log_id',
        where log_id is the uniquely assigned id of a run.

    .. py:attribute:: dst_dir
        :type: str

        The destination directory where
        the database containing the runs is created.
        By default it is set to the source directory 'src_dir'.
        The user can select a different location for the database
        by setting the variable 'dst_dir' of the constructor to a different directory.
    """

    def __init__(
        self,
        src_dir: str,
        dst_dir: Optional[str] = None,
        parser: Parser = DefaultParser(),
        refresh: bool = True,
    ):
        """Create a reader object.

        :param src_dir: The path to the parent directory containing logs of several
            runs.
        :param dst_dir: The destination directory where the database will be created.
        :param parser: A parser for querying the database.
        :param refresh: Re-create the database even if it already exists.
        :type src_dir: str
        :type dst_dir: str (default None)
        :type parser: Parser (default DefaultParser)
        :type refresh: bool (default True)
        :raises PermissionError: if user has no writing priviledges on dst_dir
        """
        self.parser = parser
        self.src_dir = os.path.abspath(src_dir)
        self.file_name = "database"
        if dst_dir is None:
            dst_dir = self.src_dir
        self.dst_dir = _ensure_writable(dst_dir)

        self.database = TinyDB(
            os.path.join(self.dst_dir, self.file_name + ".json"),
            storage=JSONStorage,
            sort_keys=True,
            indent=4,
            separators=(",", ": "),
        )
        self.runs = self.database.table("runs")
        self._fields = self.database.table("fields")

        if not self.database.tables() or refresh:
            print("Creating a database file of the runs...")
            self._create_base()
            print(f"Database file created in {self.dst_dir}")

    def __len__(self) -> int:
        """Return the number of runs contained in the database created by the reader.

        :return: Number of runs contained in the database.
        :rtype: int
        """
        return len(self.runs)

    def __del__(self):
        self.database.close()

    def filter(
        self, query_string: str = "", result_format: str = DataFrameType.DataFrame.value,
    ) -> Union[DataFrame, pd.DataFrame]:
        """Search a query in a database of runs.

        :param query_string: a string defining the query constaints.
        :param result_format: format of the result (either a pandas dataframe or an
            object of type DataFrame). By default returns a DataFrame object.
        :type query_string: str (default "")
        :type result_format: str (default False)
        :return: The result of a query either as a DataFrame or a pandas dataframe.
        :rtype: Union[DataFrame,pd.DataFrame]
        :raises SyntaxError: if the query string does not follow expected syntax.
        """
        is_valid = False
        for member in DataFrameType:
            if result_format == member.value:
                is_valid = True
        if not is_valid:
            raise Exception(
                f"Invalid format string: {result_format}. Valid format are one of the following:"
                + str([member.value for member in DataFrameType])
            )

        if query_string:
            query = self.parser.parse(query_string)

            res = self.runs.search(query)
        else:
            res = self.runs.all()
        res = [DataDict(r, parent_dir=_get_log_dir(r, self.src_dir)) for r in res]
        res = DataFrame(res)
        if result_format == DataFrameType.Pandas.value:
            return res.toPandas(lazy=False)
        if result_format == DataFrameType.DataFrame.value:
            return res

    @property
    def fields(self) -> pd.DataFrame:
        """Return all fields of the database except those specific to MLXP, excluding
        the fields contained in the file 'mlxp.yaml'.

        return: a dataframe of all fields contained in the database
        rtype: pd.DataFrame
        """
        fields_dict = {k: v for d in self._fields.all() for k, v in d.items() if not k.startswith("mlxp")}
        dataframe = pd.DataFrame(list(fields_dict.items()), columns=["Fields", "Type"])
        dataframe.set_index("Fields", inplace=True)
        dataframe = dataframe.sort_index()

        return dataframe

    @property
    def searchable(self) -> pd.DataFrame:
        """Return all fields of the database that are searchable, excluding the fields
        contained in the file 'mlxp.yaml'.

        return: a dataframe of all fields contained in the database that can be searched using the method filter
        rtype: pd.DataFrame
        """
        fields_dict = {k: v for d in self._fields.all() for k, v in d.items() if _is_searchable(k)}
        dataframe = pd.DataFrame(list(fields_dict.items()), columns=["Fields", "Type"])
        dataframe.set_index("Fields", inplace=True)
        dataframe = dataframe.sort_index()

        return dataframe

    def _create_base(self):
        self.database.drop_table("runs")
        self.database.drop_table("fields")
        all_fields = {}
        dir_nrs = [
            int(d)
            for d in os.listdir(self.src_dir)
            if os.path.isdir(os.path.join(self.src_dir, d)) and d.isdigit()
        ]
        files_not_found = []
        for file_id in dir_nrs:
            path = os.path.join(self.src_dir, str(file_id))
            try:
                data, fields = _get_data(path)
                self.runs.insert(Document(data, doc_id=file_id))
                all_fields.update(fields)
            except FileNotFoundError:
                files_not_found.append(path)

        for key, value in all_fields.items():
            self._fields.insert({key: value})

        if files_not_found:
            print("Warning: The following files were not found:")
            print(files_not_found)


def _get_metrics_dir(res_dict, src_dir):
    abs_metrics_dir = res_dict["info.logger.metrics_dir"]
    parent_log_dir = os.path.dirname(res_dict["info.logger.log_dir"])

    relpath = os.path.relpath(abs_metrics_dir, parent_log_dir)

    return os.path.join(src_dir, relpath)


def _get_log_dir(res_dict, src_dir):
    # abs_metrics_dir = r["info.logger.metrics_dir"]
    return os.path.join(src_dir, str(res_dict["info.logger.log_id"]))


def _get_data(path):
    data = {"config": {}, "info": {}}
    for key in data:
        fname = os.path.join(path, Directories.Metadata.value, key + ".yaml")
        with open(fname, "r") as file:
            data[key] = yaml.safe_load(file)

    metadata_dict = _flatten_dict(data, parent_key="")

    fields = {key: str(type(value)) for key, value in metadata_dict.items()}

    metrics_dict = _get_metrics_data(path)
    artifacts_dict = _get_artifacts_data(path)

    metadata_dict.update(metrics_dict)
    metadata_dict.update(artifacts_dict)
    fields.update(metrics_dict)
    fields.update({key: "Artifact" for key,values in artifacts_dict.items()})
    return metadata_dict, fields


def _get_metrics_data(path):
    keys_dir = os.path.join(path, Directories.Metrics.value, ".keys")

    lazydata_dict = {}
    try:
        for file_name in os.listdir(keys_dir):
            if file_name.endswith(".yaml"):
                prefix = os.path.splitext(file_name)[0]
                full_file_name = os.path.join(keys_dir, file_name)
                with open(full_file_name, "r") as file:
                    keys_dict = yaml.safe_load(file)
                if keys_dict:
                    lazydata_dict.update({prefix + "." + key: LAZYDATA for key in keys_dict.keys()})
    except FileNotFoundError:
        pass
    return lazydata_dict


def _get_artifacts_data(path):
    artifacts_dict_name = os.path.join(path, Directories.Artifacts.value, ".keys/artifacts.yaml")

    lazydata_dict = {}
    try:
        with open(artifacts_dict_name, "r") as file:
            keys_dict = yaml.safe_load(file)
        if keys_dict:
            for key, value in keys_dict.items():

                lazydata_dict.update(
                    {".".join(["artifact", key, path]): LAZYARTIFACT for path in value.keys()}
                )

    except FileNotFoundError:
        pass
    return lazydata_dict


def _ensure_writable(dst_dir):
    err_msg = "Please select a different destination directory."
    try:
        os.makedirs(dst_dir, exist_ok=True)
    except PermissionError:
        message = f"Unable to create the destination directory {dst_dir}.\n"
        raise PermissionError(message + err_msg)
    if not os.access(dst_dir, os.W_OK):
        message = f"Unable to write in the destination directory {dst_dir}.\n"
        raise PermissionError(message + err_msg)
    return dst_dir


def _flatten_dict(src_dict: MutableMapping, parent_key: str = "", sep: str = "."):
    return dict(_flatten_dict_gen(src_dict, parent_key, sep))


def _flatten_dict_gen(src_dict, parent_key, sep):
    for key, value in src_dict.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, MutableMapping):
            yield from _flatten_dict(value, new_key, sep=sep).items()
        else:
            yield new_key, value
