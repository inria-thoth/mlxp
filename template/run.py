# script for submitting jobs to cluster
from __future__ import print_function

import scipy.stats._qmc

import os
import logging
import hydra
import omegaconf
import argparse
import yaml
import torch
import os
import numpy as np
import random
 
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, ListConfig, OmegaConf
from Experimentalist.launcher_2 import _launch
from Experimentalist.structured_config import register_configs, add_exp_cfg
from Experimentalist.launcher import create

from searcher import Trainer

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
import functools
from typing import Any, Callable, List, Optional

work_dir = os.getcwd()

def reproducibility(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def save_config(cfg, path):
    from ruamel import yaml
    from Experimentalist.logger import config_to_dict
    cfg_dict = config_to_dict(cfg)
    string = yaml.dump(cfg_dict, Dumper=yaml.RoundTripDumper)
    with open(path,'a') as f:
        f.write(string)

# def _launch(task_function):
#     #@functools.wraps
#     def decorated_task(cfg):
#         if not cfg.system.isBatchJob:
#             return task_function(cfg)            
#         cfg.system.isBatchJob=False
#         cfg.system.cmd=os.path.abspath(__file__)
#         try:
#             create(cfg)
#         except Exception as e:
#             print('No job launched')
#             logger.critical(e, exc_info=True)
       
#     return decorated_task


# def multiple_decorators(func):
#     #@functools.wraps
#     src = os.getcwd()
#     config_name = 'config.yaml' #os.path.join(src,'configs','config.yaml')
#     config_path = os.path.join(src,'configs')

    
#     return hydra.main(config_name=config_name,config_path=config_path)(_launch(func))


def launch(task_function):
    #@functools.wraps
    #register_configs()
    def decorated_task(cfg):
        #add_exp_cfg(cfg)
        cfg = add_exp_cfg(cfg)
        if cfg.cluster.engine not in ["OAR","SLURM"]:
            cfg.system.isBatchJob=False
        if not cfg.system.isBatchJob:
            return task_function(cfg)            
        cfg.system.isBatchJob=False
        cfg.system.cmd=os.path.abspath(__file__)
        _launch(cfg)
        # try:
        #     create(cfg)
        # except Exception as e:
        #     print('No job launched')
            #logger.critical(e, exc_info=True)
       
    return decorated_task


@hydra.main(config_name='config_2.yaml',config_path='./configs' )
#@launch
@launch
def main(cfg: DictConfig) -> None:
    # logger.info(f"Current working directory: {os.getcwd()}")
    # try:
    #     create(cfg)
    # except Exception as e:
    #     print('No job launched')
    #     logger.critical(e, exc_info=True)

    Config_singleton = False
    os.chdir(work_dir)
     
    trainer = Trainer(cfg)
    cfg.logs.log_id = trainer.args.logs.log_id
    log_path = trainer.get_log_path()
    transfer_config_path = os.path.join(log_path,'transfer_config.yaml')
    if 'escaper' in cfg.transfer:
        omegaconf.OmegaConf.set_struct(cfg.transfer, True)
        with omegaconf.open_dict(cfg.transfer):
            cfg.transfer.escaper.model = cfg.loss.outer.model
        if cfg.transfer.escaper.operation_type =='PIL':
            op_name = cfg.transfer.escaper.model.operations.name.split('.')[-1]
            cfg.transfer.escaper.model.operations.name='core.operation.'+op_name
    save_config(cfg.transfer,transfer_config_path)

    if not os.path.exists(os.path.join(log_path,'search_models.ckpt')):
        path = os.path.join(trainer.get_log_path(),'ckpt','pre-train_models.pth')
        try:
            if os.path.exists(cfg.inner_init):
                path = cfg.inner_init
        except:
            pass                      
        if not os.path.exists(path):

            ### pre-training model
            print("Starting pre-training")
            trainer.mode='pre-train'
            trainer.init()
            resume= None
            ckpt_path= os.path.join(cfg.logs.path, 'ckpt')
            os.makedirs(ckpt_path, exist_ok=True)
            tag = os.path.join(ckpt_path,trainer.tag+'models')        
            save= tag+'.pth'
            path = os.getcwd()
            os.chdir(os.path.join(path,'ESCAPER_evaluate'))
            result,Config_singleton = run_from_py(transfer_config_path,cfg.transfer,save=save, resume=resume, tag=tag,
                                    cv_ratio=cfg.data.split,cv=cfg.data.cv)
            os.chdir(path)
            trainer.log_metrics(result,tag=trainer.tag)
            
            # reproducibility(0)
            # trainer.mode='pre-train'
            # trainer.main()
            # trainer=Trainer(cfg)
            # print("Finished pre-training")
        if cfg.mode in ['search','train']:
            print("Starting search")
            ### searching augmentations
            reproducibility(0)
            trainer.mode='search'
            trainer.main()
            #cfg.logs.log_name = cfg.logs.log_name+'/'+cfg.logs.log_id
            #trainer=Trainer(cfg)
            print("Finished search")

    if cfg.mode=='train':
        print("Starting finetuning")
        ### fine-tuning
        trainer.mode='train'
        trainer.init()
        resume= os.path.join(cfg.logs.path,'search_')
        ckpt_path= os.path.join(cfg.logs.path, 'ckpt')
        os.makedirs(ckpt_path, exist_ok=True)
        tag = os.path.join(ckpt_path,trainer.tag+'models')        
        save= tag+'.pth'
        path = os.getcwd()
        os.chdir(os.path.join(path,'ESCAPER_evaluate'))
        result,_ = run_from_py(transfer_config_path,cfg.transfer,save=save, resume=resume, tag=tag,cv_ratio=0.,cv=0,Config_singleton=Config_singleton)
        os.chdir(path)
        trainer.log_metrics(result,tag=trainer.tag)
        print("Finished finetuning")

if __name__ == "__main__":
    main()























