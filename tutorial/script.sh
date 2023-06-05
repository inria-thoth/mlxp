#!/bin/bash


python main.py  \
                optimizer.lr=10.,1.,0.1\
                seed=1,2,3,4\
                +mlxp.use_scheduler=True\
                +mlxp.use_version_manager=True\
                +mlxp.use_logger=True\
