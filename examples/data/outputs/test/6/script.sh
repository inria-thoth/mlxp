#!/bin/bash
#OAR -n test/6
#OAR -E /home/marbel/Documents/projects/Experimentalist/examples/data/outputs/test/6/log.stderr
#OAR -O /home/marbel/Documents/projects/Experimentalist/examples/data/outputs/test/6/log.stdout
#OAR -l core=1,walltime=15:00:00
#OAR -t besteffort
#OAR -t idempotent
#OAR -p gpumem>'16000' and not host like 'gpuhost26' and not host like 'gpuhost27'

source ~/.bashrc
source gpu_setVisibleDevices.sh
conda activate 'default'
cd /home/marbel/Documents/projects/Experimentalist/examples/data/workdir/.date_27_09_2022_time_11_33
/scratch/clear/marbel/anaconda3/bin/python /home/marbel/Documents/projects/Experimentalist/examples/main.py optimizer=adam ++logs.log_name=test ++system.seed=1 ++max_iter=100 ++system.date='27/09/2022'             ++system.time='11:33:23'  ++logs.log_id=6
