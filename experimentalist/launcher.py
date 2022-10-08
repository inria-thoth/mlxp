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
from experimentalist.utils import _flatten_dict


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

valid_schedulers = ["OAR", "SLURM"]

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
    isForceGitClean: bool = True
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




def launch(
    config_path: Optional[str] = _UNSPECIFIED_,
    config_name: Optional[str] = None
) -> Callable[[TaskFunction], Any]:
    """Decorator of the main function to be executed.  
    
    Notes
    -----
    This function allows to use hydra for excuting python code 
    and enables most of the functionalities provided by the hydra-core package: 
    composing configs from multiple files, overriding configs form the command line 
    and sweeping over multiple values of a given configuration.
    It behaves similarly as the decorator hydra.main provided in the hydra-core package:
    https://github.com/facebookresearch/hydra/blob/main/hydra/main.py .
    When it comes to passing the configs to the run: 
    The configs are contained in a yaml file 'config_name' 
    within the directory 'config_path' passed as argument to this function.
    Overrides of the configs from the command line are also supported 
    as well as sweeping over multiple values of a given configuration.
    See: https://hydra.cc/docs/intro/ for complete documentation on how to use Hydra. 
    Unlike hydra.main which decorates functions taking an OmegaConf object, 
    this function decorates functions with the following signature: main(logger: Logger).
    The logger object, can then be used to log outputs of the current run. 
    Finally, this function also supports batch submission to a cluster using a scheduler. 
    This is acheived by setting the config parameter: logger.config.system.isBatchJob to True 
    and configuring the scheduler by specifying a config file cluster. 
    Two job schedulers are currently supported: ['OAR', 'SLURM' ]. 
 
    
    Parameters
    ----------
    config_path: The config path, a directory relative
                        to the declaring python file.
                        If config_path is None no directory is added
                        to the Config search path.
    config_name: The name of the config
                        (usually the file name without the .yaml extension)

    Raises
    ------
    `AssertionError`
        Raised if no valid job scheduler is specifyed when submitting in batch mode, i.e. logger.config.system.isBatchJob=True.
    `JobSubmissionError`
        Raised if the launcher failed to submit a job in batch mode.
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
            if cfg.cluster.engine not in ["OAR", "SLURM"]:
                cfg.system.isBatchJob = False

            logger = Logger(cfg)
            logger._set_cluster_job_id()
            logger.log_config()

            if cfg.system.isBatchJob:
                if cfg.cluster.engine not in valid_schedulers:
                    raise AssertionError(f"No valid job scheduler found! Supported schedulers are {str(valid_schedulers)}")
            else:
                try:
                    logger._log_status("RUNNING")
                    task_function(logger)
                    logger._log_status("COMPLETE")
                    return None
                except Exception:
                    logger._log_status("FAILED")
                    raise

            cfg.system.isBatchJob = False
            submit_job(logger)

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


