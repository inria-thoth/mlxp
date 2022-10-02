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
from dataclasses import dataclass
from typing import Any, Type
import abc

@dataclass
class Artifact(abc.ABC):
    """An abstract base class for any types of artifacts.
 
    Attributes
    ----------
    obj: 'Any'
        The structure to be saved
    ext: 'str'
        The extension under which the object obj is saved

    Methods
    -------
    save(fname: 'str')
        Saves the object into a file named fname.

    Notes
    -----
    This class allows to deal with different objects structures such as
    numpy arrays, torch tensors, checkpoints, etc. 
    Instances of this class are meant to be used as inputs 
    to the method log_artifact of the class Logger.
    New classes inheriting from this abstract class 
    can be created by the user depending on the need.
    """
    obj: Any
    ext: str
    
    @abc.abstractmethod
    def save(self, fname):
        """Saves the attribute obj into a file named fname.

        Parameters
        ----------
        fname: `str`
            The name of the file where the object must be saved.
        """
        pass

@dataclass
class NumpyArray(Artifact):
    """An subclass of Artifact for saving dictionaries of numpy arrays.
    """
    ext= ".npz"
    def save(self, fname):
        import numpy as np
        np.savez(fname, **self.obj)
@dataclass
class PNGImage(Artifact):
    """An subclass of Artifact for saving a instance of matplotlib.figure.Figure.
    """
    ext= ".png"
    def save(self, fname):
        import matplotlib
        assert isinstance(self.obj, matplotlib.figure.Figure)
        self.obj.savefig(f"{fname}{self.ext}", bbox_inches="tight")
@dataclass
class TorchModel(Artifact):
    """An subclass of Artifact for saving pytorch objects: Tensor, Module, or 
    a dictionary containing the whole state of a module. 
    """
    ext= ".pth"
    def save(self, fname):
        import torch
        torch.save(self.obj, f"{fname}{self.ext}")
@dataclass
class Checkpoint(Artifact):
    """An subclass of Artifact for saving any python object that is serializable. 
    """
    ext= ".pkl"
    def save(self, fname):
        with open(f"{fname}{self.ext}", "wb") as f:
                    pkl.dump(self.obj, f)


class Logger(object):
    """ Logger.

    Attributes
    ----------
    config: 'ConfigDict'
        A structure containing the configuration parameters for a run
    root: 'str'
        The path to the main directory containing 
        all the directories corresponding to different runs.
        root is constructed from the config: root = root_dir/log_dir/log_name
        where root_dir, log_dir and log_name are contained in config.logs
    run_id: 'int'
        The unique index of a run in a directory of runs. 
        It is used to construct the directory of the run 
        of the form: /path/to/run/run_id
        By default, it is set to None and is 
        assigned a integer value at runtime. 
        When initialized with a integer, 
        the corresponding root directory, if it exists, is used 
        It starts from 1 and is incremented for each new run
    run_dir: 'str'
        The path to the output of a particular run.
        dir is of the form: root/run_id

    Methods
    -------
    log_config(file_name: 'str'='metadata')
        Saves the config attribute corresponding to the current run  
        into a yaml file self._run_dir/file_name+'.yaml'. 
        Default: file_name='metadata'.
    log_metric(metric_dict: 'dict', file_name: 'str'="metrics")
        Saves a dictionary of scalars to a file named 
        file_name+'.json' in the directory self._run_dir. 
        Default: file_name='metrics'.
    log_artifact(artifact: 'Artifact', file_name: 'str')
        Saves an instance of a class (ex: NumpyArray) 
        inheriting from the class Artifact into a destination file:
        'artifacts_dir/file_name', where artifacts_dir is the directory 
        corresponding to the class of the instance (ex: NumpyArray) for a given run.   
    copy_artifact(file_name: 'str', dst_name: 'str', artifact_class: 'Type[Artifact]')
        Copies an artifact of type artifact_class  stored in 'artifacts_dir/name' 
        to a destination file 'artifacts_dir/dst_name', where artifacts_dir is the directory 
        where artifacts of the class 'artifact_class' are saved for a given run.
    """
    def __init__(self, config, overwrite=None):
        self._config = config
        log_dir = os.path.abspath(
            os.path.join(self._config.logs.root_dir, self._config.logs.log_dir)
        )
        self._root = os.path.join(log_dir, self._config.logs.log_name)
        self._run_id, self._run_dir = _make_run_dir(config.logs.log_id, 
                                                    self._root)
        
        self._update_config()
        if self._config.logs.log_to_file:
            log_file = open(os.path.join(self._run_dir, "log.txt"), "w", buffering=1)
            sys.stdout = log_file
            sys.stderr = log_file

    @property
    def config(self):
        """Returns the config. Allows the config to be immutable.
        """
        return self._config

    @property
    def root(self):
        """Returns the root directory. Allows the root to be immutable.
        """
        return self._root

    @property
    def run_id(self):
        """Returns the run_id. Allows the run_id to be immutable.
        """
        return self._run_id

    @property
    def run_dir(self):
        """Returns the run_dir. Allows the run_dir to be immutable.
        """
        return self._run_dir


    def log_config(self, file_name="metadata"):
        """Saves the config attribute corresponding to the current run  
        into a yaml file self._run_dir/file_name+'.yaml'. 
        Default: file_name='metadata'.

        Parameters
        ----------
        file_name: `str`
            name of the file
        """

        abs_name = os.path.join(self._run_dir, file_name)
        omegaconf.OmegaConf.save(config=self._config, f=abs_name + ".yaml")


    def log_metric(self, metric_dict, file_name="metrics"):
        """Saves a dictionary of scalars to a json file named 
        file_name+'.json' in the directory self._run_dir. 
        Default: file_name='metrics'.

        Parameters
        ----------
        metric_dict: 'dict'
            Dictonary of scalars.
        file_name: `str`
            name of the file
        """

        file_name = os.path.join(self._run_dir, file_name)
        with open(file_name + ".json", "a") as f:
            json.dump(metric_dict, f)
            f.write(os.linesep)

    def log_artifact(self, artifact, file_name):
        """Saves the attribute obj of an instance inheriting from the abstract class Artifact 
        into a destination file: 'self._run_dir/artifact_class_name/file_name'. 
        The directory 'artifact_class_name' is named after 
        the child class inheriting from Artifact.   

        Parameters
        ----------
        artifact: 'Artifact'
            An instance of a class inheriting from the abstract class Artifact.
        file_name: `str`
            name of the file where the artifact is saved.
        
        Raises
        ------
        `Assertionerror`
            Raised if artifact is not an instance of Artifact.
        """

        assert isinstance(artifact,Artifact)
        subdir = os.path.join(self._run_dir, type(artifact).__name__)
        os.makedirs(subdir, exist_ok=True)
        fname = os.path.join(subdir, file_name)
        artifact.save(fname)

    def copy_artifact(self, file_name , dst_name, artifact_class):
        """Copies an already existing artifact obj 
        from a source file: self._run_dir/artifact_class_name/file_name 
        to a destination file self._run_dir/artifact_class_name/file_name, 
        where artifact_class_name is the name of the class artifact_class.  
        
        Notes
        -----
        The source file name needs to have the same extension
        as the attribute ext of the class artifact_class.


        Parameters
        ----------
        file_name: `str`
            name of the source file to be copied.
        dst_name: `str`
            name of the destination file of the copy.
        artifact_class: 'Type[Artifact]'
            A class inheriting from the abstract class Artifact.

        Raises
        ------
        `FileNotFoundError`
            Raised if the source file is not found.
        """

        assert issubclass(artifact_class, Artifact)
        ckpt_dir_name = artifact_class.__name__
        ext = getattr(artifact_class, 'ext')
        subdir = os.path.join(self._run_dir, ckpt_dir_name)
        fname = os.path.join(subdir, file_name)
        copy_fname = os.path.join(subdir, dst_name)
        try:
            shutil.copy(f"{fname}{ext}", f"{copy_fname}{ext}")
        except FileNotFoundError as e:
            raise FileNotFoundError

    def _log_status(self, status):
        """
        log_status(status: 'str')
            Saves the status of the run into the 'metadata.yaml' file
            There are 4 admissible values: ["STARTING","COMPLETE", "RUNNING", "FAILED"]
            Throws an error if a non-admissible value is passed.
            This function is only used internally
        """
        if status in ["COMPLETE", "RUNNING", "FAILED"]:
            omegaconf.OmegaConf.set_struct(self._config, True)
            with omegaconf.open_dict(self._config):
                self._config.system.status = status
            omegaconf.OmegaConf.set_struct(self._config, False)
            self.log_config()
        else:
            raise NotImplementedError

    def _update_config(self):
        now = datetime.now()
        date = now.strftime("%d/%m/%Y")
        time = now.strftime("%H:%M:%S")
        omegaconf.OmegaConf.set_struct(self._config, True)
        with omegaconf.open_dict(self._config):
            self._config.system.hostname = socket.gethostname()
            self._config.system.process_id = os.getpid()
            self._config.logs.log_id = self._run_id
            self._config.logs.path = os.path.join(self._root, str(self._run_id))
            self._config.system.date = date
            self._config.system.time = time
            self._config.system.status = "STARTING"
        omegaconf.OmegaConf.set_struct(self._config, False)



    def _set_cluster_job_id(self):
        abs_name = os.path.join(self._run_dir, "metadata.yaml")
        if os.path.isfile(abs_name):
            with open(abs_name, "r") as file:
                configs = yaml.safe_load(file)
                if "cluster_job_id" in configs["system"]:
                    omegaconf.OmegaConf.set_struct(self._config, True)
                    with omegaconf.open_dict(self._config):
                        self._config.system.cluster_job_id = configs["system"][
                            "cluster_job_id"
                        ]
                    omegaconf.OmegaConf.set_struct(self._config, False)



def _make_run_dir(_id, root):
    os.makedirs(root, exist_ok=True)
    log_dir = None
    if _id is None:
        fail_count = 0
        while log_dir is None:
            try:
                _id = _maximum_existing_run_id(root) + 1
                log_dir_tmp = os.path.join(root, str(_id))
                os.mkdir(log_dir)
                log_dir = log_dir_tmp # set log_dir only if successful creation
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
