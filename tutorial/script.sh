#!/bin/bash



#OAR -l core=1, walltime=6:00:00
#OAR -t besteffort
#OAR -t idempotent
#OAR -p gpumem>'16000' and not host like 'gpuhost25' and not host like 'gpuhost26' and not host like 'gpuhost8'

source gpu_setVisibleDevices.sh
conda activate base




HYDRA_FULL_ERROR=1 python -m ipdb main.py  optimizer.lr=10.,1. seed=1,2,3\
                +mlxp.use_version_manager=True