import hydra
from hydra import utils

from hydra.experimental import compose, initialize

#initialize("configs")
#cfg = compose("config.yaml", overrides=[])

@hydra.main(config_path='./configs/config.yaml')
def run(cfg):
	print(cfg.pretty())

#if __name__ == "__main__":
run()
