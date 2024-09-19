"""The launcher allows launching multiple experiments on a cluster using hydra."""

import atexit
import functools
import importlib
import os
import signal
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import omegaconf
import yaml
from hydra import version
from hydra._internal.utils import _run_hydra, get_args_parser
from hydra.core.hydra_config import HydraConfig
from hydra.types import TaskFunction
from omegaconf import DictConfig, OmegaConf

from mlxp._internal.configure import _build_config, _process_config_path
from mlxp.data_structures.config_dict import ConfigDict, convert_dict
from mlxp.enumerations import Status
from mlxp.errors import InvalidSchedulerError, MissingFieldError
from mlxp.logger import Logger
from mlxp.enumerations import Directories
from mlxp.scheduler import Schedulers_dict, _create_scheduler
import warnings
warnings.filterwarnings('ignore', module='hydra')



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


def _clean_dir_on_exit(signum, frame):
    _clean_dir()
    exit(0)




atexit.register(_clean_dir)
signal.signal(signal.SIGTERM, _clean_dir_on_exit)


def launch(
    config_path: str = "configs", seeding_function: Union[Callable[[Any], None], None] = None,
) -> Callable[[TaskFunction], Any]:
    """Create a decorator of the main function to be executed.
    :samp:`launch` allows composing configurations from multiple configuration files
    by leveraging hydra (see hydra-core package).
    This function behaves similarly to :samp:`hydra.main` provided in the hydra-core package:
    https://github.com/facebookresearch/hydra/blob/main/hydra/main.py.
    It expects a path to a configuration file named :samp:`config.yaml`
    contained in the directory :samp:`config_path` and returns a decorator.
    The returned decorator expects functions with the following signature: :samp:`main(ctx: mlxp.Context)`.

    :example:

    .. code-block:: python

        import mlxp

        @mlxp.launch(config_path='configs',
                     seeding_function=set_seeds)
        def main(ctx: mlxp.Context)->None:

            print(ctx.config)

        if __name__ == "__main__":
            main()

    Runing the above python code will create an object :samp:`ctx` of type :samp:`mlxp.Context` on the fly
    and provide it to the function :samp:`main`. Such object stores information about the run.
    In particular, the field :samp:`ctx.config` stores the options contained in the config file 'config.yaml'.
    Additionally, :samp:`ctx.logger`, provides a logger object of the class :samp:`mlxp.Logger` for logging results of the run.
    Just like in hydra, it is also possible to override the configs from the command line and
    to sweep over multiple values of a given configuration when executing python code.
    See: https://hydra.cc/docs/intro/ for complete documentation on how to use Hydra.

    This function is necessary to enable MLXP's functionalities including:
        1. Multiple submissions to a cluster queue using :samp:`mlxpsub`
        2. Job versioning: Creating a 'safe' working directory from which jobs are executed when submitted to a cluster queue, to ensure each job was executed with a specific version of the code.

    :param config_path: The config path, a directory where the default user configuration and MLXP settings are stored.
    :param seeding_function:  A callable for setting the seed of random number generators. It is called with the seed option in 'ctx.config.seed' passed to it.
    :type config_path: str (default './configs')
    :type seeding_function: Union[Callable[[Any], None],None] (default None)
    :return: A decorator of the main function to be executed.
    :type: Callable[[TaskFunction], Any]

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


            if cfg_passthrough is None:
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
            else:
                return task_function(cfg_passthrough)


        return decorated_main

    def launcher_decorator(task_function):
        @functools.wraps(task_function)
        def decorated_task(overrides):
            co_filename = task_function.__code__.co_filename

            config, mlxp_cfg, info_cfg, im_handler = _build_config(
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
            OmegaConf.update(info_cfg, "info", info, merge=True)
            if mlxp_cfg.mlxp.use_version_manager:
                version_manager = instantiate(mlxp_cfg.mlxp.version_manager.pop("name"))(
                    **mlxp_cfg.mlxp.version_manager
                )
                version_manager._set_im_handler(im_handler)
                work_dir = version_manager.make_working_directory()
                # cfg.update({"info": {"version_manager": version_manager.get_info()}})
                OmegaConf.update(
                    info_cfg, "info", {"version_manager": version_manager.get_info()}, merge=True
                )
            else:
                work_dir = os.getcwd()

            # cfg.update({"info": {"work_dir": work_dir}})
            OmegaConf.update(info_cfg, "info", {"work_dir": work_dir}, merge=True)

            if mlxp_cfg.mlxp.use_scheduler:
                try:
                    scheduler_key = mlxp_cfg.mlxp.scheduler.pop("name")
                    assert scheduler_key in Schedulers_dict
                    _create_scheduler(Schedulers_dict[scheduler_key])
                    class_name = "mlxp.scheduler." + Schedulers_dict[scheduler_key]["name"]
                    scheduler = instantiate(class_name)(**mlxp_cfg.mlxp.scheduler)
                    if not mlxp_cfg.mlxp.use_logger:
                        print("Logger is currently disabled.")
                        print("To use the scheduler, the logger must be enabled")
                        print("Enabling the logger...")
                        OmegaConf.update(mlxp_cfg, "mlxp", {"use_logger": True}, merge=True)
                        # mlxp_cfg.mlxp.use_logger = True
                except AssertionError:
                    error_msg = scheduler_key + " does not correspond to any supported scheduler\n"
                    error_msg += f"Supported schedulers are {list(Schedulers_dict.keys())}"
                    raise InvalidSchedulerError(error_msg) from None
                    # scheduler = None
                    # cfg.mlxp.use_scheduler = False
            else:
                scheduler = None

            if mlxp_cfg.mlxp.use_logger:
                logger = instantiate(mlxp_cfg.mlxp.logger.pop("name"))(**mlxp_cfg.mlxp.logger)
                log_id = logger.log_id
                log_dir = logger.log_dir
                parent_log_dir = logger.parent_log_dir
                OmegaConf.update(info_cfg, "info", {"logger": logger.get_info()}, merge=True)
            else:
                logger = None

            if mlxp_cfg.mlxp.use_scheduler:
                main_cmd = _main_job_command(
                    info_cfg.info.executable,
                    info_cfg.info.current_file_path,
                    work_dir,
                    parent_log_dir,
                    log_id,
                )

                scheduler.submit_job(main_cmd, log_dir)
                OmegaConf.update(info_cfg, "info", {"scheduler": scheduler.get_info()}, merge=True)
                logger._log_configs(config, "config_unresolved", resolve=False)
                logger._log_configs(info_cfg.info, "info")

            else:
                # ## Setting up the working directory
                cur_dir = os.getcwd()
                _set_work_dir(work_dir)
                OmegaConf.update(info_cfg, "info", {"status": Status.RUNNING.value}, merge=True)

                if logger:
                    # cfg.update({"info": _get_mlxp_configs(log_dir)})
                    OmegaConf.update(info_cfg, "info", _get_mlxp_configs(log_dir), merge=True)
                    logger._log_configs(config)
                    logger._log_configs(info_cfg.info, "info")

                try:

                    # cfg.update({"info": {"status": Status.RUNNING.value}})

                    if seeding_function:
                        try:
                            assert "seed" in config.keys()
                        except AssertionError:
                            msg = "Missing field: The 'config' must contain a field named 'seed'\n"
                            msg += "provided as argument to the function 'seeding_function' "
                            raise MissingFieldError(msg)
                        seeding_function(config.seed)
                    # if mlxp_cfg.mlxp.config_read_only:
                    #     OmegaConf.set_readonly(config, True)
                    # else:
                    #     OmegaConf.set_readonly(config, False)

                    if mlxp_cfg.mlxp.resolve:
                        OmegaConf.resolve(config)

                    if mlxp_cfg.mlxp.as_ConfigDict:
                        config = convert_dict(
                            config, src_class=omegaconf.dictconfig.DictConfig, dst_class=ConfigDict
                        )

                    ctx = Context(config=config, mlxp=mlxp_cfg, info=info_cfg, logger=logger)

                    task_function(ctx)
                    now = datetime.now()
                    info = {
                        "end_date": now.strftime("%d/%m/%Y"),
                        "end_time": now.strftime("%H:%M:%S"),
                        "status": Status.COMPLETE.value,
                    }
                    OmegaConf.update(info_cfg, "info", info, merge=True)
                    if logger:
                        logger._log_configs(info_cfg.info, "info")

                    _reset_work_dir(cur_dir)
                    return None
                except Exception:
                    now = datetime.now()
                    info = {
                        "end_date": now.strftime("%d/%m/%Y"),
                        "end_time": now.strftime("%H:%M:%S"),
                        "status": Status.FAILED.value,
                    }
                    OmegaConf.update(info_cfg, "info", info, merge=True)
                    if logger:
                        logger._log_configs(info_cfg.info, "info")

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
        provided as argument to the decorator mlxp.launch.
        It's content can be overriden from the command line.

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

    # config: ConfigDict = None
    # mlxp: ConfigDict = None
    # info: ConfigDict = None
    config: DictConfig = None
    mlxp: DictConfig = None
    info: DictConfig = None
    logger: Union[Logger, None] = None


T = TypeVar("T")


def instance_from_dict(class_name: str, arguments: Dict[str, Any]) -> T:
    """Create an instance of a class based on a dictionary of arguments.

    :param class_name: The name of the class
    :param arguments: A dictionary of arguments to the class constructor
    :type class_name: str
    :type arguments: Dict[str,Any]
    :return: An instance of a class 'class_name' constructed using the arguments in
        'arguments'.
    :rtype: T
    """

    return instantiate(class_name)(**arguments)


def instantiate(class_name: str) -> T:
    """Dynamically imports a module and retrieves a class or function in it by name.

    Given the fully qualified name of a class or function (in the form 'module.submodule.ClassName' or
    'module.submodule.function_name'), this function imports the module and returns a handle to the class
    or function.

    :param class_name: The fully qualified name of the class or function to retrieve.
                       This should include the module path and the name,
                       e.g., 'module.submodule.ClassName' or 'module.submodule.function_name'.
    :type class_name: str

    :return: A handle (reference) to the class or function specified by `class_name`.
    :rtype: Type or Callable

    :raises ImportError: If the module cannot be imported.
    :raises AttributeError: If the class or function cannot be found in the module.
    :raises NameError: If the name cannot be evaluated after attempts to retrieve it.

    Example:
    --------
    >>> MyClass = instantiate('my_module.MyClass')
    >>> my_instance = MyClass()
    >>> my_function = instantiate('my_module.my_function')
    >>> result = my_function()
    """

    # Split the module and the class/function name
    module_name, attr = os.path.splitext(class_name)

    # Ensure the attribute name doesn't start with a dot
    attr = attr.lstrip(".")

    try:
        # Import the module dynamically
        module = importlib.import_module(module_name)

        # Try to get the attribute (class or function)
        return getattr(module, attr)

    except ImportError as error:
        raise ImportError(f"Could not be import '{module_name}' ") from error

    except AttributeError as error:
        raise AttributeError(f"'{attr}' not found in '{module_name}'.") from error


def _set_work_dir(work_dir):
    os.chdir(work_dir)
    sys.path.insert(0, work_dir)


def _reset_work_dir(cur_dir):
    os.chdir(cur_dir)
    sys.path = sys.path[1:]


def _get_mlxp_configs(log_dir):

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
    

    abs_name = os.path.join(log_dir, Directories.Metadata.value, "config.yaml")
    configs = {}

    if os.path.isfile(abs_name):
        with open(abs_name, "r") as file:
            configs = yaml.safe_load(file)
    configs = OmegaConf.create(configs)
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

    def filter_fn(config_dict):
        return (
            ("version_manager" not in config_dict)
            and ("scheduler" not in config_dict)
            and ("logger.parent_log_dir" not in config_dict)
            and ("logger.forced_log_id" not in config_dict)
            and ("interactive_mode" not in config_dict)
        )

    filtered_args = list(filter(filter_fn, overrides))
    args = " ".join(filtered_args)
    return args
