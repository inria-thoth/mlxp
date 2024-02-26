#!/bin/bash


#OAR -l core=1, walltime=6:00:00
#OAR -t besteffort
#OAR -t idempotent
#OAR -p gpumem>'16000'


cd test_examples

python launch.py  \
                optimizer.lr=10.,1.,0.1\
                seed=5,6,7,8\
                +mlxp.use_version_manager=False\
                +mlxp.use_logger=True\


