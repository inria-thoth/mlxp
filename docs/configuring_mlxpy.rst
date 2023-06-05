


.. _Configuring_mlxpy:

Configuring MLXP
=================

MLXP is intended to be a configurable tool with default functionalities that can be adjusted by the user. 
The package default settings are stored in a file 'mlxpy.yaml' located in the same directory as the 'config.yaml' file. These files are created automatically if they don't already exist. 
By default, './configs/mlxpy.yaml' contains the following:

.. code-block:: yaml

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
     parent_work_dir: ./.workdir
     compute_requirements: false
   use_version_manager: false
   use_scheduler: false
   use_logger: true
   interactive_mode: true

The logger
----------
The options under 'logger' are specific to the MLXP logger object. The field 'name' must contain the class name of the used logger. By default, it is set to 'DefaultLogger'. The user can provide a custom Logger provided that it inherits from the abstract class 'Logger'. The remaining fields refer to logger's options:

- parent_log_dir: The location where the directories of each run will be stored. The outputs for each run are saved in a directory of the form 
  'parent_log_dir/log_id' where 'log_id' is an integer uniquely assigned by the logger to the run.
- forced_log_id: An id optionally provided by the user for the run. If forced_log_id is positive, then the logs of the run will be stored under 'parent_log_dir/forced_log_id'. Otherwise, the logs will be stored in a directory 'parent_log_dir/log_id' where 'log_id' is assigned uniquely for the run during execution. 
- log_streams_to_file: If true logs the system stdout and stderr of a run to a file named "log.stdour" and "log.stderr" in the log directory.

The scheduler
-------------
The options under 'scheduler' are specific to the MLXP scheduler object. The field 'name' must contain the class name of the used scheduler. By default, it is set to 'NoScheduler' meaning that no scheduler is defined. MLXP currently supports two job schedulers 'OAR' and 'SLUM'. In order to use them, the field 'name' must be modified to 'OARScheduler' of 'SLURMScheduler'. Additionally, the user can provide a custom scheduler inheriting from the abstract class 'Scheduler'. The remaining fields refer to scheduler's options:

- env_cmd: Command for activating the working environment. (e.g. 'conda activate my_env')
- shell_path: Path to the shell used for submitting a job using a scheduler. (default '/bin/bash')
- shell_config_cmd: command for configuring the shell when submitting a job using a scheduler. (default 'source ~/.bashrc')
- cleanup_cmd: A command for clearning the environment when executing a job submitted by the scheduler. (e.g.: 'module purge' for SLURM) 
- option_cmd: A list of strings containing the scheduler's options for the job. This allows to specify the desired resources to the scheduler such as the duration of the job, the quantity and type of resources, etc. 


The version manager
-------------------
The options under 'version_manager' are specific to the MLXP version manager object. The field 'name' must contain the class name of the used version manager. By default, it is set to 'GitVM', which is the version manager based on git. The user can provide a custom version manager inheriting from the abstract class 'VersionManager'. The remaining fields refer to manager's options:

- parent_work_dir: The target parent directory of the new working directory returned by the version manager
- compute_requirements: When set to true, the version manager stores a list of requirements and their version.


The interactive mode
--------------------
This option allows to enable/disable MLXP's interactive mode. 

When set to 'True', MLXP uses the interactive mode whenever applicable:
  
  - Sheduling: When 'use_scheduler==True' and 'scheduler.name=="NoScheduler"', MLXP asks the user to select a valid scheduler.
  - Version managment: When 'use_version_manager==True', MLXP asks the user to handle uncommited/untracked files and to choose the location from which code will be executed: 
      
When set to 'False', no interactive mode is used and the following behavior occurs:

  - Sheduling: When 'use_scheduler==True' and 'scheduler.name=="NoScheduler"' MLXP throws an error.
  -  Version managment: When 'use_version_manager==True':

    * Existing untracked files or uncommitted changes are ignored.
    * A copy of the code is made based on the latest commit (if not already existing) and code is executed from there. 


Overriding MLXP's settings
---------------------------

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