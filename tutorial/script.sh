#!/bin/bash



#OAR -l core=1, walltime=6:00:00
#OAR -t besteffort
#OAR -t idempotent
#OAR -p gpumem>'16000' and not host like 'gpuhost25' and not host like 'gpuhost26' and not host like 'gpuhost8'

source gpu_setVisibleDevices.sh
conda activate base




python main.py  optimizer.lr=10.,1.,0.1 seed=1,2,3,4\
                +mlxp.use_version_manager=True