# class for reading resuls of experiments

import os
import json
import yaml

from tinydb import TinyDB, where
from tinydb.storages import JSONStorage
from tinydb import Query
from tinydb.table import Document
import itertools

from experimentalist.collections import ConfigList, Config
from operator import eq, ge, gt, le, lt, ne
import functools

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


    def search(self, query_string="", output_format="configcollection"):
        if query_string:
            res = []
            or_querie_str_list = query_string.split('|')
            for or_query_str in or_querie_str_list:
                and_queries_str_list = or_query_str.split("&")
                query_list_unsafe = [token.split() for token in and_queries_str_list]
                query_list = [token for token in query_list_unsafe if len(token)==3]
                try:
                    assert len(query_list_unsafe)>0
                    assert len(query_list_unsafe) == len(query_list)
                except AssertionError:
                    raise SyntaxError(" The query string contains an error! Please check the syntax. ex: key == True")
                and_queries = make_and_queries(query_list)
                for query in and_queries:
                    if query:
                        Q = _make_query(query)
                        res += self.runs.search(Q)
        else:
            res = self.runs.all()
        res = [ Config(r,parent_key=self.file_name) for r in res ]
        #res = ConfigCollection([ConfigList(res)])
        res = ConfigList(res)
        config_diff = res.config_diff()
        if output_format=="pandas":
            res = res.toPandasDF()
        #elif output_format=="configcollection":
        return res, config_diff

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


def make_and_queries(tokens):
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

def isfloat(v):
    try:
        float(v)
        return True
    except:
        return False
def isint(v):
    try:
        int(v)
        return True
    except:
        return False    

def isbool(v):
    return v in ["True","False"]

def tobool(v):
    if v=="True":
        return True
    elif v=="False":
        return False
    else:
        raise ValueError
def _eval_str(v):
    if isint(v):
        v = int(v)
    elif isfloat(v):
        v = float(v)
    elif isbool(v):
        v = tobool(v)
    return v


def _process_query_value(value):
    values = value.split(",")
    values = map(str.strip, values)
    return [_eval_str(v) for v in values]


def _build_field_struct(key):
    keys = key.split(".")
    field = Query()
    for k in keys[1:]:
        field = field[k]
    return field

def _make_query(query_list):
    qs = []
    for query in query_list:
        k, op, v = query['key'], query['op'], query['value']
        opf = ops.get(op, None)
        if opf is None:
            print("Unknown operator: {0:s}".format(op))
            return where(None)
        field = _build_field_struct(k)

        qs.append(opf(field, v))

    return functools.reduce(lambda a, b: a & b, qs)

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

