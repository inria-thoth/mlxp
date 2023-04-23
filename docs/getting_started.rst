Getting started
===============

Introduction
^^^^^^^^^^^^
Mlxpy is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. 


Key functionalities
^^^^^^^^^^^^^^^^^^^
  1. Launching several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs by adding a single decorator to the main task function.   
  2. Logging outputs (metrics, artifacts, checkpoints) of a job in a uniquely assigned directory along with all metadata and configuration options to reproduce the experiment.
  3. Code version management by automatically generating a deployment version of the code based on the latest git commit. 
  4. Submitting jobs to a cluster using a job scheduler. 
  5. Exploiting the results of several experiments by easily reading, querying, grouping, and aggregating the output of several jobs. 


Quick start guide
^^^^^^^^^^^^^^^^^

Let's say you have a python file 'main.py' that calls a function 'my_task' performing some task. To use mlxpy for launching a job, you can use the decorator 'mlxpy.launch' above the function 'my_task'. 

.. code-block:: python
   :caption: main.py

   import mlxpy 

   @mlxpy.launch(config_path='./configs')
   def my_task(ctx: mlxpy.Context)->None:

     print("ctx.config")

     print("The logger object is an instance of:")
     print(type(ctx.logger))


   if __name__ == "__main__":
     my_task()

The decorated function 'my_func' must take a  variable 'ctx' of type 'mlxpy.Context' as an argument. Note that 'my_task' is later called without providing the context variable just like in  `hydra <https://hydra.cc/>`_.
The 'ctx' variable is automatically created on the fly during execution and stores information about the run. It contains four fields: 'config', 'mlxpy', 'info', and 'logger':

  * ctx.config: Stores task-specific options provided by the user. These options are loaded from a yaml file 'config.yaml' located in the directory 'config_path' provided as input to the decorator (here config_path='./configs').  
  * ctx.mlxpy: Stores options contained in a yaml file 'mlxpy.yaml' located in the same directory 'config_path' and which configures the package mlxpy (see section below).  
  * ctx.info: Contains information about the current run: ex. status, start time, hostname, etc. 
  * ctx.logger: A logger object that can be used in the code for logging variables (metrics, checkpoints, artifacts). When logging is enabled, these variables are all stored in a uniquely defined directory. 

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
   <class 'mlxpy.logger.DefaultLogger'>
   
One can check that these outputs match the content of the yaml file 'config.yaml':

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

Just like in `hydra <https://hydra.cc/>`_, you can also override the options contained in the 'config.yaml' file from the command line: 

.. code-block:: console

   $ python main.py +optimizer.lr=0.1 +model.num_layers=6
   
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
   <class 'mlxpy.logger.DefaultLogger'>

If the file 'config.yaml' or its parent directory 'config_path' do not exist, they will be created automatically. By default, 'config.yaml' contains a single field 'seed' with a 'null' value intended for seeding random number generators.

.. code-block:: yaml
   :caption: ./configs/config.yaml

   seed: null




.. _Configuring_mlxpy:

Configuring mlxpy
^^^^^^^^^^^^^^^^^

Mlxpy is intended to be a configurable tool with default functionalities that can be adjusted by the user. 
The package default settings are stored in a file 'mlxpy.yaml' located in the same directory as the 'config.yaml' file. These files are created automatically if they don't already exist. 
By default, 'mlxpy.yaml' contains the following:

.. code-block:: yaml
   :caption: ./configs/mlxpy.yaml

   logger:
     name: DefaultLogger
     parent_log_dir: ./logs
     forced_log_id: -1
     log_streams_to_file: false
   scheduler:
     name: NoScheduler
     shell_path: ''
     shell_config_cmd: ''
     env_cmd: ''
     cleanup_cmd: ''
     option_cmd: []
   version_manager:
     name: GitVM
     parent_target_work_dir: ./.workdir
     compute_requirements: false
   use_version_manager: false
   use_scheduler: false
   use_logger: true
   interactive_mode: true

The logger
""""""""""
The options under 'logger' are specific to the mlxpy logger object. The field 'name' must contain the class name of the used logger. By default, it is set to 'DefaultLogger'. The user can provide a custom Logger provided that it inherits from the abstract class 'Logger'. The remaining fields refer to logger's options:

- parent_log_dir: The location where the directories of each run will be stored. The outputs for each run are saved in a directory of the form 
  'parent_log_dir/log_id' where 'log_id' is an integer uniquely assigned by the logger to the run.
- forced_log_id: An id optionally provided by the user for the run. If forced_log_id is positive, then the logs of the run will be stored under 'parent_log_dir/forced_log_id'. Otherwise, the logs will be stored in a directory 'parent_log_dir/log_id' where 'log_id' is assigned uniquely for the run during execution. 
- log_streams_to_file: If true logs the system stdout and stderr of a run to a file named "log.stdour" and "log.stderr" in the log directory.

The scheduler
"""""""""""""
The options under 'scheduler' are specific to the mlxpy scheduler object. The field 'name' must contain the class name of the used scheduler. By default, it is set to 'NoScheduler' meaning that no scheduler is defined. Mlxpy currently supports two job schedulers 'OAR' and 'SLUM'. In order to use them, the field 'name' must be modified to 'OARScheduler' of 'SLURMScheduler'. Additionally, the user can provide a custom scheduler inheriting from the abstract class 'Scheduler'. The remaining fields refer to scheduler's options:


- env_cmd: Command for activating the working environment. 
    (e.g. 'conda activate my_env')
- shell_path: Path to the shell used for submitting a job using a scheduler. (default '/bin/bash')
- shell_config_cmd: command for configuring the shell when submitting a job using a scheduler. (default 'source ~/.bashrc')
- cleanup_cmd: A command for clearning the environment when executing a job submitted by the scheduler. (e.g.: 'module purge' for SLURM) 
- option_cmd: A list of strings containing the scheduler's options for the job. This allows to specify the desired resources to the scheduler such as the duration of the job, the quantity and type of resources, etc. 


The version manager
"""""""""""""""""""
The options under 'version_manager' are specific to the mlxpy version manager object. The field 'name' must contain the class name of the used version manager. By default, it is set to 'GitVM', which is the version manager based on git. The user can provide a custom version manager inheriting from the abstract class 'VersionManager'. The remaining fields refer to manager's options:

- parent_target_work_dir: The target parent directory of the new working directory returned by the version manager
- compute_requirements: When set to true, the version manager stores a list of requirements and their version.


The interactive mode
""""""""""""""""""""
This option allows to enable/disable mlxpy's interactive mode. 

When set to 'True', mlxpy uses the interactive mode whenever applicable:
  
  - Sheduling: When 'use_scheduler==True' and 'scheduler.name=="NoScheduler"', mlxpy asks the user to select a valid scheduler.
  - Version managment: When 'use_version_manager==True', mlxpy asks the user to handle uncommited/untracked files and to choose the location from which code will be executed: 
      
When set to 'False', no interactive mode is used and the following behavior occurs:

  - Sheduling: When 'use_scheduler==True' and 'scheduler.name=="NoScheduler"' mlxpy throws an error.
  -  Version managment: When 'use_version_manager==True':

    * Existing untracked files or uncommitted changes are ignored.
    * A copy of the code is made based on the latest commit (if not already existing) and code is executed from there. 


Overriding the mlxpy setting
""""""""""""""""""""""""""""

It is possible to override these options from the command line by adding the prefix '+mlxpy' before the options. For instance, setting the option 'use_logger' to False disables logging. In this case, the logger object in ctx.logger has a 'Null' value: 

.. code-block:: console

   $ python main.py +mlxpy.use_logger=false 
   
   seed: null
   model:
     num_layers: 4
   optimizer:
     lr: 1e-3

   The logger object is an instance of:
   <class 'NoneType'>  



Citing mlxpy
^^^^^^^^^^^^

If you use mlxpy in your research please use the following BibTeX entry:


.. code-block:: bibtex 

   @Misc{Arbel2023Mlxpy,
     author = {Michae Arbel},
     title = {mlxpy},
     howpublished = {Github},
     year = {2023},
     url = {https://github.com/MichaelArbel/mlxpy}
   }

