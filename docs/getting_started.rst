Quick start guide
=================


This quick-start guide is meant to give you a overview of how MLXP works. 
To get a more in-depth understanding of MLXP's capabilities, please follow the :doc:`main tutorial <tutorial.rst>`.


Let's say you are given a directory 'my_project' containing a python file 'main.py' and a sub-directory 'configs' containing a configuration file 'config.yaml' for the project:

.. code-block:: text

   my_project/
   ├── configs/
   │   └── config.yaml
   └── main.py


In this example, the file 'main.py' contains a function 'my_task' that performs some task when called. To use MLXP for launching a job, you can use the decorator 'mlxp.launch' above the function 'my_task'. 

.. code-block:: python

   import mlxp 

   @mlxp.launch(config_path='./configs')
   def my_task(ctx: mlxp.Context)->None:

     print("ctx.config")

     print("The logger object is an instance of:")
     print(type(ctx.logger))


   if __name__ == "__main__":
     my_task()

The decorated function 'my_func' must take a  variable 'ctx' of type 'mlxp.Context' as an argument. Note that 'my_task' is later called without providing the context variable just like in  `hydra <https://hydra.cc/>`_.
The 'ctx' variable is automatically created on the fly during execution and stores information about the run. It contains four fields: 'config', 'mlxp', 'info', and 'logger':

- **ctx.config**: Stores task-specific options provided by the user. These options are loaded from a yaml file 'config.yaml' located in the directory 'config_path' provided as input to the decorator (here config_path='./configs').  
- **ctx.mlxp**: Stores MLXP's settings used for the run. 
- **ctx.info**: Contains information about the current run: ex. status, start time, hostname, etc. 
- **ctx.logger**: A logger object that can be used in the code for logging variables (metrics, checkpoints, artifacts). When logging is enabled, these variables are all stored in a uniquely defined directory of the form 'parent_log_dir/log_id' where 'parent_log_dir' is provided by the user and 'log_id' is unique id that MLXP assigns to the run. 

When executing the Python file 'main.py' from the command line, we get the following output:

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

   The logger object is an instance of:
   <class 'mlxp.logger.DefaultLogger'>
   
One can check that these outputs match the content of the yaml file './configs/config.yaml':

.. code-block:: yaml
  
   seed: 0
   num_epoch: 10
   model:
    num_units: 100
   data:
    d_int: 10
    device: 'cpu'
   optimizer:
    lr: 10.

Logging
-------

By default logging is activated and the logger creates a directory 'parent_log_dir/log_id' where 'parent_log_dir' is provided by the user (default to 'logs') while 'log_id' is unique id that MLXP assigns to the run. 
Once the job is executed, the configuration options used for the run are automatically stores in a file 'parent_log_dir/log_id/metadata/config.yaml'. Additionally, the user can log additional informations using the methods 'log_metrics', 'log_checkpoint' (see :ref: `Logging tutorial'<logging>`).

Overriding options
------------------

Just like in `hydra <https://hydra.cc/>`_, you can also override the options contained in the 'config.yaml' file from the command line: 

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

   The logger object is an instance of:
   <class 'mlxp.logger.DefaultLogger'>

If the file 'config.yaml' or its parent directory 'config_path' do not exist, they will be created automatically. When created automatically,  'config.yaml' is empty and needs to be filled with default values of the user defined options.  

Submitting to a job scheduler
-----------------------------

Let's say, you'd like to submit multiple jobs into a job scheduler. You can do this easily using the mlxpsub command! The first step is to create a script 'script.sh' in your working directory (here under my_project/). In this script you can define the resources allocated to your jobs, using the syntax of your job scheduler, as well as the python command for exectuting the python script 'main.py' with different option values. Thanks to Hydra, you don't need any for loops and your job as be as concise as what follows: 

    .. code-block:: console

      #!/bin/bash

      #OAR -l core=1, walltime=6:00:00
      #OAR -t besteffort
      #OAR -t idempotent

      python main.py  optimizer.lr=10.,1. seed=1,2
      python main.py  model.num_units=100,200 seed=1,2

The above script is maint to create and exectute 8 jobs in total that will be submitted to an OAR job scheduler. Currently, MLXP supports both OAR and SLURM. 
The first 4 jobs correspond to the first python command using all possible combinations of option values for 'optimizer.lr' and 'seed': (10.,1), (10,2), (1.,1), (1.,2).
The 4 next jobs are for the second command wich varies the options 'model.num_units' and 'seed'.

You only need to run the following command in the terminal:


    .. code-block:: console
      mlxpsub script.sh


MLXP creates a script for each job corresponding to optionsetting.
Each script is located in a directory of the form 'parent_log/log_id', where log_id is automatically assigned by MLXP for each job. Here is an example of the first created script in 'logs/1/script.sh' where the user sets 'parent_log' to 'logs'. 
   
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
Additionally, MLXP pre-processes the python command toextraits working directory 
and set it explicitly in the newly created script befothepython command. 


