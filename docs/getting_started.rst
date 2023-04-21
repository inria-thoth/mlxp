Getting started
===============

Introduction
^^^^^^^^^^^^
mlxpy is an open-source python framework for managing multiple experiments with flexible option structure from launching, logging to querying results. 


Key functionalities
^^^^^^^^^^^^^^^^^^^
  - Launching several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs by adding a single decorator to the main task function (see Quick start guide).   
  - Logging outputs (metrics, artifacts, checkpoints) of a job in a uniquely assigned directory along with all metadata and configuration options to reproduce the experiment.
  - Code version management by automatically generating a deployment version of the code based on the latest git commit. 
  - Submitting jobs to a cluster using a job scheduler. 
  - Exploiting the results of several experiments by easily reading, querying, grouping and aggregating the output of several jobs. 


Quick start guide
^^^^^^^^^^^^^^^^^

Let's say you have a python file 'main.py' that call a function 'my_task' performing some task. To use mlxpy for launching a job, you can use the decorator 'expy.launch' above the function 'my_task'. 

.. code-block:: python
   :caption: main.py

   import mlxpy as expy

   @expy.launch(config_path='./configs')
   def my_task(ctx: expy.Context)->None:

     print("ctx.config")

     print("The logger object is an instance of:")
     print(type(logger))


   if __name__ == "__main__":
     my_task()

The decorated function 'my_func' must take as arguments a context variable 'ctx' which is an object of the class Context. 
Note that 'my_task' is later called without providing the context variable just like in  `hydra <https://hydra.cc/>`_.
The 'ctx' variable is automatically created on the fly during execution and stores informations about the run. It contains four fields: 'config', 'mlxpy', 'info' and 'logger':

  - ctx.config: Stores task specific options provided by the user. These options are loaded from a yaml file 'config.yaml' located in the directory 'config_path' provided as input to the decorator (here config_path='./configs').  
  - ctx.mlxpy: Stores options contained in a yaml file 'mlxpy.yaml' located in the same directory 'config_path' and which configure the package mlxpy (see section below).  
  - ctx.info: Contains information about the current run: ex. status, start time, hostname, etc. 
  - ctx.logger: Is an a logger object that can be used in the code for logging variables (metrics, checkpoints, artifacts). When logging is enabled, these variables are all stored in a uniquely defined directory. 

When executing the python file 'main.py' from the command-line, we get the following output:

.. code-block:: console

   $ python main.py

   seed: null
   model:
     num_layers: 4
   optimizer:
     lr: 1e-3

   The logger object is an instance of:
   <class 'mlxpy.logger.DefaultLogger'>
   
One can check that these outputs match the content of the yaml file 'config.yaml':

.. code-block:: yaml
   :caption: ./configs/config.yaml
  
   seed: null
   model:
     num_layers: 4
   optimizer:
     lr: 1e-3

Just like in `hydra <https://hydra.cc/>`_, you can also override the options contained in the 'config.yaml' file from the command-line: 

.. code-block:: console

   $ python main.py +optimizer.lr=10. +model.num_layers=6
   
   seed: null
   model:
     num_layers: 6
   optimizer:
     lr: 10

   The logger object is an instance of:
   <class 'mlxpy.logger.DefaultLogger'>

If the file 'config.yaml' or its parent directory 'config_path' do not exist, they will be created automatically. By default, 'config.yaml' contains a single field 'seed' with a 'null' value intended for seeding randomn number generators.

.. code-block:: yaml
   :caption: ./configs/config.yaml

   seed: null



mlxpy configuration
^^^^^^^^^^^^^^^^^^^

mlxpy is intended to be a configurable tool with default functionalities that can be adjusted by the user. 
The package configurations are stored in a file 'mlxpy.yaml' located in the same directory as the 'config.yaml' file.
If the file 'mlxpy.yaml' does not exit already, it is created automatically with default configuration options:

.. code-block:: yaml
   :caption: ./configs/mlxpy.yaml

   logger:
     name: DefaultLogger
     parent_log_dir: ./logs
     forced_log_id: -1
     log_streams_to_file: false
   scheduler:
     name: Scheduler
     shell_path: ''
     shell_config_cmd: ''
     env_cmd: ''
     cleanup_cmd: ''
     option_cmd: []
   version_manager:
     name: GitVM
     parent_target_work_dir: ./.workdir
     skip_requirements: false
     interactive_mode: true
   use_version_manager: false
   use_scheduler: false
   use_logger: true

The fields 'logger', 'scheduler' and 'version_manager' contain the configurations for logging information (Logger), submitting to a job scheduler (Scheduler) and managing code version used for executing jobs (VersionManager). For all three configuration fields, the sub-field 'name' must contain the relevant class name of the object instantiated during execution. 
In case of using custom classes provided by the user, the full scope of such classes must be provided to the sub-fields 'name'. These classes must inherit form abstract classes Logger, Scheduler or VersionManager. 
The remaining sub-fields are variables provided to the constructor of these classes. 
Finally, the options 'use_version_manager', 'use_scheduler' and 'use_logger' either enable or disable these three functionalities (logging, scheduling and version management).  

It is possible to override these options from the command-line by adding the prefix 'mlxpy' before the options. For instance, setting the option 'use_logger' to False disables logging. In this case, the logger object in ctx.logger has a 'Null' value: 

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
^^^^^^^^^^^^^^^^^^^^^^

If you use mlxpy in your research please use the following BibTeX entry:


.. code-block:: bibtex 

   @Misc{Arbel2023Expy,
     author = {Michae Arbel},
     title = {mlxpy},
     howpublished = {Github},
     year = {2023},
     url = {https://github.com/MichaelArbel/mlxpy}
   }

