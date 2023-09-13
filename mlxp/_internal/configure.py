import os

import omegaconf
import yaml
from omegaconf import OmegaConf

from mlxp._internal._interactive_mode import _bcolors, _printc
from mlxp.data_structures.config_dict import ConfigDict, convert_dict
from mlxp.data_structures.schemas import Metadata
from mlxp.enumerations import DefaultSchedulers
from mlxp.scheduler import Scheduler


def _configure_scheduler(mlxp_config):
    while True:
        print("You can either choose one of the job schedulers available by default, ")

        print(
            f"or define a custom one by inheriting from the abstract class {Scheduler} (see documentation)  "
        )

        _printc(
            _bcolors.OKBLUE, "For a default scheduler, you can choose one from this list:",
        )
        _printc(_bcolors.FAIL, f"{[member.value for member in DefaultSchedulers]}")
        _printc(
            _bcolors.OKBLUE,
            "For a custom scheduler, you must provide the full name of the user-defined Scheduler subclass (ex. my_app.CustomScheduler).",
        )

        files_input = input(
            f"{_bcolors.OKGREEN} Please enter your choice (or hit Enter to skip) :{_bcolors.ENDC}"
        )
        if files_input:
            names = files_input.strip().rsplit(".", 1)
            is_valid = True
            for name in names:
                if not name.isidentifier():
                    is_valid = False
            if is_valid:
                omegaconf.OmegaConf.set_struct(mlxp_config, True)
                with omegaconf.open_dict(mlxp_config):
                    mlxp_config.mlxp.scheduler.name = files_input
                omegaconf.OmegaConf.set_struct(mlxp_config, False)
                _printc(_bcolors.OKBLUE, f" Setting Scheduler to {files_input} ")
                break
            else:
                _printc(
                    _bcolors.OKBLUE, f" {files_input} is not a valid class identifier. Please try again  ",
                )
        else:
            break


def _ask_configure_scheduler(mlxp_config, mlxp_file):
    while True:

        _printc(
            _bcolors.OKGREEN, " Would you like to select a default job scheduler now ?  (y/n):",
        )
        print(
            f"{_bcolors.OKGREEN}y{_bcolors.ENDC}: The job scheduler configs will be stored in the file {mlxp_file}"
        )
        print(f"{_bcolors.OKGREEN}n{_bcolors.ENDC}: No scheduler will be selected by default.")

        choice = input(f"{_bcolors.OKGREEN}Please enter you answer (y/n):{_bcolors.ENDC}")

        if choice == "y":
            _configure_scheduler(mlxp_config)
            break
        elif choice == "n":

            _printc(_bcolors.OKBLUE, "No scheduler will be selected by default.")
            _printc(
                _bcolors.OKBLUE, "To use a scheduler, you will need to select one later.",
            )
            break
        else:
            _printc(_bcolors.OKBLUE, "Invalid choice. Please try again. (y/n)")


def _build_config(overrides, config_path, config_name):

    os.makedirs(config_path, exist_ok=True)
    custom_config_file = os.path.join(config_path, config_name + ".yaml")
    if not os.path.exists(custom_config_file):
        with open(custom_config_file, "w"):
            pass

    overrides_mlxp, overrides_config = _process_overrides(overrides)

    cfg = _get_default_config(config_path, overrides_mlxp)

    cfg = OmegaConf.merge(cfg, overrides_config)

    cfg = convert_dict(cfg, src_class=omegaconf.dictconfig.DictConfig, dst_class=ConfigDict)

    return cfg


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


def _get_mlxp_configs(mlxp_file, default_config):

    with open(mlxp_file, "r") as file:
        mlxp_config = OmegaConf.create({"mlxp": yaml.safe_load(file)})
    valid_keys = list(default_config["mlxp"].keys())
    for key in mlxp_config["mlxp"].keys():
        try:
            assert key in valid_keys
        except AssertionError:
            msg = f"In the file {mlxp_file},"
            msg += f"the following field is invalid: {key}\n"
            msg += f"Valid fields are {valid_keys}\n"
            raise AssertionError(msg)

    return mlxp_config


def _set_scheduler(default_config, overrides, mlxp_file):

    scheduler_settings = _get_scheduler_settings(default_config, overrides, mlxp_file)
    scheduler_name, scheduler_name_default, using_scheduler, interactive_mode = scheduler_settings
    update_default_conifg = False
    if scheduler_name == "NoScheduler":
        if using_scheduler:
            _printc(_bcolors.OKBLUE, "No scheduler is configured by default ")
            if interactive_mode:
                _printc(_bcolors.OKBLUE, "Entering interactive mode ")
                _ask_configure_scheduler(default_config, mlxp_file)
                _printc(_bcolors.OKBLUE, "Leaving interactive mode ")
                update_default_conifg = True
            else:
                pass
    else:
        omegaconf.OmegaConf.set_struct(default_config, True)
        with omegaconf.open_dict(default_config):
            default_config.mlxp.scheduler.name = scheduler_name
        omegaconf.OmegaConf.set_struct(default_config, False)
        if scheduler_name_default == "NoScheduler":
            update_default_conifg = True
            _printc(_bcolors.OKBLUE, f"Setting Scheduler to: {scheduler_name} ")
    return update_default_conifg


def _get_scheduler_settings(default_config, overrides, mlxp_file):

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
    using_scheduler = using_scheduler or not os.path.exists(mlxp_file)
    return scheduler_name, scheduler_name_default, using_scheduler, interactive_mode


def _get_default_config(config_path, overrides):
    default_config = OmegaConf.structured(Metadata)
    conf_dict = OmegaConf.to_container(default_config, resolve=True)
    default_config = OmegaConf.create(conf_dict)

    os.makedirs(config_path, exist_ok=True)
    mlxp_file = os.path.join(config_path, "mlxp.yaml")

    if os.path.exists(mlxp_file):
        mlxp_config = _get_mlxp_configs(mlxp_file, default_config)
        default_config = OmegaConf.merge(default_config, mlxp_config)

    update_default_conifg = _set_scheduler(default_config, overrides, mlxp_file)

    if not os.path.exists(mlxp_file) or update_default_conifg:
        _printc(
            _bcolors.OKBLUE, f"Default settings for mlxp will be created in {mlxp_file} ",
        )
        mlxp = OmegaConf.create(default_config["mlxp"])
        omegaconf.OmegaConf.save(config=mlxp, f=mlxp_file)
    if overrides:
        default_config = OmegaConf.merge(default_config, overrides)
    return default_config


def _process_config_path(config_path, file_name):
    if os.path.isabs(config_path):
        return config_path
    else:
        abs_path = os.path.abspath(config_path)
        rel_path = os.path.relpath(abs_path, os.getcwd())
        return os.path.join(os.path.dirname(file_name), rel_path)
