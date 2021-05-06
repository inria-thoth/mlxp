from MLExp.reader import Reader 


import os
import logging
import hydra

from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, ListConfig, OmegaConf



query = {}
query['trainer.optimizer.optimizer'] =['SGD','Adam']

query['trainer.b_size'] = [500,1000]


#out = reader.search_list([query,query])




@hydra.main(config_path='./configs/config.yaml')
def main(cfg: DictConfig) -> None:
	exp_dir = os.path.join(os.path.abspath(cfg.logs.log_dir),cfg.logs.log_name)
	reader = Reader(exp_dir)
	reader.constuct_base()
	out = reader.search(query)
	for o in out:
		print(o['logs']['log_id'])
if __name__ == "__main__":
    main()
