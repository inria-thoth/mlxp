#!/bin/bash


python main.py  \
                optimizer.lr=10.,1.,0.1\
                seed=1,2,3,4\
                +mlxpy.use_scheduler=True\
                +mlxpy.use_version_manager=True\
                +mlxpy.use_logger=True\
