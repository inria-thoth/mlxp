import hydra
from hydra import utils

from hydra.experimental import compose, initialize

#initialize(config_path= "configs")
#cfg = compose("config.yaml", overrides=[])

@hydra.main(config_name='./configs/config.yaml')
def run(cfg):
	return cfg.pretty()

if __name__ == "__main__":
	run(cfg)
