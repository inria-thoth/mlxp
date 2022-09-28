#!/bin/bash

seed=0
log_name=test
isBatchJob=True

HYDRA_FULL_ERROR=1   OC_CAUSE=1 python -m ipdb main.py  \
                optimizer=sgd,adam\
                ++logs.log_name=$log_name\
                ++system.isBatchJob=$isBatchJob\
                ++system.seed=0,1,2,3\
                ++max_iter=100\
                ++system.isForceGitClean=False\



