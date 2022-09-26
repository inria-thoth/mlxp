import functools
from typing import Any, Callable, Optional
from types import CodeType

import hydra
from hydra.types import TaskFunction
from omegaconf import MISSING
from omegaconf import OmegaConf
from dataclasses import dataclass, field


from experimentalist.cluster_launcher import submit_job
from experimentalist.logger import Logger

import os


_UNSPECIFIED_: Any = object()


hydra_defaults = [
    "hydra.output_subdir=null",
    "hydra.run.dir=.",
    "hydra.sweep.dir=.",
    "hydra.sweep.subdir=.",
    "hydra.hydra_logging.disable_existing_loggers=True",
    "hydra.job_logging.disable_existing_loggers=True",
]


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

    hydra_decorator = hydra.main(
        config_path=config_path, config_name=config_name, version_base=version_base
    )

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
