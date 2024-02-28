Quick start guide
=================


This quick-start guide is meant to give you a overview of how MLXP works. 
To get a more in-depth understanding of MLXP's capabilities, please follow the  :ref:`tutorial<tutorial>`.


1- Using MLXP
-------------

Let's say you are given a directory :samp:`my_project` containing a python file :samp:`main.py` and a sub-directory :samp:`configs` containing a file 'config.yaml' with option configurations for the project:

.. code-block:: text

   my_project/
   ├── configs/
   │   └── config.yaml
   └── main.py


In this example, the file :samp:`main.py` contains a function :samp:`my_task` that performs some task when called. To use MLXP for launching a job, you can use the decorator :samp:`mlxp.launch` above the function :samp:`my_task`. 

.. code-block:: python

   import mlxp 

   @mlxp.launch(config_path='./configs')
   def my_task(ctx: mlxp.Context)->None:

     # Displaying user-defined options from './configs/config.yaml
     print("ctx.config")

     # Logging information in log directory created by MLXP: (here "./logs/1" )
     for i in range(ctx.config.num_epoch)
        ctx.logger.log_metrics({"epoch":i})



   if __name__ == "__main__":
     my_task()

The decorated function :samp:`my_task` must take a  variable :samp:`ctx` of type :samp:`mlxp.Context` as an argument. Note that :samp:`my_task` is later called without providing the context variable just like in  `hydra <https://hydra.cc/>`_.
The :samp:`ctx` variable is automatically created on the fly during execution and stores information about the run. 
Importantly, it contains: 


 - :samp:`ctx.config`:  a dictionary-like object storing user-defined configurations, usually loaded from a yaml file located in a configuration directory (here the directory :samp:`./configs`)
 - :samp:`ctx.logger`: A logger object that can be used in the code for saving variables (metrics, checkpoints, artifacts).

2- Configuring
--------------

Just like when using `hydra <https://hydra.cc/>`_, you can provide all default options needed for the code in a separate Yaml file named :samp:`config.yaml` and contained in the :samp:`./configs` directory. These will be passed to the object :samp:`ctx.config`.

.. code-block:: yaml
    :caption: ./configs/config.yaml
   
    seed: 0
    num_epoch: 10
    model:
     num_units: 100
    data:
     d_int: 10
     device: 'cpu'
    optimizer:
     lr: 10.

3- Logging
----------

Logging is activated by default and as soon as the run is launched, the logger creates a directory :samp:`parent_log_dir/log_id`  where :samp:`parent_log_dir` is provided by the user (default to :samp:`./logs`) while :samp:`log_id` is unique id that MLXP assigns to the run. 

- **Logging metadata:** Once the job is executed, the configuration options used for the run are automatically stored in a file :samp:`parent_log_dir/log_id/metadata/config.yaml`. 

- **Logging metrics and artifacts:** Additionally, the user can log additional informations using the methods :samp:`log_metrics`, :samp:`log_checkpoint` (see :ref:`Logging tutorial<logging>`) which are stored in the directories :samp:`metrics` and :samp:`artifacts`.


**Log directory structure:** Each log directory contains three sub-directories: samp:`metadata`, :samp:`metrics` and samp:`artifacts`:

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
   │   │   └──.keys/
   │   │       └── metrics.yaml
   │   └── artifacts/
   │       └── pickle/
   │           └── last_ckpt.pkl
   │    
   ├── 2/...
   └── 3/...




4- Launching locally
--------------------


When executing the Python file :samp:`main.py` from the command line, we get the following output:

.. code-block:: console

   $ python main.py

   seed: 0
   num_epoch: 10
   model:
    num_units: 100
   data:
    d_int: 10
    device: 'cpu'
   optimizer:
    lr: 10.



Overriding options from the command-line interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just like in `hydra <https://hydra.cc/>`_, you can also override the options contained in the :samp:`config.yaml` file from the command line: 

.. code-block:: console

   $ python main.py optimizer.lr=0.1 model.num_layers=6
   
   seed: 0
   num_epoch: 10
   model:
    num_units: 100
   data:
    d_int: 10
    device: 'cpu'
   optimizer:
    lr: 0.1


If the file :samp:`config.yaml` or its parent directory :samp:`config_path` do not exist, they will be created automatically. When created automatically,  :samp:`config.yaml` is empty and needs to be filled with default values of the user defined options.  


5- Submitting multiple jobs to a job scheduler
----------------------------------------------

Let's say, you'd like to submit multiple jobs into a job scheduler. You can do this easily using the mlxpsub command! 

i) Creating a job script
^^^^^^^^^^^^^^^^^^^^^^^^

The first step is to create a script 'script.sh' in your working directory (here under :samp:`my_project`). In this script you can define the resources allocated to your jobs, using the syntax of your job scheduler, as well as the python command for exectuting the python script :samp:`main.py` with different option values. Thanks to Hydra, you don't need any for loops and your job as be as concise as what follows: 

    .. code-block:: console

      #!/bin/bash

      #OAR -l core=1, walltime=6:00:00
      #OAR -t besteffort
      #OAR -t idempotent

      python main.py  optimizer.lr=10.,1. seed=1,2
      python main.py  model.num_units=100,200 seed=1,2

The above script is maint to create and exectute 8 jobs in total that will be submitted to an OAR job scheduler:

- The first 4 jobs correspond to the first python command using all possible combinations of option values for :samp:`optimizer.lr`  and :samp:`seed` : :samp:`(10.,1), (10,2), (1.,1), (1.,2)`.

- The 4 next jobs are for the second command wich varies the options :samp:`model.num_units` and :samp:`seed`.


MLXP supports multiple job schedulers, including 
`SLURM <https://slurm.schedmd.com/documentation.html>`_,  `OAR <https://oar.imag.fr/>`_, `TORQUE <https://hpc-wiki.info/hpc/Torque>`_, `SGE <https://gridscheduler.sourceforge.net/>`_, `MWM <https://docs.oracle.com/cd/E58073_01/index.htm>`_ and 
`LSF <https://www.ibm.com/docs/en/spectrum-lsf/10.1.0>`_. 
All what you have to do is to use the native syntax for specifying resources for the job as commants in the script. 

ii) Submitting using mlxpsub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You only need to run the following command in the terminal:


.. code-block:: console

  mlxpsub script.sh 


How it works
^^^^^^^^^^^^

MLXP creates a script for each job corresponding to optionsetting. Each script is located in a directory of the form :samp:`parent_log/log_id`  , where log_id is automatically assigned by MLXP for each job. 

Here is an example of the first created script in :samp:`logs/1/script.sh`  where the user sets :samp:`parent_log`  to :samp:`logs`. 
   
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
the job's name, stdout and stderr file paths, so there is no need to specify those in the original script :samp:`script.sh`.

These scripts contain the same scheduler's options 
as in :samp:`script.sh` and a single python command specific option setting: :samp:`optimizer.lr=10. seed=1`. 

Additionally, MLXP pre-processes the python command to extract the working directory and sets it explicitly in the newly created script before the python command. 

