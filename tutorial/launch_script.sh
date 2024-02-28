#!/bin/bash


#OAR -l core=1, walltime=6:00:00
#OAR -t besteffort
#OAR -t idempotent
#OAR -p gpumem>'16000'



python main.py  model.num_units=2,3,4 optimizer.lr=10.,1. seed=1,2,3\
                +mlxp.use_version_manager=False +mlxp.interactive_mode=False

sleep 10


python read.py