


.. _Configuring_mlxp:

Configuring MLXP
=================

MLXP is intended to be a configurable tool with default functionalities that can be adjusted by the user. 
The package default settings are stored in a file :samp:`mlxp.yaml` located in the same directory as the :samp:`config.yaml` file. These files are created automatically if they don't already exist. 
By default,  :samp:`./configs/mlxp.yaml` contains the following:

.. code-block:: yaml

   logger:
     name: DefaultLogger
     parent_log_dir: ./logs
     forced_log_id: -1
     log_streams_to_file: false
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
The options under  :samp:`logger` are specific to the MLXP logger object. The field :samp:`name` must contain the class name of the used logger. By default, it is set to :samp:`DefaultLogger`. The user can provide a custom Logger provided that it inherits from the abstract class :samp:`Logger`. The remaining fields refer to logger's options:

- :samp:`parent_log_dir`: The location where the directories of each run will be stored. The outputs for each run are saved in a directory of the form :samp:`parent_log_dir/log_id` where :samp:`log_id` is an integer uniquely assigned by the logger to the run.
- :samp:`forced_log_id`: An id optionally provided by the user for the run. If :samp:`forced_log_id` is positive, the logs of the run will be stored under :samp:`parent_log_dir/forced_log_id`. Otherwise, the logs will be stored in a directory :samp:`parent_log_dir/log_id` where :samp:`log_id` is assigned uniquely for the run during execution. 
- :samp:`log_streams_to_file`: If true logs the system stdout and stderr of a run to a file named :samp:`log.stdout`  and :samp:`log.stderr` in the log directory.


The version manager
-------------------
The options under :samp:`version_manager` are specific to the MLXP version manager object. The field :samp:`name` must contain the class name of the used version manager. By default, it is set to :samp:`GitVM`, which is the version manager based on git. The user can provide a custom version manager inheriting from the abstract class :samp:`VersionManager`. The remaining fields refer to manager's options:

- :samp:`parent_work_dir`: The target parent directory of the new working directory returned by the version manager
- :samp:`compute_requirements`: When set to true, the version manager stores a list of requirements and their version.


The interactive mode
--------------------
This option allows to enable/disable MLXP's interactive mode. 

When set to :samp:`True`, MLXP uses the interactive mode for interacting with some MLXP modules:

  - **Version management:** When :samp:`use_version_manager==True`, MLXP asks the user to handle uncommited/untracked files. 
      
When set to :samp:`False`, no interactive mode is used and the following behavior occurs:

  - **Version management:** When :samp:`use_version_manager==True`: Existing untracked files or uncommitted changes are ignored.


Overriding MLXP's settings
---------------------------

It is possible to override these options from the command line by adding the prefix :samp:`+mlxp` before the options. For instance, setting the option :samp:`use_logger` to :samp:`False` disables logging. In this case, the logger object in :samp:`ctx.logger`  has a :samp:`Null` value: 

.. code-block:: console

   $ python main.py +mlxp.use_logger=false 
   
   seed: null
   model:
     num_layers: 4
   optimizer:
     lr: 1e-3

   The logger object is an instance of:
   <class 'NoneType'>  