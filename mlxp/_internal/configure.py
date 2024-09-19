import os
from copy import deepcopy

import omegaconf
import yaml
from omegaconf import OmegaConf

from mlxp._internal._interactive_mode import InteractiveModeHandler, _bcolors, _printc
from mlxp.data_structures.schemas import Metadata
from mlxp.errors import InvalidConfigFileError
from mlxp.mlxpsub import scheduler_env_var


def _update_scheduler_config(mlxp_config):
    if scheduler_env_var in os.environ:
        variable_value = os.environ[scheduler_env_var]
        with open(variable_value, "r") as file:
            scheduler_config = OmegaConf.create({"mlxp": yaml.safe_load(file)})
        mlxp_config = OmegaConf.merge(mlxp_config, scheduler_config)

    return mlxp_config


def _update_config(default_cfg, overrides_config, overrides_mlxp):
    info_cfg = OmegaConf.create({"info": default_cfg.info})
    mlxp_cfg = OmegaConf.create({"mlxp": default_cfg.mlxp})
    config = default_cfg.config
    if overrides_mlxp:
        mlxp_cfg = OmegaConf.merge(mlxp_cfg, overrides_mlxp)

    return overrides_config, mlxp_cfg, info_cfg


def _build_config(config_path, config_name, co_filename, overrides, interactive_mode_file):
    config_path = _process_config_path(config_path, co_filename)

    os.makedirs(config_path, exist_ok=True)
    custom_config_file = os.path.join(config_path, config_name + ".yaml")
    if not os.path.exists(custom_config_file):
        with open(custom_config_file, "w"):
            pass
    default_cfg = _get_default_config(config_path)

    mlxp_file = os.path.join(config_path, "mlxp.yaml")
    if not os.path.exists(mlxp_file):
        _save_mlxp_file(default_cfg.mlxp, mlxp_file)

    overrides_mlxp, overrides_config = _process_overrides(overrides)

    # Override default configs
    config, mlxp_cfg, info_cfg = _update_config(default_cfg, overrides_config, overrides_mlxp)

    mlxp_cfg = _update_scheduler_config(mlxp_cfg)
    _update_default_directories(mlxp_cfg.mlxp, co_filename)
    im_handler = InteractiveModeHandler(mlxp_cfg.mlxp.interactive_mode, interactive_mode_file)

    return config, mlxp_cfg, info_cfg, im_handler


def _process_overrides(overrides):

    if "mlxp" in overrides:
        # overrides_mlxp = OmegaConf.to_container(cfg.hydra.overrides.task, resolve=False)
        overrides_mlxp = OmegaConf.create({"mlxp": overrides.mlxp})
    #        cfg = OmegaConf.merge(cfg, overrides_mlxp)
    else:
        overrides_mlxp = None

    omegaconf.OmegaConf.set_struct(overrides, True)
    with omegaconf.open_dict(overrides):
        overrides.pop("mlxp")
    omegaconf.OmegaConf.set_struct(overrides, False)

    return overrides_mlxp, overrides


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


def _get_default_config(config_path):
    default_config = OmegaConf.structured(Metadata)
    conf_dict = OmegaConf.to_container(default_config, resolve=True)
    default_config = OmegaConf.create(conf_dict)

    os.makedirs(config_path, exist_ok=True)
    mlxp_file = os.path.join(config_path, "mlxp.yaml")

    if os.path.exists(mlxp_file):
        mlxp_config = _get_mlxp_configs(mlxp_file, default_config["mlxp"])
        default_config = OmegaConf.merge(default_config, mlxp_config)

    return default_config


def _save_mlxp_file(mlxp_conf, mlxp_file):

    omegaconf.OmegaConf.save(config=mlxp_conf, f=mlxp_file)
    _printc(
        _bcolors.OKBLUE, f"Default settings for mlxp are saved in {mlxp_file} ",
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
