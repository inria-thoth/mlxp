import numpy as np

import csv
import sys
import os
import time
from datetime import datetime
import pprint
import socket
import json
import pickle as pkl

import timeit

from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinyrecord import transaction

#from pytorch_pretrained_biggan import BigGAN
#from  models.generator import BigGANwrapper
from utils import timer
import omegaconf
from hydra import utils
from tinydb import Query
from sqlalchemy import create_engine
import sqlalchemy as sa

import pandas as pd

def config_to_dict(config):
    done = False
    out_dict = {}
    for key, value in config.items():
        if isinstance(value,omegaconf.dictconfig.DictConfig):
            out_dict[key] =  config_to_dict(value)
        else:
            out_dict[key] = value
    return out_dict



def set_seeds(seeds):
    keys = seeds.keys()
    if 'torch'in keys:
        import torch
        torch.manual_seed(seeds['torch']) 
    if 'numpy' in keys:
        np.random.seed(seeds['numpy'])

class Experiment(object):
    def __init__(self,config):
        self.config = config
        #self.git_store_commit()
        set_seeds(self.config.system.seed)
        #self.device = assign_device(self.config.device)

        print(f"Process id: {str(os.getpid())} | hostname: {socket.gethostname()}")
        print(f"Time: {datetime.now()}")
        self.pp = pprint.PrettyPrinter(indent=4)
        self.pp.pprint(vars(config))

        self.saver = Saver(self.config.logs.log_dir)
        self.saver.save_config(self.config)
        self.samples_dir = self.saver.samples_dir

        os.chdir(utils.get_original_cwd())

    def git_check_commit(self):

        raise NotImplementedError
        # Checks if all modifs are commited throw error otherwise or make an actuall commit on a dedicated branch

    def git_get_commit(self):

        raise NotImplementedError
        # returns the current commit

    def git_store_commit(self):
        
        # stores the commit name to the config file after ensuring all modifs are commited

        self.git_check_commit()
        self.config.system.git.commit = self.git_get_commit()

    def save_checkpoint(self,state_dict, epoch, tag, best=False, model_type='torch'):
        self.saver.save_checkpoint(state_dict, epoch, tag, best=best, model_type=model_type)


    def save_data(self,metrics_dict, arrays_dict = None ,index=0):
        self.saver.save_data( metrics_dict, arrays_dict = arrays_dict ,index=index )

def get_db_file_manager(root_dir):

    #fs = HashFS(os.path.join(root_dir, "hashfs"), depth=3, width=2, algorithm="md5")
    db = TinyDB(os.path.join(root_dir, "metadata.json"), storage=JSONStorage,sort_keys=True, indent=4, separators=(',', ': '))
    return db
class Saver(object):
    def __init__(self, root = "./runs_db", overwrite=None):
        #from .tinydb_hashfs_bases import get_db_file_manager
        root_dir = os.path.abspath(root)
        os.makedirs(root_dir, exist_ok=True)
        #db = get_db_file_manager(root_dir)
        #self.db = db
        #self.runs = db.table("runs")
        self.overwrite = overwrite
        self.run_entry = {}
        self.db_run_id = None
        self.root = root_dir
        
        self.samples_dir = None
        self.checkpoint_dir = None
        self.arrays_dir = None


    def _make_run_dir(self, _id):
        os.makedirs(self.root, exist_ok=True)
        self.dir = None
        if _id is None:
            fail_count = 0
            _id = self._maximum_existing_run_id() + 1
            while self.dir is None:
                try:
                    self._make_dir(_id)
                except FileExistsError:  # Catch race conditions
                    if fail_count < 1000:
                        fail_count += 1
                        _id += 1
                    else:  # expect that something else went wrong
                        raise
        else:
            self.dir = os.path.join(self.root, str(_id))
            os.mkdir(self.dir)
        return _id
    def _maximum_existing_run_id(self):
        dir_nrs = [
            int(d)
            for d in os.listdir(self.root)
            if os.path.isdir(os.path.join(self.root, d)) and d.isdigit()
        ]
        if dir_nrs:
            return max(dir_nrs)
        else:
            return 0

    def _make_dir(self, _id):
        new_dir = os.path.join(self.root, str(_id))
        os.mkdir(new_dir)
        self.dir = new_dir  # set only if mkdir is successful
    def save_config(self,config):
        # config contains only experiment parameters
        # host_info:  slurm id, hostname, gpu , etc
        # meta : run_id, starting time, slum id

        self.db_run_id = None
        self.db_run_id = self._make_run_dir(self.db_run_id)
        self.get_host_config(config)
        self.run_entry = config
        self.run_entry.logs.log_id = self.db_run_id
        with TinyDB(os.path.join(self.root, str(self.db_run_id), "metadata.json"), storage=JSONStorage) as db: 
            runs = db.table("runs")
            runs.insert(config_to_dict(self.run_entry))
        self.make_dirs()
        self.log_file(config.logs.log_to_file)
    def save_data(self,metrics_dict, arrays_dict = None ,index=0):
        if arrays_dict is not None:
            fname = os.path.join(self.root, str(self.db_run_id), 'arrays', f'arrays_{str(index).zfill(3)}')
            np.savez(fname, **arrays_dict)
            metrics_dict['index'] = index
            metrics_dict['path_arrays'] = fname
        file_name = os.path.join(self.root, str(self.db_run_id), f'metrics')
        with open(file_name+'.json','a') as f:
            json.dump(metrics_dict,f)
            f.write(os.linesep)
    def save_checkpoint(self, state_dict, epoch, tag, best=False, model_type='torch'):
            path = os.path.join(self.root, str(self.db_run_id), 'checkpoints', tag+'_'+str({epoch})+'.pth')
            if model=='torch':
                torch.save(state_dict, path)
                print(f'Saved model parameters to {path}')

    def log_file(self,log_to_file):
        if log_to_file:
            log_file = open(os.path.join(self.root,str(self.db_run_id), f'log.txt'), 'w', buffering=1)
            sys.stdout = log_file
            sys.stderr = log_file
    def get_host_config(self,config):
        config.system.hostname = socket.gethostname()
        config.system.process_id = os.getpid()

    def make_dirs(self):
        os.makedirs(self.root, exist_ok=True)
        self.arrays_dir = os.path.join(self.root, str(self.db_run_id), 'arrays')
        os.makedirs(self.arrays_dir, exist_ok=True)
        self.checkpoint_dir = os.path.join(self.root, str(self.db_run_id), 'checkpoints')
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.samples_dir = os.path.join(self.root, str(self.db_run_id), 'samples')
        os.makedirs(self.samples_dir, exist_ok=True)



class Reader(object):
    def __init__(self,root):
        self.root_dir = os.path.abspath(root)
        self.db = get_db_file_manager(self.root_dir)
        self.runs = db.table("runs")

    def search_from_query_dict(self, query_dict):
        """Wrapper to TinyDB's search function."""
        #query_dicts =  {'sampler/latent_sampler': ['lagevin'], 'model/d_model': ['sngan'] }]
        User = Query()
        Q = None

        for key, value in query_dict.items():
            keys = key.split('/')
            field = User[keys[0]]
            for k in keys[1:]:
                field = field[k]
            if Q is None:
                Q = field.one_of(value)
            else:
                Q &= field.one_of(value)
        return self.runs.search(Q)

    def search_from_union_query_dict(self,query_dicts, commun_queries=None):
        res = []
        for query_dict in query_dicts:
            if commun_queries is not None:
                query_dict = {**query_dict, **commun_queries}
                res += self.search_dict_query(query_dict)
        return res


    def apply_func_to_array(self,runs, results):
        keys
        out_dict = {}

        return  [ os.path.join(self.root_dir, str(run['_id'])) for run in runs ] 


