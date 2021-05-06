from __future__ import print_function

#import torch
import argparse
import yaml
import torch

from trainer import Trainer

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

import hydra
from hydra import utils

# check whether we want to load a pretrained model depending on the given parameters




@hydra.main(config_path='./configs/config.yaml')
def run(cfg):
	trainer = Trainer(cfg)
	trainer.main()
	print('Finished!')

if __name__ == "__main__":
    run()

