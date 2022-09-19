# class for running experiments
import os
from datetime import datetime
import pprint
import socket

#from pytorch_pretrained_biggan import BigGAN
#from  models.generator import BigGANwrapper
from Experimentalist.logger import Logger
#from hydra import hydra_utils
import numpy as np
import random
import pickle as pkl

def set_seeds(seeds):
    keys = seeds.keys()
    if 'torch'in keys:
        import torch
        torch.manual_seed(seeds['torch']) 
    if 'numpy' in keys:
        np.random.seed(seeds['numpy'])
        random.seed(seeds['numpy'])

class Experimentalist(object):
    def __init__(self,config):
        # self.config = config
        # #self.git_store_commit()
        # self.timer = Timer()
        # #self.git_store_commit()

        # #self.device = assign_device(self.config.device)
        # print(f"Process id: {str(os.getpid())} | hostname: {socket.gethostname()}")
        # print(f"Time: {datetime.now()}")
        # self.pp = pprint.PrettyPrinter(indent=4)
        # self.pp.pprint(vars(config))

        # self.logger = Logger(self.config)
        # self.logger.log_config()
        # set_seeds(self.config.system.seed)
        # #os.chdir(hydra_utils.get_original_cwd()) # Not sure what this is for!
        self.config = config
        #self.git_store_commit()
        self.logger = Logger(self.config)
        set_seeds(self.config.system.seed)
        #os.chdir(hydra_utils.get_original_cwd()) # Not sure what this is for!


        
    # def display_msg(step, msg):
    #         self.timer(step, msg)

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

    def log_metrics(self,metrics_dict,tag='',step=None):
        self.logger.log_metrics(metrics_dict,tag,step)

    def log_artifacts(self,artifact, step, **kwargs):
        self.logger.log_artifacts(artifact, step, **kwargs)



