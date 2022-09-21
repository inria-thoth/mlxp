# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import copy
import functools
import pickle
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, List, Optional
from types import CodeType
from omegaconf import DictConfig, open_dict, read_write

from hydra import version
from hydra._internal.deprecation_warning import deprecation_warning
from hydra._internal.utils import _run_hydra, get_args_parser
from hydra.core.hydra_config import HydraConfig
from hydra.core.utils import _flush_loggers, configure_log
from hydra.types import TaskFunction
from Experimentalist.cluster_launcher import submit_job
from Experimentalist.structured_config import format_config
import os


_UNSPECIFIED_: Any = object()


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


hydra_defaults = ['hydra.output_subdir=null',
                 'hydra.run.dir=.',
                 'hydra.sweep.dir=.',
                 'hydra.sweep.subdir=.',
                 'hydra.hydra_logging.disable_existing_loggers=True',
                 'hydra.job_logging.disable_existing_loggers=True']






def fix_co_filename(func, co_filename):
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
        fn_code.co_cellvars)


def launch(
    config_path: Optional[str] = _UNSPECIFIED_,
    config_name: Optional[str] = None,
    version_base: Optional[str] = None,
) -> Callable[[TaskFunction], Any]:
    """
    :param config_path: The config path, a directory relative to the declaring python file.
                        If config_path is None no directory is added to the Config search path.
    :param config_name: The name of the config (usually the file name without the .yaml extension)
    """

    version.setbase(version_base)

    if config_path is _UNSPECIFIED_:
        if version.base_at_least("1.2"):
            config_path = None
        elif version_base is _UNSPECIFIED_:
            url = "https://hydra.cc/docs/upgrades/1.0_to_1.1/changes_to_hydra_main_config_path"
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

    def main_decorator(task_function: TaskFunction) -> Callable[[], None]:
        #task_function = launch(task_function)
        @functools.wraps(task_function)
        def decorated_main(cfg_passthrough: Optional[DictConfig] = None) -> Any:
            if cfg_passthrough is not None:
                return task_function(cfg_passthrough)
            else:
                args_parser = get_args_parser()
                args = args_parser.parse_args()
                overrides = args.overrides + hydra_defaults
                setattr(args, 'overrides', overrides)

                if args.experimental_rerun is not None:
                    cfg = _get_rerun_conf(args.experimental_rerun, args.overrides)
                    task_function(cfg)
                    _flush_loggers()
                else:
                    # no return value from run_hydra() as it may sometime actually run the task_function
                    # multiple times (--multirun)
                    _run_hydra(
                        args=args,
                        args_parser=args_parser,
                        task_function=task_function,
                        config_path=config_path,
                        config_name=config_name,
                    )
        return decorated_main

    def cluster_launcher_decorator(task_function):
        @functools.wraps(task_function)
        def decorated_task(cfg):
            cfg = format_config(cfg)
            cfg.system.cmd=task_function.__code__.co_filename
            cfg.system.app=os.environ['_']
            if cfg.cluster.engine not in ["OAR","SLURM"]:
                cfg.system.isBatchJob=False
            if not cfg.system.isBatchJob:
                return task_function(cfg)            
            cfg.system.isBatchJob=False
            submit_job(cfg)
        fix_co_filename(decorated_task, task_function.__code__.co_filename)        
        return decorated_task

    def composed_decorator(task_function: TaskFunction) -> Callable[[], None]:
        task_function = cluster_launcher_decorator(task_function)
        task_function = main_decorator(task_function)
        return task_function

    return composed_decorator




