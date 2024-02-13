4- Scheduling jobs with MLXP
----------------------------

If you have access to an HPC cluster, then you probably use a job scheduler for submitting jobs. 
MLXP allows you to combine the 'multirun' capabilities of `hydra <https://hydra.cc/>`_ with job scheduling to easily submit multiple experiments to a cluster. 
Currently, MLXP supports the following job schedulers: 
`SLURM <https://slurm.schedmd.com/documentation.html>`_,  `OAR <https://oar.imag.fr/>`_, `TORQUE <https://hpc-wiki.info/hpc/Torque>`_, `SGE <https://gridscheduler.sourceforge.net/>`_, `MWM <https://docs.oracle.com/cd/E58073_01/index.htm>`_ and 
`LSF <https://www.ibm.com/docs/en/spectrum-lsf/10.1.0>`_.



Submitting jobs to a job scheduler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's say, you'd like to submit multiple jobs into a job scheduler. You can do this easily using the 
mlxpsub command! 


The first step is to create a script ex.: 'script.sh' in your working directory (here under my_project/). 
In this script, you can define the resources allocated to your jobs, using the syntax of your job scheduler, as well as the python command for exectuting your main python script. You can then pass different option values to your python script 'main.py' as discussed earlier in :ref: `the launching tutorial'<launching_multiruns>`:


    .. code-block:: console

      #!/bin/bash

      #OAR -l core=1, walltime=6:00:00
      #OAR -t besteffort
      #OAR -t idempotent

      python main.py  optimizer.lr=10.,1. seed=1,2
      python main.py  model.num_units=100,200 seed=1,2

The above script is meant to create and exectute 8 jobs in total that will be submitted to an OAR job scheduler. The first 4 jobs correspond to the first python command using all possible combinations of option values for 'optimizer.lr' and 'seed': (10.,1), (10,2), (1.,1), (1.,2).
The 4 next jobs are for the second command wich varies the options 'model.num_units' and 'seed'.

You only need to run the following command in the terminal:


    .. code-block:: console
      mlxpsub script.sh


MLXP creates a script for each job corresponding to an option setting. Each script is located in a directory of the form 'parent_log/log_id', where log_id is automatically assigned by MLXP for each job. Here is an example of the first created script in 'logs/1/script.sh' where the user sets 'parent_log' to 'logs'. 
   
.. code-block:: console
    #!/bin/bash
    #OAR -n logs/1
    #OAR -E /root/logs/1/log.stderr
    #OAR -O /root/logs/1/log.stdout
    #OAR -l core=1, walltime=6:00:00
    #OAR -t besteffort
    #OAR -t idempotent
   
    cd /root/workdir/
    python main.py  optimizer.lr=10. seed=1
   
As you can see, MLXP automatically assigns values for 
the job's name, stdout and stderr file paths, 
so there is no need to specify those in the originscript'script.sh'.
These scripts contain the same scheduler's options 
as in 'script.sh' and a single python command usionespecific option setting:
    optimizer.lr=10. seed=1
Additionally, MLXP pre-processes the python command to extract the working directory and sets it explicitly in the newly created script before the python command. 


We can check that the job is assigned to a cluster queue using the command 'oarstat':

.. code-block:: console

   $ oarstat

   Job id    S User     Duration   System message
   --------- - -------- ---------- ----------------------------------------

   684627    R username 1:15:42 R=1,W=192:0:0,J=B (Karma=0.064,quota_ok)


Once, the job finishes execution, we can double-check that everything went well by inspecting the directory './logs/1' which should contain the usual logs and two additional files 'log.stdout' and 'log.stderr':



.. code-block:: text
   :caption: ./logs/
   
   logs/
   ├── 1/
   │   ├── metadata/
   │   │   ├── config.yaml
   │   │   ├── info.yaml
   │   │   └── mlxp.yaml
   │   ├── metrics/
   │   │   ├── train.json
   │   │   └── .keys/
   │   │        └── metrics.yaml
   │   ├── artifacts/
   │   │   └── Checkpoint/
   │   │       └── last_ckpt.pkl
   │   ├── log.stderr
   │   ├── log.stdout
   │   └── script.sh
   │
   ├──...


How does it work?
"""""""""""""""""


Here is what happens:

1. mlxpsub command parses the script to extract the scheduler's instructions and figures out what scheduler is used, then provides those information as a context prior to executing the script. 
2. `hydra <https://hydra.cc/>`_ performs a cross-product of the options provided and creates as many jobs are needed (3x4).
3. The MLXP creates a separate directory for each one of these jobs. Each directory is assigned a unique log_id and contains a script to be submitted. 
4. All generated scripts are submitted to the job scheduler.


