#!/bin/bash


#HYDRA_FULL_ERROR=1   OC_CAUSE=1 python -m ipdb launch.py

cd test_examples

python launch.py  \
                optimizer.lr=10.,1.,0.1\
                seed=1,2,3,4\
                +mlxp.use_scheduler=False\
                +mlxp.use_version_manager=False\
                +mlxp.use_logger=True\


python read.py
