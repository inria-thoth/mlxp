# class for reading resuls of experiments

import os
import json
import yaml

from tinydb import TinyDB, where
from tinydb.storages import JSONStorage
from tinydb import Query
from tinydb.table import Document
import itertools

from experimentalist.collections import ConfigCollection, ConfigList
from operator import eq, ge, gt, le, lt, ne

class Reader(object):
    def __init__(self, root, file_name="metadata", reload=True):
        self.root_dir = os.path.abspath(root)
        self.file_name = file_name
        self.db = _get_db_file_manager(self.root_dir, file_name=file_name)
        self.runs = self.db.table("runs")
        self.latest_id = 0
        if reload:
            self.reload()

    def reload(self):
        # get all dirs in root greater than latest_id in the db
        self.db.drop_table("runs")
        self.runs = self.db.table("runs")
        self._construct_base() # constructing the database from the run directory

    #def search(self, filter="", output_format='pandas'):


    def _search(self, queries_dict):
        """Wrapper to TinyDB's search function."""
        res = []
        queries_dict = _preprocess_queries_dict(queries_dict)
        all_queries = _query_generator(**queries_dict)
        for query_dict in all_queries:
            Q = _make_query(query_dict)
            res += self.runs.search(Q)
        res = ConfigList(res, root_name=self.file_name)
        return ConfigCollection([res])

    def search(self, query_string):
        res = []
        or_querie_str_list = s.split('|')
        for or_query_str in or_querie_str_list:
            and_queries_str_list = or_query_str.split("&")
            and_queries = make_and_queries(and_queries_str_list)
            for query in and_queries:
                Q = _make_query(query)
                res += self.runs.search(Q)        
        res = ConfigList(res, root_name=self.file_name)
        return ConfigCollection([res])



    def _handle_legacy(self, file_id):
        file_name = os.path.join(self.root_dir, str(file_id), self.file_name)
        try:
            with open(file_name + ".json", "r") as file:
                data = json.load(file)
            with open(file_name + ".yaml", "w") as file:
                yaml.dump(data["runs"][str(file_id)], file, default_flow_style=False)
            self._add_to_base(file_id)
        except FileNotFoundError:
            pass

    def _add_to_base(self, file_id):
        with open(
            os.path.join(self.root_dir, str(file_id), self.file_name + ".yaml"), "r"
        ) as file:
            data = yaml.safe_load(file)
            self.runs.insert(Document(data, doc_id=file_id))


    def _construct_base(self):
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
                self._add_to_base(d)
            except FileNotFoundError:
                self._handle_legacy(d)




ops = {
    "==": eq,
    "!=": ne,
    "<=": le,
    ">=": ge,
    "<": lt,
    ">": gt,
}

def parse_query(s):
    all_queries = []
    and_queries = s.split('|')
    for and_query in and_queries:
        tokens = and_query.split("&")
        all_queries += make_or_queries(tokens)


def make_and_queries(tokens):
    tokens = map(str.strip, tokens)
    tokens = [token.split(" ", 3) for token in tokens]
    tokens_and = [token for token in tokens if token[1] == "!=" ]
    tokens_or  = [token for token in tokens if token[1] != "!=" ]
    or_queries = _product_queries(tokens_or)
    and_queries = _product_queries(tokens_and)
    and_queries =  [item for sublist in and_queries for item in sublist]
    or_queries = [ or_query + and_queries  for or_query in  or_queries ]
    return or_queries

def _product_queries(tokens):
    keys = [token[0] for token in tokens]
    vals = [_process_query_value(token[2]) for token in tokens]
    ops  = [token[1] for token in tokens]
    prod_queries = []
    for instance in itertools.product(*vals):
        prod_queries.append(
            [ {'key': key, 'op': op, 'value': val } 
                for key, op, val in zip(keys,ops,instance) ])

    return prod_queries

def _eval_str(v):      
    if isfloat(v):
        v = float(v)
    elif isint(v):
        v = int(v)
    return v


def _process_query_value(value):
    values = value.split(",")
    values = map(str.strip, values)
    return [_eval_str(v) for v in values]


def _build_field_struct(key):
    keys = k.split(".")
    field = Query()
    for k in keys[1:]:
        field = field[k]
    return field

def _make_query(query_list):
    for query in query_list:
        k, op, v = query['key'], query['op'], query['value']
        opf = ops.get(op, None)
        if opf is None:
            print("Unknown operator: {0:s}".format(op))
            return where(None)
        field = _build_field_struct(key)

        qs.append(opf(field, v))

    return reduce(lambda a, b: a & b, qs)

# def _make_query(query_dict):
#     Q = None
#     User = Query()
#     for key, value in query_dict.items():
#         keys = key.split(".")
#         field = User[keys[0]]
#         for k in keys[1:]:
#             field = field[k]
#         if Q is None:
#             Q = field.one_of([value])
#         else:
#             Q &= field.one_of([value])

#     return Q


def _query_generator(**kwargs):
    keys = kwargs.keys()
    vals = kwargs.values()
    for instance in itertools.product(*vals):
        yield dict(zip(keys, instance))


def _get_db_file_manager_unsafe(root_dir, file_name="metadata"):
    file_name = file_name + ".json"
    return TinyDB(
        os.path.join(root_dir, file_name),
        storage=JSONStorage,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )

def _get_db_file_manager(root_dir, file_name="metadata"):
    try:
        return _get_db_file_manager_unsafe(root_dir, file_name)
    except PermissionError:
        # Handle case where there is no write privileges,
        # the database will be created in a subirectory of the working directory
        root, dir_name = os.path.split(root_dir)
        root_dir = os.path.join(os.getcwd(), dir_name)
        os.makedirs(root_dir, exist_ok=True)
        return _get_db_file_manager_unsafe(root_dir, file_name)

def _preprocess_queries_dict(queries_dict):
    return {".".join(key.split(".")[1:]): value for key, value in queries_dict.items()}

