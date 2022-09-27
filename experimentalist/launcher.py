import copy
import os
import functools
import pickle
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, List, Optional
from types import CodeType
from dataclasses import dataclass, field

from omegaconf import OmegaConf, DictConfig, open_dict, read_write
from omegaconf import MISSING

from hydra import version
from hydra._internal.deprecation_warning import deprecation_warning
from hydra._internal.utils import _run_hydra, get_args_parser
from hydra.core.hydra_config import HydraConfig
from hydra.core.utils import _flush_loggers, configure_log
from hydra.types import TaskFunction


from experimentalist.cluster_launcher import submit_job
from experimentalist.logger import Logger
from experimentalist.utils import flatten_dict


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


def remove_hydra_files(sweep_dir):
    # abs_sweep_dir = os.path.abspath(sweep_dir)
    try:
        os.remove(os.path.join(sweep_dir, "multirun.yaml"))
    except FileNotFoundError:
        pass


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


def set_co_filename(func, co_filename):
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


@dataclass
class Cluster:
    engine: str = ""
    cleanup_cmd: str = ""
    cmd: list = field(default_factory=lambda: [])


@dataclass
class OAR(Cluster):
    engine: str = "OAR"


@dataclass
class SLURM(Cluster):
    engine: str = "SLURM"


@dataclass
class System:
    user: str = "${oc.env:USER}"
    env: str = "conda activate '${oc.env:CONDA_DEFAULT_ENV}'"
    shell_path: str = "/bin/bash"
    shell_config_path: str = "~/.bashrc"
    isBatchJob: bool = False
    status: str = MISSING
    cmd: str = MISSING
    app: str = MISSING
    hostname: str = MISSING
    process_id: int = MISSING
    date: Any = MISSING
    time: Any = MISSING


@dataclass
class Logs:
    log_dir: str = "data/outputs"
    work_dir: str = "data/.workdir"
    root_dir: str = "."
    log_name: str = "logs"
    log_to_file: bool = False
    log_id: Any = None
    path: str = MISSING


@dataclass
class Config:
    system: System = System()
    logs: Logs = Logs()
    cluster: Cluster = Cluster()


def format_config(cfg):
    base_conf = OmegaConf.structured(Config)
    conf_dict = OmegaConf.to_container(base_conf, resolve=True)
    base_conf = OmegaConf.create(conf_dict)
    return OmegaConf.merge(base_conf, cfg)


def launch(
    config_path: Optional[str] = _UNSPECIFIED_,
    config_name: Optional[str] = None,
    version_base: Optional[str] = None,
) -> Callable[[TaskFunction], Any]:
    """
    :param config_path: The config path, a directory relative
                        to the declaring python file.
                        If config_path is None no directory is added
                        to the Config search path.
    :param config_name: The name of the config
                        (usually the file name without the .yaml extension)
    """

    # hydra_decorator = hydra.main(
    #     config_path=config_path, config_name=config_name, version_base=version_base
    # )

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
                flattened_hydra_default_dict = flatten_dict(hydra_defaults_dict)
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
                    remove_hydra_files(hydra_defaults_dict["hydra"]["sweep"]["dir"])

        return decorated_main

    def launcher_decorator(task_function):
        @functools.wraps(task_function)
        def decorated_task(cfg):
            cfg = format_config(cfg)
            cfg.system.cmd = task_function.__code__.co_filename
            cfg.system.app = os.environ["_"]
            if cfg.cluster.engine not in ["OAR", "SLURM"]:
                cfg.system.isBatchJob = False

            logger = Logger(cfg)
            logger.set_cluster_job_id()
            logger.log_config()
            if not cfg.system.isBatchJob:
                try:
                    logger.log_status("RUNNING")
                    task_function(cfg, logger)
                    logger.log_status("COMPLETE")
                    return None
                except Exception:
                    logger.log_status("FAILED")
                    raise

            cfg.system.isBatchJob = False
            submit_job(cfg, logger)

        set_co_filename(decorated_task, task_function.__code__.co_filename)

        return decorated_task

    def composed_decorator(task_function: TaskFunction) -> Callable[[], None]:
        # old_co_filename = task_function.__code__.co_filename
        decorated_task = launcher_decorator(task_function)
        # new_co_filename = decorated_task.__code__.co_filename
        # set_co_filename(decorated_task, old_co_filename)
        task_function = hydra_decorator(decorated_task)
        # set_co_filename(task_function, new_co_filename)
        return task_function

    return composed_decorator
