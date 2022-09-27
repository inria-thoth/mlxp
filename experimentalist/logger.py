# class for logging experiments


import sys
import os
import socket
import json
import yaml
import omegaconf
from datetime import datetime
from random import random
from time import sleep
import dill as pkl
import shutil
import pprint


class Logger(object):
    def __init__(self, config, overwrite=None):

        #print(f"Process id: {str(os.getpid())} | hostname: {socket.gethostname()}")
        #print(f"Time: {datetime.now()}")

        self.config = config
        if config.logs.log_id is None:
            log_dir = os.path.abspath(os.path.join(self.config.logs.root_dir,self.config.logs.log_dir))
        else:
            log_dir = self.config.logs.log_dir
        self.root = os.path.join(
            log_dir, self.config.logs.log_name
        )
        self.db_run_id = config.logs.log_id
        self.setup_dir()
        self.update_run_config(log_dir)
        self.log_file()

    def get_log_dir(self):
        return self.db_run_id, self.dir

    def setup_dir(self):
        os.makedirs(self.root, exist_ok=True)
        self.db_run_id, self.dir = _make_run_dir(self.db_run_id, self.root)

    def update_run_config(self,log_dir):
        now = datetime.now()
        date = now.strftime("%d/%m/%Y")
        time = now.strftime("%H:%M:%S")
        omegaconf.OmegaConf.set_struct(self.config, True)
        with omegaconf.open_dict(self.config):
            self.config.system.hostname = socket.gethostname()
            self.config.system.process_id = os.getpid()
            self.config.logs.log_id = self.db_run_id
            self.config.logs.path = os.path.join(self.root, str(self.db_run_id))
            self.config.system.date = date
            self.config.system.time = time
            self.config.system.status = "STARTING"
            self.config.logs.log_dir= log_dir
        omegaconf.OmegaConf.set_struct(self.config, False)

    def log_config(self):
        abs_name = os.path.join(self.dir, "metadata")
        omegaconf.OmegaConf.save(config=self.config, f=abs_name + ".yaml")

    def log_status(self, status):
        if status in ["COMPLETE", "RUNNING", "FAILED"]:
            omegaconf.OmegaConf.set_struct(self.config, True)
            with omegaconf.open_dict(self.config):
                self.config.system.status = status
            omegaconf.OmegaConf.set_struct(self.config, False)
            self.log_config()
        else:
            raise NotImplementedError

        # file_name = os.path.join(self.dir, f'status.txt')
        # with open(file_name,'w') as f:
        #     if status in ['COMPLETE','RUNNING','FAILED']:
        #         f.write(status)
        #     else:
        #         raise NotImplementedError

    def set_cluster_job_id(self):
        abs_name = os.path.join(self.dir, "metadata.yaml")
        if os.path.isfile(abs_name):
            with open(abs_name, "r") as file:
                configs = yaml.safe_load(file)
                if "cluster_job_id" in configs["system"]:
                    omegaconf.OmegaConf.set_struct(self.config, True)
                    with omegaconf.open_dict(self.config):
                        self.config.system.cluster_job_id = configs["system"][
                            "cluster_job_id"
                        ]
                    omegaconf.OmegaConf.set_struct(self.config, False)

    def log_metrics(self, metrics_dict, tag="", step=None):
        # mlflow.log_metics(metrics_dict, step=step)
        file_name = os.path.join(self.dir, tag + "metrics")
        with open(file_name + ".json", "a") as f:
            json.dump(metrics_dict, f)
            f.write(os.linesep)

    def log_artifacts(self, artifact, step, art_type, tag="", copy=False, copy_tag=""):
        subdir = os.path.join(self.dir, art_type)
        os.makedirs(subdir, exist_ok=True)
        fname = os.path.join(subdir, f"{tag}_{str(step)}")
        if art_type == "arrays":
            import numpy as np

            np.savez(fname, **artifact)
        elif art_type == "figures":
            artifact.savefig(f"{fname}.png", bbox_inches="tight")
        elif art_type == "torch_models":
            import torch

            torch.save(artifact, f"{fname}.pth")
            print("Model saved at " + fname + ".pth")
        elif art_type == "checkpoints":
            with open(f"{fname}.pkl", "wb") as f:
                pkl.dump(artifact, f)
            if copy:
                copy_fname = os.path.join(subdir, f"{copy_tag}_{str(step)}")
                shutil.copy(f"{fname}.pkl", f"{copy_fname}.pkl")

    def log_file(self):
        if self.config.logs.log_to_file:
            log_file = open(os.path.join(self.dir, "log.txt"), "w", buffering=1)
            sys.stdout = log_file
            sys.stderr = log_file


def config_to_dict(config):
    out_dict = {}
    for key, value in config.items():
        if isinstance(value, omegaconf.dictconfig.DictConfig):
            out_dict[key] = config_to_dict(value)
        else:
            out_dict[key] = value
    return out_dict


def _make_run_dir(_id, root):
    os.makedirs(root, exist_ok=True)
    log_dir = None
    if _id is None:
        fail_count = 0
        # _id = self._maximum_existing_run_id() + 1
        while log_dir is None:
            try:
                _id = _maximum_existing_run_id(root) + 1
                log_dir = _make_dir(_id, root)
            except FileExistsError:  # Catch race conditions
                sleep(random())
                if fail_count < 1000:
                    fail_count += 1
                else:  # expect that something else went wrong
                    raise
    else:
        log_dir = os.path.join(root, str(_id))
        os.makedirs(root, exist_ok=True)
    return _id, log_dir


def _maximum_existing_run_id(root):
    dir_nrs = [
        int(d)
        for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d)) and d.isdigit()
    ]
    if dir_nrs:
        return max(dir_nrs)
    else:
        return 0


def _make_dir(_id, root):
    log_dir = os.path.join(root, str(_id))
    os.mkdir(log_dir)
    return log_dir  # set only if mkdir is successful


def _log_config(cfg, file_name, path):
    # config contains only experiment parameters
    # host_info:  slurm id, hostname, gpu , etc
    # meta : run_id, starting time, slum id
    abs_name = os.path.join(path, file_name)
    omegaconf.OmegaConf.save(config=cfg, f=abs_name + ".yaml")


def set_date_time(config_dict):
    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")
    if config_dict["system"]["date"] == "" or config_dict["system"]["time"] == "":
        config_dict["system"]["date"] = date
        config_dict["system"]["time"] = time
