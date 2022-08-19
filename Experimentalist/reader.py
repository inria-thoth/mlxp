# class for reading resuls of experiments

import os
import json


from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinyrecord import transaction

from tinydb import Query
from tinydb.table import Document
import itertools

from Experimentalist.utils import ConfigsList, flatten_dict


class Reader(object):
    def __init__(self,root, file_name="metadata", reload=True):
        self.root_dir = os.path.abspath(root)
        self.file_name = file_name
        self.db = get_db_file_manager(self.root_dir, file_name=file_name)
        self.runs = self.db.table("runs")
        self.latest_id =  0
        if reload:
            self.constuct_base()
    def update_base(self):
        self.latest_id = 0
        dir_nrs = [
            int(d)
            for d in os.listdir(self.root_dir)
            if os.path.isdir(os.path.join(self.root_dir, d)) and d.isdigit() and int(d)>self.latest_id
        ]
        for d in dir_nrs:
            try:
                with open(os.path.join(self.root_dir,str(d),self.file_name+'.json')) as file:
                    data = json.load(file)
                    self.runs.insert(Document(data["runs"][str(d)], doc_id=d ) )
            except FileNotFoundError:
                pass

    def constuct_base(self):
        # get all dirs in root greater than latest_id in the db
        self.db.drop_table('runs')
        self.runs = self.db.table("runs")
        self.update_base()
    def search(self, queries_dict):
        """Wrapper to TinyDB's search function."""
        #query_dicts =  {'sampler/latent_sampler': ['lagevin'], 'model/d_model': ['sngan'] }]
        queries_dict = preprocess_queries_dict(queries_dict)
        res = []
        all_queries = query_generator(**queries_dict)
        for query_dict in all_queries:
            Q = make_query(query_dict)
            res += self.runs.search(Q)
        res = [{'hierarchical': r, 'flattened': flatten_dict(r,parent_key=self.file_name) } for r in res ]
        return ConfigsList(res)

    def search_list(self,list_queries_dict, commun_queries=None):
        res = []
        for queries_dict in list_queries_dict:
            if commun_queries is not None:
                queries_dict = {**queries_dict, **commun_queries}
            res += self.search(queries_dict)
        return res


def preprocess_queries_dict(queries_dict, file_name='metadata'):
    return { '.'.join(key.split('.')[1:]): value 
            for key, value in  queries_dict.items() }

def make_query(query_dict):
    Q = None
    User = Query()
    for key, value in query_dict.items():
        keys = key.split('.')
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
    file_name = file_name+'.json'
    try:
        db = TinyDB(os.path.join(root_dir, file_name), storage=JSONStorage,sort_keys=True, indent=4, separators=(',', ': '))
    except: 
        ### handle case where there is no write priviledges, the database will be created in a subirectory of the working directory
        root, dir_name = os.path.split(root_dir)
        root_dir = os.path.join(os.getcwd(),dir_name)
        os.makedirs(root_dir, exist_ok=True)
        db = TinyDB(os.path.join(root_dir, file_name), storage=JSONStorage,sort_keys=True, indent=4, separators=(',', ': '))
    return db





