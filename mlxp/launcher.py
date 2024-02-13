"""The launcher allows launching multiple experiments on a cluster using hydra."""

import atexit
import copy
import functools
import importlib
import os
import signal
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import yaml
from hydra import version
from hydra._internal.utils import _run_hydra, get_args_parser
from hydra.core.hydra_config import HydraConfig
from hydra.types import TaskFunction
from omegaconf import DictConfig

import mlxp
from mlxp._internal.configure import _build_config, _process_config_path
from mlxp.data_structures.config_dict import ConfigDict
from mlxp.enumerations import Status
from mlxp.errors import InvalidSchedulerError, MissingFieldError
from mlxp.logger import Logger

_UNSPECIFIED_: Any = object()


hydra_defaults_dict = {
    "hydra.mode": "MULTIRUN",
    "hydra.output_subdir": "null",
    "hydra.run.dir": ".",
    "hydra.sweep.dir": ".",
    "hydra.sweep.subdir": ".",
    "hydra/job_logging": "disabled",
    "hydra/hydra_logging": "disabled",
}


interactive_mode_file = os.path.join(hydra_defaults_dict["hydra.sweep.dir"], "user_choices.yaml")


def _clean_dir():
    sweep_dir = hydra_defaults_dict["hydra.sweep.dir"]
    try:
        os.remove(os.path.join(sweep_dir, "multirun.yaml"))
        os.remove(interactive_mode_file)
    except FileNotFoundError:
        pass


atexit.register(_clean_dir)
signal.signal(signal.SIGTERM, _clean_dir)
signal.signal(signal.SIGINT, _clean_dir)


def launch(
    config_path: str = "configs", seeding_function: Union[Callable[[Any], None], None] = None,
) -> Callable[[TaskFunction], Any]:
    """Create a decorator of the main function to be executed.

    :example:

    .. code-block:: python

        import mlxp

        @mlxp.launch(config_path='configs',
                     seeding_function=set_seeds)
        def my_func(ctx: mlxp.Context)->None:

            print(ctx.config)

        if __name__ == "__main__":
            my_func()

    :param config_path: The config path, a directory where the default user configuration and MLXP settings are stored.
    :param seeding_function:  A callable for setting the seed of random number generators. It is called with the seed option in 'ctx.config.seed' passed to it.
    :type config_path: str (default './configs')
    :type seeding_function: Union[Callable[[Any], None],None] (default None)
    :return: A decorator of the main function to be executed.
    :type: Callable[[TaskFunction], Any]

    This function allows four main functionalities:

        1. Composing configurations from multiple files using hydra (see hydra-core package).
        This behavior is similar to the decorator hydra.main provided in the hydra-core package:
        https://github.com/facebookresearch/hydra/blob/main/hydra/main.py.
        The configs are contained in a yaml file 'config.yaml' stored in
        the directory 'config_path' passed as argument to this function.
        Unlike hydra.main which decorates functions taking an OmegaConf object,
        mlxp.launch  decorates functions with the following signature: main(ctx: mlxp.Context).
        The ctx object is created on the fly during the execution of the program
        and stores information about the run.
        In particular, the field cfg.config stores the options contained in the config file 'config.yaml'.
        Additionally, cfg.logger, provides a logger object of the class mlxp.Logger for logging results of the run.
        Just like in hydra, it is also possible to override the configs from the command line and
        to sweep over multiple values of a given configuration when executing python code.
        See: https://hydra.cc/docs/intro/ for complete documentation on how to use Hydra.

        2. Seeding: Additionally, mlxp.launch takes an optional argument 'seeding_function'.
        By default, 'seeding_function' is None and does nothing. If a callable object is passed to it, this object is called with the argument cfg.config.seed
        right before calling the decorated function. The user-defined callable is meant to set the seed of any random number generator used in the code.
        In that case, the option 'ctx.config.seed' must be none empty.

        3. Submitting jobs to a cluster queue using a scheduler.
        This is achieved by setting the config value scheduler.name to the name of a valid scheduler.
        Two job schedulers are currently supported by default: ['OARScheduler', 'SLURMScheduler' ].
        It is possible to support other schedulers by
        defining a subclass of the abstract class Scheduler.

        4. Version management: Creating a 'safe' working directory when submitting jobs to a cluster.
        This functionality sets the working directory to a new location
        created by making a copy of the code based on the latest commit
        to a separate destination, if it doesn't exist already. Executing code
        from this copy allows separting development code from code deployed in a cluster.
        It also allows recovering exactly the code used for a given run.
        This behavior can be modified by using a different version manager VersionManager (default GitVM).

        .. note:: Currently, this functionality expects the executed python file to part of a git repository.
    """
    config_name = "config"
    version_base = None  # by default set the version base for hydra to None.
    version.setbase(version_base)

    def hydra_decorator(task_function: TaskFunction) -> Callable[[], None]:
        # task_function = launch(task_function)
        @functools.wraps(task_function)
        def decorated_main(cfg_passthrough: Optional[DictConfig] = None) -> Any:
            processed_config_path = _process_config_path(config_path, task_function.__code__.co_filename)
            os.makedirs(processed_config_path, exist_ok=True)

            if cfg_passthrough is not None:
                return task_function(cfg_passthrough)
            else:
                args_parser = get_args_parser()
                args = args_parser.parse_args()

                # Setting hydra defaults
                hydra_defaults = [key + "=" + value for key, value in hydra_defaults_dict.items()]
                overrides = args.overrides + hydra_defaults
                setattr(args, "overrides", overrides)

                _clean_dir()

                _run_hydra(
                    args=args,
                    args_parser=args_parser,
                    task_function=task_function,
                    config_path=processed_config_path,
                    config_name=config_name,
                )

                _clean_dir()

        return decorated_main

    def launcher_decorator(task_function):
        @functools.wraps(task_function)
        def decorated_task(overrides):
            co_filename = task_function.__code__.co_filename

            cfg, im_handler = _build_config(
                config_path, config_name, co_filename, overrides, interactive_mode_file
            )
            now = datetime.now()
            info = {
                "hostname": socket.gethostname(),
                "process_id": os.getpid(),
                "executable": sys.executable,
                "current_file_path": task_function.__code__.co_filename,
                "start_date": now.strftime("%d/%m/%Y"),
                "start_time": now.strftime("%H:%M:%S"),
                "status": Status.STARTING.value,
            }

            cfg.update({"info": info})

            if cfg.mlxp.use_version_manager:
                version_manager = _instance_from_config(cfg.mlxp.version_manager)
                version_manager._set_im_handler(im_handler)
                work_dir = version_manager.make_working_directory()
                cfg.update({"info": {"version_manager": version_manager.get_info()}})
            else:
                work_dir = os.getcwd()

            cfg.update({"info": {"work_dir": work_dir}})

            if cfg.mlxp.use_scheduler:
                try:
                    scheduler = _instance_from_config(cfg.mlxp.scheduler, module=mlxp.scheduler)
                    if not cfg.mlxp.use_logger:
                        print("Logger is currently disabled.")
                        print("To use the scheduler, the logger must be enabled")
                        print("Enabling the logger...")
                        cfg.mlxp.use_logger = True
                except AttributeError:
                    error_msg = cfg.mlxp.scheduler.name + " is not a valid scheduler\n"
                    error_msg += "There are two options to prevent this error from happening:\n"
                    error_msg += " 1) Disable the scheduler by setting mlxp.use_scheduler=False\n"
                    error_msg += " 2) Configure a valid scheduler: for instance, you can use the interactive mode to select one of the default schedulers\n"
                    error_msg += "For more information about scheduler configuration, please refer to the documentation"
                    raise InvalidSchedulerError(error_msg) from None
                    # scheduler = None
                    # cfg.mlxp.use_scheduler = False
            else:
                scheduler = None

            if cfg.mlxp.use_logger:
                logger = _instance_from_config(cfg.mlxp.logger)
                log_id = logger.log_id
                log_dir = logger.log_dir
                parent_log_dir = logger.parent_log_dir
                cfg.update({"info": {"logger": logger.get_info()}})
                cfg.update({"config": _get_configs(log_dir)})
            else:
                logger = None

            if cfg.mlxp.use_scheduler:
                main_cmd = _main_job_command(
                    cfg.info.executable, cfg.info.current_file_path, work_dir, parent_log_dir, log_id,
                )

                scheduler.submit_job(main_cmd, log_dir)
                cfg.update({"info": {"scheduler": scheduler.get_info()}})
                logger._log_configs(cfg)

            else:
                # ## Setting up the working directory
                cur_dir = os.getcwd()
                _set_work_dir(work_dir)

                if logger:
                    cfg.update({"info": _get_mlxp_configs(log_dir)})
                try:
                    cfg.update({"info": {"status": Status.RUNNING.value}})
                    if logger:
                        logger._log_configs(cfg)
                    if seeding_function:
                        try:
                            assert "seed" in cfg.config.keys()
                        except AssertionError:
                            msg = "Missing field: The 'config' must contain a field named 'seed'\n"
                            msg += "provided as argument to the function 'seeding_function' "
                            raise MissingFieldError(msg)
                        seeding_function(cfg.config.seed)

                    ctx = Context(config=cfg.config, mlxp=cfg.mlxp, info=cfg.info, logger=logger)
                    task_function(ctx)
                    now = datetime.now()
                    info = {
                        "end_date": now.strftime("%d/%m/%Y"),
                        "end_time": now.strftime("%H:%M:%S"),
                        "status": Status.COMPLETE.value,
                    }

                    cfg.update({"info": info})

                    if logger:
                        logger._log_configs(cfg)

                    _reset_work_dir(cur_dir)
                    return None
                except Exception:
                    now = datetime.now()
                    info = {
                        "end_date": now.strftime("%d/%m/%Y"),
                        "end_time": now.strftime("%H:%M:%S"),
                        "status": Status.FAILED.value,
                    }

                    cfg.update({"info": info})

                    if logger:
                        logger._log_configs(cfg)

                    _reset_work_dir(cur_dir)
                    raise

        decorated_task.__code__ = decorated_task.__code__.replace(
            co_filename=task_function.__code__.co_filename
        )

        return decorated_task

    def composed_decorator(task_function: TaskFunction) -> Callable[[], None]:
        decorated_task = launcher_decorator(task_function)
        task_function = hydra_decorator(decorated_task)

        return task_function

    return composed_decorator


@dataclass
class Context:
    """The contex object passed to the decorated function when using decorator
    mlxp.launch.

    .. py:attribute:: config
        :type: ConfigDict

        A structure containing project-specific options provided by the user.
        These options are loaded from a yaml file 'config.yaml' contained in the directory 'config_path'
        provided as argument to the decorator mlxp.launch. It's content can be overriden from the command line.

    .. py:attribute:: mlxp
        :type: ConfigDict

        A structure containing MLXP's default settings for the project.
        Its content is loaded from a yaml file 'mlxp.yaml' located in the same directory 'config.yaml'.

    .. py:attribute:: info
        :type: ConfigDict

        A structure containing information about the current run: ex. status, start time, hostname, etc.

    .. py:attribute:: logger
        :type: Union[Logger,None]

        A logger object that can be used for logging variables (metrics, checkpoints, artifacts).
        When logging is enabled, these variables are all stored in a uniquely defined directory.
    """

    config: ConfigDict = None
    mlxp: ConfigDict = None
    info: ConfigDict = None
    logger: Union[Logger, None] = None


T = TypeVar("T")


def instance_from_dict(class_name: str, arguments: Dict[str, Any], module: Any = mlxp) -> T:
    """Create an instance of a class based on a dictionary of arguments.

    :param class_name: The name of the class
    :param arguments: A dictionary of arguments to the class constructor
    :type class_name: str
    :type arguments: Dict[str,Any]
    :return: An instance of a class 'class_name' constructed using the arguments in
        'arguments'.
    :rtype: T
    """
    attr = _import_module(class_name, module)
    if arguments:
        attr = attr(**arguments)
    else:
        attr = attr()

    return attr


def _import_module(module_name, main_module):
    module, attr = os.path.splitext(module_name)
    if not attr:
        return getattr(main_module, module)
    else:
        try:
            module = importlib.import_module(module)
            return getattr(module, attr[1:])
        except BaseException:
            try:
                module = _import_module(module)
                return getattr(module, attr[1:])
            except BaseException:
                return eval(module + attr[1:])


def _instance_from_config(config, module=mlxp):
    config_module_name = "name"
    config = copy.deepcopy(config)
    module_name = config.pop(config_module_name)

    return instance_from_dict(module_name, config, module=module)


def _set_work_dir(work_dir):
    os.chdir(work_dir)
    sys.path.insert(0, work_dir)


def _reset_work_dir(cur_dir):
    os.chdir(cur_dir)
    sys.path = sys.path[1:]


def _get_mlxp_configs(log_dir):
    from mlxp.enumerations import Directories

    abs_name = os.path.join(log_dir, Directories.Metadata.value, "info.yaml")
    configs_info = {}

    if os.path.isfile(abs_name):
        with open(abs_name, "r") as file:
            configs = yaml.safe_load(file)
            if "scheduler" in configs:
                configs_info.update({"scheduler": configs["scheduler"]})
            if "version_manager" in configs:
                configs_info.update({"version_manager": configs["version_manager"]})
            if "logger" in configs:
                configs_info.update({"logger": configs["logger"]})

    return configs_info


def _get_configs(log_dir):
    from mlxp.enumerations import Directories

    abs_name = os.path.join(log_dir, Directories.Metadata.value, "config.yaml")
    configs = {}

    if os.path.isfile(abs_name):
        with open(abs_name, "r") as file:
            configs = yaml.safe_load(file)

    return configs


def _main_job_command(executable, current_file_path, work_dir, parent_log_dir, job_id):
    exec_file = os.path.relpath(current_file_path, os.getcwd())

    args = _get_overrides()
    values = [
        f"cd {work_dir}",
        f"{executable} {exec_file} {args} \
            +mlxp.logger.forced_log_id={job_id}\
            +mlxp.logger.parent_log_dir={parent_log_dir} \
            +mlxp.use_scheduler={False}\
            +mlxp.use_version_manager={False}\
            +mlxp.interactive_mode={False}",
    ]

    values = [f"{val}\n" for val in values]
    return "".join(values)


def _get_overrides():
    hydra_cfg = HydraConfig.get()
    overrides = hydra_cfg.overrides.task

    def filter_fn(x):
        return (
            ("version_manager" not in x)
            and ("scheduler" not in x)
            and ("logger.parent_log_dir" not in x)
            and ("logger.forced_log_id" not in x)
            and ("interactive_mode" not in x)
        )

    filtered_args = list(filter(filter_fn, overrides))
    args = " ".join(filtered_args)
    return args
