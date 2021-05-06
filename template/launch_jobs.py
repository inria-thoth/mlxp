# script for submitting jobs to cluster

import os
import logging
import hydra

from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, ListConfig, OmegaConf
from MLExp.launcher import create

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@hydra.main(config_path='./configs/config.yaml')
def main(cfg: DictConfig) -> None:
    logger.info(f"Current working directory: {os.getcwd()}")
    try:
        create(cfg)
    except Exception as e:
        logger.critical(e, exc_info=True)


if __name__ == "__main__":
    main()
