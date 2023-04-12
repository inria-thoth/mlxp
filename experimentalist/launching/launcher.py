import copy
import os
import subprocess
import functools
import pickle
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, List, Optional
from types import CodeType
from dataclasses import dataclass, field

import omegaconf
from omegaconf import OmegaConf, DictConfig, open_dict, read_write
from omegaconf import MISSING
from omegaconf.errors import OmegaConfBaseException
from datetime import datetime


from hydra import version
from hydra._internal.deprecation_warning import deprecation_warning
from hydra._internal.utils import _run_hydra, get_args_parser
from hydra.core.hydra_config import HydraConfig
from hydra.core.utils import _flush_loggers, configure_log
from hydra.types import TaskFunction


from experimentalist.logging.logger import Logger, Status
from experimentalist.utils import _flatten_dict, config_to_instance
from experimentalist.launching.schemas import Config
from experimentalist.launching.schedulers import JobSubmissionError


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



def launch(
    config_path: Optional[str] = _UNSPECIFIED_,
    config_name: Optional[str] = None
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
        This is achieved by setting the config value scheduler.use_scheduler=True. 
        Two job schedulers are currently supported by default: ['OAR', 'SLURM' ]. 
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
    :raises JobSubmissionError: when using a scheduler if the job submission fails in batch mode.
    :raises git.exc.InvalidGitRepositoryError: when using the LastGitCommitWD manager 
                if the executed code does not have a git repository.
    """

    version_base= None # by default set the version base for hydra to None.
    version.setbase(version_base)

    if config_path is _UNSPECIFIED_:
        if version.base_at_least("1.2"):
            config_path = None
        elif version_base is _UNSPECIFIED_:
            url = "https://hydra.cc/docs/upgrades/\
                    1.0_to_1.1/changes_to_hydra_main_config_path"
            deprecation_warning(
                message=dedent(
                    f"""
                config_path is not specified in @hydra.main().
                See {url} for more information."""
                ),
                stacklevel=2,
            )
            config_path = "."
        else:
            config_path = "."

    def hydra_decorator(task_function: TaskFunction) -> Callable[[], None]:
        # task_function = launch(task_function)
        @functools.wraps(task_function)
        def decorated_main(cfg_passthrough: Optional[DictConfig] = None) -> Any:
            if cfg_passthrough is not None:
                return task_function(cfg_passthrough)
            else:
                flattened_hydra_default_dict = _flatten_dict(hydra_defaults_dict)
                hydra_defaults = [
                    key + "=" + value
                    for key, value in flattened_hydra_default_dict.items()
                ]
                args_parser = get_args_parser()
                args = args_parser.parse_args()
                overrides = args.overrides + hydra_defaults
                setattr(args, "overrides", overrides)

                if args.experimental_rerun is not None:
                    cfg = _get_rerun_conf(args.experimental_rerun, args.overrides)
                    task_function(cfg)
                    _flush_loggers()
                else:
                    # no return value from run_hydra()
                    # as it may sometime actually run the task_function
                    # multiple times (--multirun)
                    _run_hydra(
                        args=args,
                        args_parser=args_parser,
                        task_function=task_function,
                        config_path=config_path,
                        config_name=config_name,
                    )

                    sweep_dir = hydra_defaults_dict["hydra"]["sweep"]["dir"]
                    try:
                        os.remove(os.path.join(sweep_dir, "multirun.yaml"))
                    except FileNotFoundError:
                        pass

        return decorated_main

    def launcher_decorator(task_function):
        @functools.wraps(task_function)
        def decorated_task(cfg):
            base_conf = OmegaConf.structured(Config)
            conf_dict = OmegaConf.to_container(base_conf, resolve=True)
            base_conf = OmegaConf.create(conf_dict)
            cfg = OmegaConf.merge(base_conf, cfg)

            cfg.system.cmd = task_function.__code__.co_filename
            cfg.system.app = os.environ["_"]
            ## Ensuring parent_log_dir is an absolute path
            cfg.logs.parent_log_dir = os.path.abspath(cfg.logs.parent_log_dir)
            
            if cfg.scheduler.use_scheduler:
                scheduler = config_to_instance(config_module_name="class_name", **cfg.scheduler) 
                wd_manager = config_to_instance(config_module_name="class_name", **cfg.wd_manager)
                work_dir = wd_manager.make_working_directory()
                wd_manager.update_configs(cfg.wd_manager)

                logger = Logger(cfg)
                cmd = _make_job_command(scheduler,
                                        cfg.system,
                                        work_dir,
                                        logger.parent_log_dir,
                                        logger.log_dir,
                                        logger.log_id)
                print(cmd)

                job_path = _save_job_command(cmd, logger.log_dir)
                process_output = scheduler.submit_job(job_path)
                scheduler_job_id = scheduler.get_job_id(process_output) 

                logger._update_scheduler_job_id(scheduler_job_id)
                logger.log_config()
                
            else:

                logger = Logger(cfg)
                logger._set_scheduler_job_id() # Checks if a metadata file exists and loads some of its content.
                logger.log_config()
                try:
                    logger._log_status(Status.RUNNING)
                    task_function(logger)
                    logger._log_status(Status.COMPLETE)
                    return None
                except Exception:
                    logger._log_status(Status.FAILED)
                    raise
                

        _set_co_filename(decorated_task, task_function.__code__.co_filename)

        return decorated_task

    def composed_decorator(task_function: TaskFunction) -> Callable[[], None]:
        decorated_task = launcher_decorator(task_function)
        task_function = hydra_decorator(decorated_task)
        return task_function

    return composed_decorator


def _get_rerun_conf(file_path: str, overrides: List[str]) -> DictConfig:
    msg = "Experimental rerun CLI option, other command line args are ignored."
    warnings.warn(msg, UserWarning)
    file = Path(file_path)
    if not file.exists():
        raise ValueError(f"File {file} does not exist!")

    if len(overrides) > 0:
        msg = "Config overrides are not supported as of now."
        warnings.warn(msg, UserWarning)

    with open(str(file), "rb") as input:
        config = pickle.load(input)  # nosec
    configure_log(config.hydra.job_logging, config.hydra.verbose)
    HydraConfig.instance().set_config(config)
    task_cfg = copy.deepcopy(config)
    with read_write(task_cfg):
        with open_dict(task_cfg):
            del task_cfg["hydra"]
    assert isinstance(task_cfg, DictConfig)
    return task_cfg


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




def _make_job_command(scheduler,
                  system, 
                  work_dir,
                  parent_log_dir,
                  log_dir,
                  job_id,
                  ):
    ## Writing job command
    job_command = [_job_command(system,parent_log_dir, work_dir, job_id)]

    ## Setting shell   
    shell_cmd = [f"#!{system.shell_path}\n"]
    
    ## Setting scheduler options
    sheduler_option_command = [scheduler.option_command(log_dir)]
    
    ## Setting environment
    env_cmds = [f"{system.shell_config_cmd}\n", 
                f"{scheduler.cleanup_cmd}\n"]
    try:
        env_cmds += [f"{system.env}\n"]
    except OmegaConfBaseException:
        pass

    cmd = "".join(shell_cmd + sheduler_option_command + env_cmds + job_command)

    return cmd





def _save_job_command(cmd_string, log_dir):
    job_path = os.path.join(log_dir, "script.sh")
    with open(job_path, "w") as f:
        f.write(cmd_string)
    return job_path



def _job_command(system, parent_log_dir, work_dir, job_id):
    #exec_file = system.cmd
    exec_file = os.path.relpath(system.cmd, os.getcwd())
    

    args = _get_overrides()
    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")
    values = [
        f"cd {work_dir}",
        f"{system.app} {exec_file} {args} ++system.date='{date}' \
            ++system.time='{time}'  ++logs.log_id={job_id}\
            ++logs.parent_log_dir={parent_log_dir} ++scheduler.use_scheduler={False}",
    ]
    values = [f"{val}\n" for val in values]
    return "".join(values)

def _get_overrides():
    hydra_cfg = HydraConfig.get()
    overrides = hydra_cfg.overrides.task
    def filter_fn(x):
        return ("scheduler.use_scheduler" not in x) and ("logs.parent_log_dir" not in x)
    filtered_args = list(filter(filter_fn, overrides))
    args = " ".join(filtered_args)
    return args

