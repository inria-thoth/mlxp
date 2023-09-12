#!/bin/bash


python main.py  \
                optimizer.lr=10.\
                seed=1,2,3,4\
                +mlxp.use_scheduler=False\
                +mlxp.use_version_manager=False\
                +mlxp.use_logger=True\
