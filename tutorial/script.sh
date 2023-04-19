#!/bin/bash


HYDRA_FULL_ERROR=1   OC_CAUSE=1 python -m ipdb main.py  \
                optimizer.lr=10.,1.,0.1\
                seed=1,2,3,4\
                +experimentalist.use_scheduler=True\
                +experimentalist.use_version_manager=True\
                +experimentalist.use_logger=True\
