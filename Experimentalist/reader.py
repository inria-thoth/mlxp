# class for reading resuls of experiments

import os
import json


from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinyrecord import transaction

from tinydb import Query
from tinydb.table import Document
import itertools

class Reader(object):
    def __init__(self,root):
        self.root_dir = os.path.abspath(root)
        self.db = get_db_file_manager(self.root_dir)
        self.runs = self.db.table("runs")
        self.latest_id =  0#get_lates_id(self.runs)
    def update_base(self):
        self.latest_id = 0#get_lates_id(self.runs)
        dir_nrs = [
            int(d)
            for d in os.listdir(self.root_dir)
            if os.path.isdir(os.path.join(self.root_dir, d)) and d.isdigit() and int(d)>self.latest_id
        ]
        for d in dir_nrs:
            try:
                with open(os.path.join(self.root_dir,str(d),"metadata.json")) as file:
                    data = json.load(file)
                    #try:
                    self.runs.insert(Document(data["runs"][str(d)], doc_id=d ) )
                    #except:
                    #    pass
                    #except AssertionError:
                    #    self.runs.update(Document(data, doc_id=d ) )
            except FileNotFoundError:
                pass

    def constuct_base(self):
        # get all dirs in root greater than latest_id in the db
        self.db.drop_table('runs')
        self.runs = self.db.table("runs")
        self.latest_id =  0
        self.update_base()
    def search(self, queries_dict,operation=lambda x:x):
        """Wrapper to TinyDB's search function."""
        #query_dicts =  {'sampler/latent_sampler': ['lagevin'], 'model/d_model': ['sngan'] }]
        res = []
        all_queries = query_generator(**queries_dict)
        def default_operation(config_dict): 
            if config_dict:
                for p in config_dict:
                    p['logs']['path'] = os.path.join(self.root_dir,str(p['logs']['log_id']),'metrics.json')
            return config_dict
        for query_dict in all_queries:
            Q = make_query(query_dict)
            res += operation(default_operation(self.runs.search(Q)))
        return res

    def search_list(self,list_queries_dict, commun_queries=None):
        res = []
        for queries_dict in list_queries_dict:
            if commun_queries is not None:
                queries_dict = {**queries_dict, **commun_queries}
            res += self.search(queries_dict)
        return res

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


def get_db_file_manager(root_dir):
    db = TinyDB(os.path.join(root_dir, "metadata.json"), storage=JSONStorage,sort_keys=True, indent=4, separators=(',', ': '))
    return db





