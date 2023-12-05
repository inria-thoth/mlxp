import os

import omegaconf
import yaml
from omegaconf import OmegaConf

from mlxp._internal._interactive_mode import _bcolors, _printc, InteractiveModeHandler
from mlxp.data_structures.config_dict import ConfigDict, convert_dict
from mlxp.data_structures.schemas import Metadata
from mlxp.enumerations import DefaultSchedulers
from mlxp.scheduler import Scheduler
from copy import deepcopy

def _configure_scheduler(mlxp_config):
    while True:
        print("You can either choose one of the job schedulers available by default, ")

        print(
            f"or define a custom one by inheriting from the abstract class {Scheduler} (see documentation)  "
        )

        _printc(
            _bcolors.OKBLUE,
            "For setting a default scheduler, you can choose from this list:",
        )
        _printc(_bcolors.FAIL, f"{[member.value for member in DefaultSchedulers]}")
        _printc(
            _bcolors.OKBLUE,
            "For a custom scheduler, you must provide the full name of the user-defined subclass of the Scheduler class (ex. my_app.CustomScheduler).",
        )

        files_input = input(
            f"{_bcolors.OKGREEN} Please enter your choice (or hit Enter to skip) :{_bcolors.ENDC}"
        )
        if files_input:
            is_valid = _update_scheduler_name(mlxp_config,files_input)
            if is_valid:
                break
            else:
                _printc(
                    _bcolors.OKBLUE,
                    f" {files_input} is not a valid class identifier. Please try again  ",
                )
        else:
            break


def _update_scheduler_name(mlxp_config,scheduler_name):
    names = scheduler_name.strip().rsplit(".", 1)
    is_valid = True
    for name in names:
        if not name.isidentifier():
            is_valid = False
    if is_valid:
        omegaconf.OmegaConf.set_struct(mlxp_config, True)
        with omegaconf.open_dict(mlxp_config):
            mlxp_config.mlxp.scheduler.name = scheduler_name
        omegaconf.OmegaConf.set_struct(mlxp_config, False)
        _printc(_bcolors.OKBLUE, f" Setting Scheduler to {scheduler_name} ")
    return is_valid


def _ask_configure_scheduler_override(mlxp_config,scheduler_name):
    while True:
        _printc(
            _bcolors.OKGREEN,
            "The current job(s) will be launched using "+scheduler_name+" as a scheduler. Would you like to set it as a default ?  (y/n):",
        )
        print(
            f"{_bcolors.OKGREEN}y{_bcolors.ENDC}: The job scheduler configs will be stored in the mlxp config file"
        )
        choice = input(f"{_bcolors.OKGREEN}Please enter you answer (y/n):{_bcolors.ENDC}")

        if choice == "y":
            is_valid = _update_scheduler_name(mlxp_config,scheduler_name)
            if not is_valid:
                _printc(
                    _bcolors.OKBLUE,
                    f" {scheduler_name} is not a valid class identifier.",
                )
                _printc(_bcolors.OKBLUE, "No scheduler will be selected by default.")
            break
        elif choice == "n":
            _printc(_bcolors.OKBLUE, "No scheduler will be selected by default.")
            _printc(
                _bcolors.OKBLUE,
                "To use a scheduler, you will need to select one later.",
            )
            break
        else:
            _printc(_bcolors.OKBLUE, "Invalid choice. Please try again. (y/n)")



def _ask_configure_scheduler(mlxp_config):
    while True:
        _printc(
            _bcolors.OKGREEN,
            " Would you like to select a default job scheduler now ?  (y/n):",
        )
        print(
            f"{_bcolors.OKGREEN}y{_bcolors.ENDC}: The job scheduler configs will be stored in the mlxp config file"
        )

        choice = input(f"{_bcolors.OKGREEN}Please enter you answer (y/n):{_bcolors.ENDC}")

        if choice == "y":
            _configure_scheduler(mlxp_config)
            break
        elif choice == "n":
            _printc(_bcolors.OKBLUE, "No scheduler will be selected by default.")
            _printc(
                _bcolors.OKBLUE,
                "To use a scheduler, you will need to select one later.",
            )
            break
        else:
            _printc(_bcolors.OKBLUE, "Invalid choice. Please try again. (y/n)")

def _update_config(default_cfg, overrides_config, overrides_mlxp):

    if overrides_mlxp:
        cfg = OmegaConf.merge(default_cfg, overrides_mlxp)
    else:
        cfg = deepcopy(default_cfg)

    cfg = OmegaConf.merge(cfg, overrides_config) 

    return cfg


def _build_config(config_path, config_name, co_filename, overrides, interactive_mode_file):
    config_path = _process_config_path(config_path, co_filename)

    os.makedirs(config_path, exist_ok=True)
    custom_config_file = os.path.join(config_path, config_name + ".yaml")
    if not os.path.exists(custom_config_file):
        with open(custom_config_file, "w"):
            pass

    overrides_mlxp, overrides_config = _process_overrides(overrides)

    default_cfg = _get_default_config(config_path, overrides_mlxp)
    # Override default configs
    cfg = _update_config(default_cfg, overrides_config, overrides_mlxp)

    im_handler = InteractiveModeHandler(cfg["mlxp"]["interactive_mode"], interactive_mode_file)


    update_default_config = _set_scheduler(default_cfg, overrides_mlxp["mlxp"],im_handler)

    mlxp_file = os.path.join(config_path, "mlxp.yaml")
    if not os.path.exists(mlxp_file) or update_default_config:
        _save_mlxp_file(default_cfg,mlxp_file)

    cfg = _update_config(default_cfg, overrides_config, overrides_mlxp)
    cfg = convert_dict(cfg, src_class=omegaconf.dictconfig.DictConfig, dst_class=ConfigDict)
    _update_default_directories(cfg.mlxp, co_filename)

    return cfg, im_handler


def _process_overrides(overrides):
    if "mlxp" in overrides:
        overrides_mlxp = OmegaConf.create({"mlxp": overrides["mlxp"]})
    #        cfg = OmegaConf.merge(cfg, overrides_mlxp)
    else:
        overrides_mlxp = None

    overrides = convert_dict(overrides, src_class=omegaconf.dictconfig.DictConfig, dst_class=dict)
    if "mlxp" in overrides:
        overrides.pop("mlxp")
    overrides = convert_dict(overrides, src_class=dict, dst_class=omegaconf.dictconfig.DictConfig)

    overrides_config = OmegaConf.create({"config": overrides})

    return overrides_mlxp, overrides_config


def _get_mlxp_configs(mlxp_file, default_config_mlxp):
    with open(mlxp_file, "r") as file:
        mlxp_config = OmegaConf.create({"mlxp": yaml.safe_load(file)})
    valid_keys = list(default_config_mlxp.keys())
    for key in mlxp_config["mlxp"].keys():
        try:
            assert key in valid_keys
        except AssertionError:
            msg = f"The following mlxp file is corrupted: {mlxp_file},"
            msg += f"It contains an invalid field: {key}\n"
            msg += f"Valid fields are {valid_keys}\n"
            raise InvalidConfigFileError(msg) from None

    return mlxp_config


def _set_scheduler(default_config, overrides,im_handler):
    scheduler_settings = _get_scheduler_settings(default_config, overrides)
    scheduler_name, scheduler_name_default, using_scheduler, interactive_mode = scheduler_settings
    update_default_config = False
    

    if scheduler_name_default == "NoScheduler" and using_scheduler:
        _printc(_bcolors.OKBLUE, "No default scheduler is configured")
        if im_handler._interactive_mode:
            is_scheduler_selected = im_handler.get_im_choice("scheduler_config")
            if not is_scheduler_selected:
                if scheduler_name == "NoScheduler":
                    _ask_configure_scheduler(default_config)
                else:
                    _ask_configure_scheduler_override(default_config,scheduler_name)
                im_handler.set_im_choice("scheduler_config",True)
                im_handler._save_im_choice()
                update_default_config = True
    return update_default_config


def _get_scheduler_settings(default_config, overrides):
    using_scheduler = default_config.mlxp.use_scheduler
    scheduler_name_default = default_config.mlxp.scheduler.name
    scheduler_name = scheduler_name_default
    interactive_mode = default_config.mlxp.interactive_mode
    if overrides:
        if "use_scheduler" in overrides:
            using_scheduler = overrides["use_scheduler"]
        if "scheduler" in overrides:
            if "name" in overrides["scheduler"]:
                scheduler_name = overrides["scheduler"]
        if "interactive_mode" in overrides:
            interactive_mode = overrides["interactive_mode"]
    return scheduler_name, scheduler_name_default, using_scheduler, interactive_mode


def _get_default_config(config_path, overrides_mlxp):
    default_config = OmegaConf.structured(Metadata)
    conf_dict = OmegaConf.to_container(default_config, resolve=True)
    default_config = OmegaConf.create(conf_dict)

    os.makedirs(config_path, exist_ok=True)
    mlxp_file = os.path.join(config_path, "mlxp.yaml")

    if os.path.exists(mlxp_file):
        mlxp_config = _get_mlxp_configs(mlxp_file, default_config["mlxp"])
        default_config = OmegaConf.merge(default_config, mlxp_config)
    else:
        # if no mlxp file, set the overrides as default 
        default_config = OmegaConf.merge(default_config, overrides_mlxp)

    # default_config are either loaded from the default config file 
    # or from the internal defaults of mlxp
    return default_config


def _save_mlxp_file(default_config,mlxp_file):
    
    mlxp_conf = OmegaConf.create(default_config["mlxp"])
    omegaconf.OmegaConf.save(config=mlxp_conf, f=mlxp_file)
    _printc(
        _bcolors.OKBLUE,
        f"Default settings for mlxp are saved in {mlxp_file} ",
    )


def _update_default_directories(mlxp_configs, run_file_name):
    parent_log_dir = _process_config_path(mlxp_configs.logger.parent_log_dir, run_file_name)
    mlxp_configs.logger.parent_log_dir = parent_log_dir

    parent_log_dir = _process_config_path(mlxp_configs.version_manager.parent_work_dir, run_file_name)
    mlxp_configs.version_manager.parent_work_dir = parent_log_dir


def _process_config_path(config_path, file_name):
    if os.path.isabs(config_path):
        return config_path
    else:
        abs_path = os.path.abspath(config_path)
        rel_path = os.path.relpath(abs_path, os.getcwd())
        return os.path.join(os.path.dirname(file_name), rel_path)
