import copy
import os
import subprocess
import functools
import pickle
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, List, Optional, Union, Dict, TypeVar
from types import CodeType
from dataclasses import dataclass, field

from omegaconf import DictConfig
from enum import Enum

from hydra import version
from hydra._internal.deprecation_warning import deprecation_warning
from hydra._internal.utils import _run_hydra, get_args_parser
from hydra.core.hydra_config import HydraConfig
from hydra.types import TaskFunction


from mlxpy.utils import _flatten_dict
from mlxpy.data_structures.config_dict import convert_dict, ConfigDict
from mlxpy.logger import Logger
from mlxpy.errors import MissingFieldError
import mlxpy

from datetime import datetime
import socket
import sys
from dataclasses import dataclass
from mlxpy._internal.configure import _build_config
import yaml
import importlib



_UNSPECIFIED_: Any = object()


hydra_defaults_dict = {
    "hydra": {
        "mode": "MULTIRUN",
        "output_subdir": "null",
        "run": {"dir": "."},
        "sweep": {"dir": ".", "subdir": "."},
    },
    "hydra/job_logging": "disabled",
    "hydra/hydra_logging": "disabled",
}

vm_choices_file = os.path.join(hydra_defaults_dict["hydra"]["sweep"]["dir"],
                                            "vm_choices.yaml")


def clean_dir():
    sweep_dir = hydra_defaults_dict["hydra"]["sweep"]["dir"]
    try:
        os.remove(os.path.join(sweep_dir, "multirun.yaml"))
        os.remove(vm_choices_file)
    except FileNotFoundError:
        pass   

class Status(Enum):
    """
        Status of a run. 

        The status can take the following values:

        - STARTING: The metadata for the run have been created.

        - RUNNING: The experiment is currently running. 
        
        - COMPLETE: The run is  complete and did not through any error.
        
        - FAILED: The run stoped due to an error.
    """


    STARTING = "STARTING"
    COMPLETE = "COMPLETE"
    RUNNING = "RUNNING"
    FAILED = "FAILED"


@dataclass
class Context:
    """
    The contex object passed to the decorated function when using decorator mlxpy.launch.

    .. py:attribute:: config
        :type: ConfigDict

        A structure containing project-specific options provided by the user. 
        These options are loaded from a yaml file 'config.yaml' contained in the directory 'config_path' 
        provided as argument to the decorator mlxpy.launch. It's content can be overriden from the command line. 

    .. py:attribute:: mlxpy
        :type: ConfigDict

        A structure containing mlxpy's default settings for the project. 
        Its content is loaded from a yaml file 'mlxpy.yaml' located in the same directory 'config.yaml'. 

    .. py:attribute:: info
        :type: ConfigDict

        A structure containing information about the current run: ex. status, start time, hostname, etc. 

    .. py:attribute:: logger
        :type: Union[Logger,None]

        A logger object that can be used for logging variables (metrics, checkpoints, artifacts). 
        When logging is enabled, these variables are all stored in a uniquely defined directory. 


    """
    
    config : ConfigDict = None
    mlxpy : ConfigDict = None
    info: ConfigDict = None
    logger: Union[Logger,None] = None


T = TypeVar('T')

def instance_from_dict(class_name: str, arguments: Dict[str, Any])->T:
    """
        A factory function that dynamically creates an instance of a class 
        based on a dictionary of arguments.
        
        :param class_name: The name of the class 
        :param arguments: A dictionary of arguments to the class constructor
        :type class_name: str
        :type arguments: Dict[str,Any]
        :return: An instance of a class 'class_name' constructed using the arguments in 'arguments'.
        :rtype: 
    """

    attr = import_module(class_name)
    if arguments:
        attr = attr(**arguments)
    else:
        attr = attr()

    return attr


def import_module(module_name):
    module, attr = os.path.splitext(module_name)
    if not attr:
        return  getattr(mlxpy, module)
    else:
        try:
            module = importlib.import_module(module)
            return getattr(module, attr[1:])
        except:
            try:
                module = import_module(module)
                return getattr(module, attr[1:])
            except:
                return eval(module+attr[1:])



def _instance_from_config(config):
    config_module_name = "name"
    config = copy.deepcopy(config)
    module_name = config.pop(config_module_name)

    return instance_from_dict(module_name, config)

def launch(
    config_path: str = './configs',
    seeding_function: Union[Callable[[Any], None],None] = None
) -> Callable[[TaskFunction], Any]:
    """Decorator of the main function to be executed.  

    This function allows three main functionalities: 
        - Composing configurations from multiple files using hydra (see hydra-core package). 
        This behavior is similar to the decorator hydra.main provided in the hydra-core package:
        https://github.com/facebookresearch/hydra/blob/main/hydra/main.py. 
        The configs are contained in a yaml file 'config.yaml' stored in 
        the directory 'config_path' passed as argument to this function.
        Unlike hydra.main which decorates functions taking an OmegaConf object, 
        mlxpy.launch  decorates functions with the following signature: main(ctx: mlxpy.Context).
        The ctx object is created on the fly during the execution of the program 
        and stores information about the run. 
        In particular, the field cfg.config stores the options contained in the config file 'config.yaml'. 
        Additionally, cfg.logger, provides a logger object of the class mlxpy.Logger for logging results of the run.  
        Just like in hydra, it is also possible to override the configs from the command line and 
        to sweep over multiple values of a given configuration when executing python code.   
        See: https://hydra.cc/docs/intro/ for complete documentation on how to use Hydra.
    
        - Seeding: Additionally, mlxpy.launch takes an optional argument 'seeding_function'. 
        By default, 'seeding_function' is None and does nothing. If a callable object is passed to it, this object is called with the argument cfg.config.seed
        right before calling the decorated function. The user-defined callable is meant to set the seed of any random number generator used in the code. 
        In that case, the option 'ctx.config.seed' must be none empty.  

        - Submitting jobs to a cluster queue using a scheduler. 
        This is achieved by setting the config value scheduler.name to the name of a valid scheduler. 
        Two job schedulers are currently supported by default: ['OARScheduler', 'SLURMScheduler' ]. 
        It is possible to support other schedulers by 
        defining a subclass of the abstract class Scheduler.

        - Version management: Creating a 'safe' working directory when submitting jobs to a cluster. 
        This functionality sets the working directory to a new location 
        created by making a copy of the code based on the latest commit 
        to a separate destination, if it doesn't exist already. Executing code 
        from this copy allows separting development code from code deployed in a cluster. 
        It also allows recovering exactly the code used for a given run.
        This behavior can be modified by using a different version manager VersionManager (default GitVM). 
        
        .. note:: Currently, this functionality expects 
        the executed python file to part of a git repository. 

    :param config_path: The config path, a directory where 
    the default user configuration and mlxpy settings are stored.
    :param seeding_function:  A callable for setting the seed of random number generators. 
    It is called with the seed option in 'ctx.config.seed' passed to it.

    :type config_path: str (default './configs')
    :type seeding_function: Union[Callable[[Any], None],None] (default None)

    """
    config_name = "config"
    version_base= None # by default set the version base for hydra to None.
    version.setbase(version_base)
    
    os.makedirs(config_path, exist_ok=True)
    custom_config_file = os.path.join(config_path,config_name+".yaml")
    if not os.path.exists(custom_config_file):
        custom_config = {'seed':None}
        with open(custom_config_file, "w") as f:
            yaml.dump(custom_config, f) 

    work_dir =  os.getcwd()

    def hydra_decorator(task_function: TaskFunction) -> Callable[[], None]:
        # task_function = launch(task_function)
        @functools.wraps(task_function)
        def decorated_main(cfg_passthrough: Optional[DictConfig] = None) -> Any:
            if cfg_passthrough is not None:
                return task_function(cfg_passthrough)
            else:
                args_parser = get_args_parser()
                args = args_parser.parse_args()

                ### Setting hydra defaults 
                flattened_hydra_default_dict = _flatten_dict(hydra_defaults_dict)
                hydra_defaults = [
                    key + "=" + value
                    for key, value in flattened_hydra_default_dict.items()
                ]
                overrides = args.overrides + hydra_defaults
                setattr(args, "overrides", overrides)

                clean_dir()
               
                
                _run_hydra(
                    args=args,
                    args_parser=args_parser,
                    task_function=task_function,
                    config_path=config_path,
                    config_name=config_name,
                )
                
                clean_dir()

        return decorated_main

    def launcher_decorator(task_function):
        @functools.wraps(task_function)
        def decorated_task(cfg):
            cfg = _build_config(cfg, config_path)
            
            now = datetime.now()
            info = {'hostname': socket.gethostname(),
                    'process_id': os.getpid(),
                    'executable':task_function.__code__.co_filename,
                    'app': os.environ["_"],
                    'start_date':now.strftime("%d/%m/%Y"),
                    'start_time':now.strftime("%H:%M:%S"),
                    'status':Status.STARTING.value}
            
            cfg.update({'info':info})

            if cfg.mlxpy.use_version_manager:
                version_manager = _instance_from_config(cfg.mlxpy.version_manager)
                version_manager._handle_interactive_mode(cfg.mlxpy.interactive_mode, vm_choices_file)
                work_dir = version_manager.make_working_directory()
                cfg.update({'info':{'version_manager': version_manager.get_info()} })
            else:
                work_dir = os.getcwd()

            cfg.update({'info': {'work_dir':work_dir}})

            if cfg.mlxpy.use_scheduler:
                
                scheduler = _instance_from_config(cfg.mlxpy.scheduler) 
                if not cfg.mlxpy.use_logger:
                    print("Logger is currently disabled.")
                    print("To use the scheduler, the logger must be enabled")
                    print("Enabling the logger...")
                    cfg.mlxpy.use_logger=True
            else:
                scheduler = None


            if cfg.mlxpy.use_logger:
                logger = _instance_from_config(cfg.mlxpy.logger)
                log_id = logger.log_id
                log_dir = logger.log_dir
                parent_log_dir = logger.parent_log_dir
                cfg.update({'info':{'logger':logger.get_info()}})
            else:
                logger = None
            
            if cfg.mlxpy.use_scheduler:

                main_cmd = _main_job_command(cfg.info.app,
                                             cfg.info.executable,
                                             work_dir,
                                             parent_log_dir,
                                             log_id)
                
                scheduler.submit_job(main_cmd, log_dir)
                cfg.update({'info':{'scheduler':scheduler.get_info()}})
                logger._log_configs(cfg)
                
            else:
                
                # ## Setting up the working directory
                cur_dir = os.getcwd()
                _set_work_dir(work_dir)

                

                if logger:
                    cfg.update(_get_scheduler_configs(log_dir)) # Checks if a metadata file exists and loads the scheduler configs
                try:
                    
                    cfg.update({'info':{'status':Status.RUNNING.value}})
                    if logger:
                        logger._log_configs(cfg)
                    if seeding_function:
                        try:
                            assert 'seed' in cfg.config.keys()
                        except AssertionError:
                            msg = "Missing field: The 'config' must contain a field 'seed'\n"
                            msg+= "provided as argument to the function 'seeding_function' "
                            raise MissingFieldError(msg)
                        seeding_function(cfg.config.seed)


                    ctx = Context(config=cfg.config,
                                  mlxpy=cfg.mlxpy,
                                  info=cfg.info,
                                  logger = logger)
                    task_function(ctx)
                    now =  datetime.now()
                    info = {'end_date':now.strftime("%d/%m/%Y"),
                            'end_time':now.strftime("%H:%M:%S"),
                            'status':Status.COMPLETE.value}
            
                    cfg.update({'info':info})
                    
                    if logger:
                        logger._log_configs(cfg)
                    
                    _reset_work_dir(cur_dir)
                    return None
                except Exception:
                    now =  datetime.now()
                    info = {'end_date':now.strftime("%d/%m/%Y"),
                            'end_time':now.strftime("%H:%M:%S"),
                            'status':Status.FAILED.value}
            
                    cfg.update({'info':info})

                    if logger:
                        logger._log_configs(cfg)
                    
                    _reset_work_dir(cur_dir)
                    raise

        _set_co_filename(decorated_task, task_function.__code__.co_filename)

        return decorated_task

    def composed_decorator(task_function: TaskFunction) -> Callable[[], None]:
        decorated_task = launcher_decorator(task_function)
        task_function = hydra_decorator(decorated_task)

        return task_function

    return composed_decorator


def _set_work_dir(work_dir):
    os.chdir(work_dir)            
    sys.path.insert(0, work_dir)    

def _reset_work_dir(cur_dir):
    os.chdir(cur_dir)
    sys.path  = sys.path[1:]



def _set_co_filename(func, co_filename):
    fn_code = func.__code__
    func.__code__ = CodeType(
        fn_code.co_argcount,
        fn_code.co_posonlyargcount,
        fn_code.co_kwonlyargcount,
        fn_code.co_nlocals,
        fn_code.co_stacksize,
        fn_code.co_flags,
        fn_code.co_code,
        fn_code.co_consts,
        fn_code.co_names,
        fn_code.co_varnames,
        co_filename,
        fn_code.co_name,
        fn_code.co_firstlineno,
        fn_code.co_lnotab,
        fn_code.co_freevars,
        fn_code.co_cellvars,
    )


def _get_scheduler_configs(log_dir):
    abs_name = os.path.join(log_dir, 'metadata','info.yaml')
    scheduler_configs = {}
    
    if os.path.isfile(abs_name):
        with open(abs_name, "r") as file:
            configs = yaml.safe_load(file)
            try:
                scheduler_configs = {'info':{'scheduler':configs['scheduler']}}
            except KeyError:
                pass

    return  scheduler_configs




def _main_job_command(app,executable,work_dir, parent_log_dir, job_id):
    #exec_file = info.cmd
    exec_file = os.path.relpath(executable, os.getcwd())
    

    args = _get_overrides()
    values = [
        f"cd {work_dir}",
        f"{app} {exec_file} {args} \
            +mlxpy.logger.forced_log_id={job_id}\
            +mlxpy.logger.parent_log_dir={parent_log_dir} \
            +mlxpy.use_scheduler={False}\
            +mlxpy.use_version_manager={False}"
    ]

    values = [f"{val}\n" for val in values]
    return "".join(values)

def _get_overrides():
    hydra_cfg = HydraConfig.get()
    overrides = hydra_cfg.overrides.task
    def filter_fn(x):
        return ("version_manager" not in x) and ("scheduler" not in x) and ("logger.parent_log_dir" not in x)
    filtered_args = list(filter(filter_fn, overrides))
    args = " ".join(filtered_args)
    return args

