import copy
import os
import subprocess
import functools
import pickle
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, List, Optional, Union
from types import CodeType
from dataclasses import dataclass, field

import omegaconf
from omegaconf import OmegaConf, DictConfig, open_dict, read_write
from omegaconf import MISSING
from omegaconf.errors import OmegaConfBaseException
from enum import Enum

from hydra import version
from hydra._internal.deprecation_warning import deprecation_warning
from hydra._internal.utils import _run_hydra, get_args_parser
from hydra.core.hydra_config import HydraConfig
from hydra.types import TaskFunction


from mlxpy.utils import _flatten_dict, config_to_instance
from mlxpy.data_structures.schemas import Metadata
from mlxpy.data_structures.config_dict import convert_dict, ConfigDict
from mlxpy.logger import Logger

from datetime import datetime
import socket
import sys
from dataclasses import dataclass


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
    config : ConfigDict = MISSING
    mlxpy : ConfigDict = MISSING
    info: ConfigDict = MISSING
    logger: Union[Logger,None] = MISSING


  

def launch(
    config_path: str = './configs',
    seeding_function: Union[Callable[[Any], None],None] = None
) -> Callable[[TaskFunction], Any]:
    """Decorator of the main function to be executed.  

    This function allows three main functionalities: 
        - Composing configurations from multiple files using hydra (see hydra-core package). 
        This behavior is similar to the decorator hydra.main provided in the hydra-core package:
        https://github.com/facebookresearch/hydra/blob/main/hydra/main.py. 
        The configs are contained in a yaml file 'config_name' 
        within the directory 'config_path' passed as argument to this function. 
        Unlike hydra.main which decorates functions taking an OmegaConf object, 
        this decorator acts on functions with the following signature: main(logger: Logger).
        The logger object, can then be used to log outputs of the current run.
        Just like in hydra, it is also possible to override the configs from the command line and 
        to sweep over multiple values of a given configuration when executing python code.   
        See: https://hydra.cc/docs/intro/ for complete documentation on how to use Hydra.
    
        - Submitting jobs the a scheduler's queue in a cluster. 
        This is achieved by setting the config value scheduler.name to the name of the scheduler instead of None. 
        Two job schedulers are currently supported by default: ['OARScheduler', 'SLURMScheduler' ]. 
        It is possible to support other schedulers by 
        defining a subclass of the abstract class Scheduler.

        - Creating a 'safe' working directory when submitting jobs to a cluster. 
        This functionality sets the working directory to a new location 
        created by making a copy of the code based on the latest commit 
        to a separate destination, if it doesn't exist already. Executing code 
        from this copy allows separting development code from code deployed in a cluster. 
        It also allows recovering exactly the code used for a given run.
        This behavior can be modified by using a different working directory manager WDManager (default LastGitCommitWD). 
        
        .. note:: Currently, this functionality expects 
        the executed python file to part of the git repository. 

    :param config_path: The config path, a directory relative
                        to the declaring python file.
                        If config_path is None no directory is added
                        to the Config search path.
    :param config_name: The name of the config
                        (usually the file name without the .yaml extension)
    
    :type config_path: str
    :type config_name: str (default "None")
    """
    config_name = "config"
    version_base= None # by default set the version base for hydra to None.
    version.setbase(version_base)
    
    os.makedirs(config_path, exist_ok=True)
    custom_config_file = os.path.join(config_path,config_name+".yaml")
    if not os.path.exists(custom_config_file):
        custom_config = {'seed':None}
        omegaconf.OmegaConf.save(config=custom_config, f=custom_config_file)

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
                    'exec':task_function.__code__.co_filename,
                    'app': os.environ["_"],
                    'start_date':now.strftime("%d/%m/%Y"),
                    'start_time':now.strftime("%H:%M:%S"),
                    'status':Status.STARTING.value}
            
            cfg.update_dict({'info':info})

            if cfg.mlxpy.use_version_manager:
                version_manager = config_to_instance(config_module_name="name", **cfg.mlxpy.version_manager)
                version_manager.set_vm_choices_from_file(vm_choices_file)
                work_dir = version_manager.make_working_directory()
                cfg.update_dict({'info':version_manager.get_configs()})
            else:
                work_dir = os.getcwd()

            if cfg.mlxpy.use_logger:
                logger = config_to_instance(config_module_name="name", **cfg.mlxpy.logger)
                log_id = logger.log_id
                log_dir = logger.log_dir
                parent_log_dir = logger.parent_log_dir
                cfg.update_dict({'info':{'log_id':log_id, 'log_dir':log_dir}})
            else:
                logger = None
            
            if cfg.mlxpy.use_scheduler:
                try:
                    assert logger
                except AssertionError:
                    raise Exception("To use the scheduler, you must also use a logger, otherwise results might not be stored!")
                scheduler = config_to_instance(config_module_name="name", **cfg.mlxpy.scheduler) 
                main_cmd = _main_job_command(cfg.info.app,
                                             cfg.info.exec,
                                             work_dir,
                                             parent_log_dir,
                                             log_id)
                
                process_output = scheduler.submit_job(main_cmd, log_dir)
                scheduler_job_id = scheduler.get_job_id(process_output) 

                cfg.update_dict({'info':{'scheduler':{'scheduler_job_id':scheduler_job_id}}})
                logger._log_configs(cfg)
                
            else:
                pass
                print(work_dir)
                # ## Setting up the working directory
                os.chdir(work_dir)
                #sys.path.insert(0, work_dir)
                # cfg.update_dict({'info': {'work_dir':work_dir}})

                # if logger:
                #     cfg.update_dict(_get_scheduler_configs(log_dir)) # Checks if a metadata file exists and loads the scheduler configs
                # try:
                    
                #     cfg.update_dict({'info':{'status':Status.RUNNING.value}})
                #     if logger:
                #         logger._log_configs(cfg)
                #     if seeding_function:
                #         try:
                #             assert 'seed' in cfg.config.keys()
                #         except AssertionError:
                #             msg = "Missing field: The 'config' must contain a field 'seed'\n"
                #             msg+= "provided as argument to the function 'seeding_function' "
                #             raise Exception(msg)
                #         seeding_function(cfg.config.seed)


                #     ctx = Context(config=cfg.config,
                #                   mlxpy=cfg.mlxpy,
                #                   info=cfg.info,
                #                   logger = logger)
                #     task_function(ctx)
                #     now =  datetime.now()
                #     info = {'end_date':now.strftime("%d/%m/%Y"),
                #             'end_time':now.strftime("%H:%M:%S"),
                #             'status':Status.COMPLETE.value}
            
                #     cfg.update_dict({'info':info})
                    
                #     if logger:
                #         logger._log_configs(cfg)
                    
                #     return None
                # except Exception:
                #     now =  datetime.now()
                #     info = {'end_date':now.strftime("%d/%m/%Y"),
                #             'end_time':now.strftime("%H:%M:%S"),
                #             'status':Status.FAILED.value}
            
                #     cfg.update_dict({'info':info})

                #     if logger:
                #         logger._log_configs(cfg)
                #     raise

        _set_co_filename(decorated_task, task_function.__code__.co_filename)

        return decorated_task

    def composed_decorator(task_function: TaskFunction) -> Callable[[], None]:
        decorated_task = launcher_decorator(task_function)
        task_function = hydra_decorator(decorated_task)

        return task_function

    return composed_decorator


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
    import yaml
    if os.path.isfile(abs_name):
        with open(abs_name, "r") as file:
            configs = yaml.safe_load(file)
            try:
                scheduler_configs = {'info':{'scheduler':configs['scheduler']}}
            except KeyError:
                pass

    return  scheduler_configs


def _get_default_config(config_path):
    default_config = OmegaConf.structured(Metadata)
    conf_dict = OmegaConf.to_container(default_config, resolve=True)
    default_config = OmegaConf.create(conf_dict)
    
    os.makedirs(config_path, exist_ok=True)
    mlxpy_file = os.path.join(config_path,"mlxpy.yaml")

    if os.path.exists(mlxpy_file):
        import yaml
        with open(mlxpy_file, "r") as file:
            mlxpy = OmegaConf.create({'mlxpy':yaml.safe_load(file)})
        valid_keys = ['logger','version_manager','scheduler',
                        'use_version_manager',
                        'use_logger',
                        'use_scheduler']
        for key in mlxpy['mlxpy'].keys():
            try: 
                assert key in valid_keys 
            except AssertionError:
                msg =f'In the file {mlxpy_file},'
                msg += f'the following field is invalid: {key}\n'
                msg += f'Valid fields are {valid_keys}\n'
                raise AssertionError(msg)

        default_config = OmegaConf.merge(default_config, mlxpy)
    
    else:
        mlxpy = OmegaConf.create(default_config['mlxpy'])

        omegaconf.OmegaConf.save(config=mlxpy, f=mlxpy_file)

    # for key in cfg.keys():
    #     try: 
    #         assert key in  default_config.keys()
    #     except AssertionError:
    #         msg = f'The following field is invalid: {key}\n'
    #         msg += f'Valid fields are {default_config.keys()}\n'
    #         msg += "Consider using 'config' field for user defined options"
    #         raise AssertionError(msg)
    
    # default_config = convert_dict(default_config, 
    #                     src_class=omegaconf.dictconfig.DictConfig, 
    #                     dst_class=ConfigDict)
    return default_config

def _build_config(overrides, config_path):

    cfg = _get_default_config(config_path)


    overrides_mlxpy = OmegaConf.create({'mlxpy':overrides['mlxpy']})
    cfg = OmegaConf.merge(cfg, overrides_mlxpy)
    overrides = convert_dict(overrides, 
                        src_class=omegaconf.dictconfig.DictConfig, 
                        dst_class=dict)
    overrides.pop('mlxpy')
    overrides = convert_dict(overrides, 
                        src_class=dict,
                        dst_class=omegaconf.dictconfig.DictConfig)

    config = OmegaConf.create({'config':overrides})
    cfg = OmegaConf.merge(cfg, config)

    cfg = convert_dict(cfg, 
                        src_class=omegaconf.dictconfig.DictConfig, 
                        dst_class=ConfigDict)

    return cfg

def _save_job_command(cmd_string, log_dir):
    job_path = os.path.join(log_dir, "script.sh")
    with open(job_path, "w") as f:
        f.write(cmd_string)
    return job_path



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

