Getting started
===============

Introduction
^^^^^^^^^^^^
Experimentalist is an open-source python framework for managing multiple experiments with complex option structure from launching, logging to querying results. 


Key functionalities
^^^^^^^^^^^^^^^^^^^
  - Creating several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs. 
  - Submitting jobs using a job scheduler whenerver available. 
  - Enhancing code management and reproducibility of experiments by automatically generating a deployment version of the code based on the latest git commit. 
  - Logging all outputs of a job in a uniquely assigned directory, along with all metadata and  configuration options to reproduce the experiment.
  - Managing potential job failures by providing the ability to easily resume them from their latest state.
  - Exploiting the results of several experiments by easily reading, querying, grouping and aggregating the output of several jobs. 


Quick start guide
^^^^^^^^^^^^^^^^^

To use Experimentalist for launching a job, you need to import it in the main python file that will be executed and use the decorator 'expy.launch' above the function to be run:

.. code-block:: python
   :caption: main.py

   import experimentalist as expy

   @expy.launch(config_name="config.yaml", config_path="./configs")
   def my_func(logger: expy.Logger)->None:
     print(logger.user_config)

   if __name__ == "__main__":
     my_func()

The decorated function 'my_func' must take as argument an Logger object.
The logger object will be automatically created on the fly during excecution and will laod the configurations options provided in "config.yaml" of the directory "./configs". 

.. code-block:: console

   $ python main.py
   user_config: 
      model:
        num_layers: 4
      optimizer:
        lr: 1e-3

Just like in `hydra <https://hydra.cc/>`_, you can also provide configuration options in the command-line: 

.. code-block:: console

   $ python main.py ++user_config.optimizer.lr=10. ++user_config.model.num_layers=6
   user_config: 
      model:
        num_layers: 6
      optimizer:
        lr: 10

In the above example, the command-line options override the ones contained in the file 'config.yaml':

.. code-block:: yaml
   :caption: config.yaml

   user_config: 
      model:
        num_layers: 4
      optimizer:
        lr: 1e-3
   seed_config: ???

If the file "config.yaml" or its parent directory "./configs" do not exist, they will be created automatically. By default, "config.yaml" contains two fields: 'user_config' and 'seed'. The variable 'user_config' should store options specified by the user, whereas the variable 'seed_config' is intended for seeding randomn number generators. Note that, by default, both fields are empty (indicated by question marks ???).

.. code-block:: yaml
   :caption: config.yaml

   user_config: ???
   seed_config: ???

Experimentalist configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Experimentalist is intended to be a configurable tool with default functionalities that can be adjusted by the user. The package configurations are stored in a file 'base_config.yaml' located in the directory './configs'. 
The user can then modify this file to use their own preferred configuration options. 
When a new job is executed, the 'base_config.yaml' file is then loaded automatically. 
If the file 'base_config.yaml' does not exit already, it is created automotically with default configuration options.

.. code-block:: yaml
   :caption: base_config.yaml

   logger: None
   scheduler: None
   wd_manager: None

The logger option 'parent_log_dir' specifies a relative/absolute path where the outputs of all jobs will be saved. By default and for each run, the outputs are saved in a directory 'parent_log_dir/log_id', where 'log_id' is an integer that is uniquely defined for the current run. It is possible to force the value of 'log_id' by setting 





Additionally, the user can override these configs in the command-line when executing code.



Citing Experimentalist
^^^^^^^^^^^^^^^^^^^^^^

If you use Experimentalist in your research please use the following BibTeX entry:


.. code-block:: bibtex 

   @Misc{Arbel2023Expy,
     author = {Michae Arbel},
     title = {Experimentalist},
     howpublished = {Github},
     year = {2023},
     url = {https://github.com/MichaelArbel/experimentalist}
   }

