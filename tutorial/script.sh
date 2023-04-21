#!/bin/bash


HYDRA_FULL_ERROR=1   OC_CAUSE=1 python -m ipdb main.py  \
                optimizer.lr=10.,1.,0.1\
                seed=1,2,3,4\
                +mlxpy.use_scheduler=True\
                +mlxpy.use_version_manager=True\
                +mlxpy.use_logger=True\
