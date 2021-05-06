# class for logging experiments


import numpy as np
import sys
import os
import socket
import json
from tinydb import TinyDB
from tinydb.storages import JSONStorage
import omegaconf
from tinydb.table import Document
import torch
from datetime import datetime


class Logger(object):
    def __init__(self, config, overwrite=None):
        self.config = config
        self.root = os.path.join(os.path.abspath(self.config.logs.log_dir), self.config.logs.log_name)
        self.db_run_id = None

        self.setup_dir()
        self.update_run_config()
        self.log_file()

    def setup_dir(self):
        os.makedirs(self.root, exist_ok=True)
        self.db_run_id = self._make_run_dir(self.db_run_id)
        #mlflow.set_tracking_uri("file:/"+self.root )

    def update_run_config(self):
        self.config.system.hostname = socket.gethostname()
        self.config.system.process_id = os.getpid()
        self.config.logs.log_id = self.db_run_id

    def log_config(self):
        # config contains only experiment parameters
        # host_info:  slurm id, hostname, gpu , etc
        # meta : run_id, starting time, slum id
        config_dict = config_to_dict(self.config)
        config_dict = set_date_time(config_dict)


        with TinyDB(os.path.join(self.root, str(self.db_run_id), "metadata.json"), storage=JSONStorage) as db: 
            runs = db.table("runs")
            runs.insert(Document(config_dict, doc_id=self.db_run_id ) )
        #for key, value in config_dict.items():
        #    mlflow.log_param(key, value)

    def log_metrics(self,metrics_dict, step=None):
        #mlflow.log_metics(metrics_dict, step=step)
        file_name = os.path.join(self.root, str(self.db_run_id), f'metrics')
        with open(file_name+'.json','a') as f:
            json.dump(metrics_dict,f)
            f.write(os.linesep)

    def log_artifacts(self,artifact, step, art_type, tag=''):
        subdir= os.path.join(self.root, str(self.db_run_id), art_type)
        os.makedirs(subdir, exist_ok=True)
        fname = os.path.join(subdir, f'{tag}_{str(step).zfill(3)}')
        if art_type=='arrays':
            np.savez(fname, **artifact)
        elif art_type=='figures':
            artifact.savefig(f'{fname}.png',bbox_inches='tight')
        elif art_type=='torch_models':
            torch.save(artifact, f'{fname}.pth')

    def log_file(self):
        if self.config.logs.log_to_file:
            log_file = open(os.path.join(self.root,str(self.db_run_id), f'log.txt'), 'w', buffering=1)
            sys.stdout = log_file
            sys.stderr = log_file
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

def set_date_time(config_dict):
    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")
    if config_dict['system']['date']=='' or config_dict['system']['time']=='':
        config_dict['system']['date'] = date
        config_dict['system']['time'] = time

    return config_dict
def config_to_dict(config):
    done = False
    out_dict = {}
    for key, value in config.items():
        if isinstance(value,omegaconf.dictconfig.DictConfig):
            out_dict[key] =  config_to_dict(value)
        else:
            out_dict[key] = value
    return out_dict
