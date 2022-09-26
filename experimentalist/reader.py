# class for reading resuls of experiments

import os
import json
import yaml

from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb import Query
from tinydb.table import Document
import itertools

from experimentalist.collections import ConfigCollection, ConfigList


class Reader(object):
    def __init__(self, root, file_name="metadata", reload=True):
        self.root_dir = os.path.abspath(root)
        self.file_name = file_name
        self.db = get_db_file_manager_safe(self.root_dir, file_name=file_name)
        self.runs = self.db.table("runs")
        self.latest_id = 0
        if reload:
            self.constuct_base()

    def update_base(self):
        self.latest_id = 0
        dir_nrs = [
            int(d)
            for d in os.listdir(self.root_dir)
            if os.path.isdir(os.path.join(self.root_dir, d))
            and d.isdigit()
            and int(d) > self.latest_id
        ]
        for d in dir_nrs:
            try:
                self.add_to_base(d)
            except FileNotFoundError:
                self.handle_legacy(d)

    def add_to_base(self, file_id):
        with open(
            os.path.join(self.root_dir, str(file_id), self.file_name + ".yaml"), "r"
        ) as file:
            data = yaml.safe_load(file)
            self.runs.insert(Document(data, doc_id=file_id))

    def handle_legacy(self, file_id):
        file_name = os.path.join(self.root_dir, str(file_id), self.file_name)
        try:
            with open(file_name + ".json", "r") as file:
                data = json.load(file)
            with open(file_name + ".yaml", "w") as file:
                yaml.dump(data["runs"][str(file_id)], file, default_flow_style=False)
            self.add_to_base(file_id)
        except FileNotFoundError:
            pass

    def constuct_base(self):
        # get all dirs in root greater than latest_id in the db
        self.db.drop_table("runs")
        self.runs = self.db.table("runs")
        self.update_base()

    def search(self, queries_dict):
        """Wrapper to TinyDB's search function."""
        queries_dict = preprocess_queries_dict(queries_dict)
        res = []
        all_queries = query_generator(**queries_dict)
        for query_dict in all_queries:
            Q = make_query(query_dict)
            res += self.runs.search(Q)
        res = ConfigList(res, root_name=self.file_name)
        return ConfigCollection([res])

    def search_list(self, list_queries_dict, commun_queries=None):
        res = []
        for queries_dict in list_queries_dict:
            if commun_queries is not None:
                queries_dict = {**queries_dict, **commun_queries}
            res += self.search(queries_dict)
        return res


def preprocess_queries_dict(queries_dict, file_name="metadata"):
    return {".".join(key.split(".")[1:]): value for key, value in queries_dict.items()}


def make_query(query_dict):
    Q = None
    User = Query()
    for key, value in query_dict.items():
        keys = key.split(".")
        field = User[keys[0]]
        for k in keys[1:]:
            field = field[k]
        if Q is None:
            Q = field.one_of([value])
        else:
            Q &= field.one_of([value])

    return Q


def query_generator(**kwargs):
    keys = kwargs.keys()
    vals = kwargs.values()
    for instance in itertools.product(*vals):
        yield dict(zip(keys, instance))


def get_db_file_manager(root_dir, file_name="metadata"):
    file_name = file_name + ".json"
    return TinyDB(
        os.path.join(root_dir, file_name),
        storage=JSONStorage,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )


def get_db_file_manager_safe(root_dir, file_name="metadata"):
    try:
        return get_db_file_manager(root_dir, file_name)
    except PermissionError:
        # Handle case where there is no write privileges,
        # the database will be created in a subirectory of the working directory
        root, dir_name = os.path.split(root_dir)
        root_dir = os.path.join(os.getcwd(), dir_name)
        os.makedirs(root_dir, exist_ok=True)
        return get_db_file_manager(root_dir, file_name)
