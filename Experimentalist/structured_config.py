import hydra
from hydra.core.config_store import ConfigStore
from dataclasses import dataclass, field
from omegaconf import MISSING
from omegaconf import OmegaConf
from typing import Any, Callable, List, Optional


@dataclass
class Cluster: 
    engine: str=""
    cleanup_cmd: str=""  
    cmd: list=field(default_factory=lambda:[])

@dataclass
class OAR(Cluster):
    engine: str="OAR"

@dataclass
class SLURM(Cluster):
    engine: str="SLURM"

@dataclass
class System:
    user: str='${oc.env:USER}'
#    account: str='${oc.env:ACCOUNT}'
    env: str="conda activate '${oc.env:CONDA_DEFAULT_ENV}'"
    shell_path: str="/bin/bash"
    shell_config_path: str="~/.bashrc"
    cmd: str=MISSING
    app: str=MISSING
    isBatchJob: bool=False
    hostname: str=MISSING
    process_id: int=MISSING
    date: Any=MISSING
    time: Any=MISSING

@dataclass
class Logs:
    log_dir: str='data/outputs'
    log_name: str='logs'
    log_to_file: bool= False
    log_id: Any= None
    path: str=MISSING

@dataclass
class Config:
    system: System=System()
    logs: Logs=Logs()
    cluster: Cluster=Cluster() 

def create_from_structured_config(StructuredConfig):
    conf= OmegaConf.structured(StructuredConfig)
    conf_dict = OmegaConf.to_container(conf, resolve=True)
    return OmegaConf.create(conf_dict)


def format_config(cfg):
    base_conf = create_from_structured_config(Config)
    return  OmegaConf.merge(base_conf, cfg)  

# @dataclass
# class HydraConfig:
#     user: Any = None
#     hydra: Any = field(default_factory= lambda:{
#         "output_subdir": None,
#         "run":{"dir": "."},
#         "sweep":{"dir":".", "subdir":"."},
#         "hydra_logging":{"disable_existing_loggers":True},
#         "job_logging":{"disable_existing_loggers":True},
#         })
#     exp: Config=Config()
# # def set_hydra_config(cfg):
# #     cfg.hydra.output_subdir=None
# #     cfg.hydra.run.dir = "."
# #     cfg.hydra.sweep.dir="."
# #     cfg.hydra.sweep.subdir="."
# #     cfg.hydra.hydra_logging.disable_existing_loggers=True
# #     cfg.hydra.job_logging.disable_existing_loggers=True


# def register_configs() -> None:
#     cs = ConfigStore.instance()

#     cs.store(group="default_config",
#              name="base", 
#              node=HydraConfig)

#     cs.store(group="default_config/config",
#              name="base", 
#              node=Config)
    
#     cs.store(
#         group="default_config/cluster",
#         name="base",
#         node=Cluster)

#     cs.store(
#         group="default_config/cluster",
#         name="oar",
#         node=OAR,
#     )
#     cs.store(
#         group="default_config/cluster",
#         name="slurm",
#         node=SLURM,
#     )

#     cs.store(
#         group="default_config/system",
#         name="base",
#         node=System,
#     )
#     cs.store(
#         group="default_config/logs",
#         name="base",
#         node=Logs,
#     )











