Introduction
^^^^^^^^^^^^

MLXPy is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. 

MLXPy stands for Machine Learning eXperiments Python package.


Key functionalities
^^^^^^^^^^^^^^^^^^^


1. Launching several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs by adding a single decorator to the main task function.   
2. Logging outputs (metrics, artifacts, checkpoints) of a job in a uniquely assigned directory along with all metadata and configuration options to reproduce the experiment.
3. Code version management by automatically generating a deployment version of the code based on the latest git commit. 
4. Submitting jobs to a cluster using a job scheduler. 
5. Exploiting the results of several experiments by easily reading, querying, grouping, and aggregating the output of several jobs. 


Requirements
^^^^^^^^^^^^


.. list-table::
   :header-rows: 1
   :class: left

   * - Requirements
   * - hydra-core
   * - omegaconf
   * - tinydb
   * - setuptools
   * - PyYAML
   * - pandas
   * - ply
   * - dill
   * - GitPython


Installing MLXPy
^^^^^^^^^^^^^^^^

You can install this package by cloning it from the GitHub repository
and then installing it with `pip`. Before installing MLXPy, make sure you the requirements are installed.


1. Clone the repository:

.. code-block:: console
   
   $ git clone git@github.com:MichaelArbel/mlxpy.git

2. Change to the package directory:

.. code-block:: console
   
   $ cd mlxpy

3. Install the requirements using `pip`:

.. code-block:: console
   
   $ pip install -r requirements.txt

4. Install the package:

.. code-block:: console
   
   $ pip install .

Note: You may need to use `pip3` instead of `pip` depending on your setup.






Quick start guide
^^^^^^^^^^^^^^^^^

Let's say you are given a directory 'my_project' containing a python file 'main.py' and a sub-directory 'configs' containing a configuration file 'config.yaml' for the project:

.. code-block:: text

   my_project/
   ├── configs/
   │   └── config.yaml
   └── main.py


In this example, the file 'main.py' contains a function 'my_task' that performs some task when called. To use MLXPy for launching a job, you can use the decorator 'mlxpy.launch' above the function 'my_task'. 

.. code-block:: python

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
* ctx.mlxpy: Stores MLXPy's settings used for the run. 
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

If the file 'config.yaml' or its parent directory 'config_path' do not exist, they will be created automatically. When created automatically,  'config.yaml' contains a single field 'seed' ('null' by default) which is intended for seeding random number generators.

.. code-block:: yaml

   seed: null


Acknowledgments
^^^^^^^^^^^^^^^

I would like to acknowledge the following contributors for their contributions to the development of this package:

- `Alexandre Zouaoui <https://azouaoui.me/>`_ kindly shared his python implementation for creating job scripts and submiting them to a cluster. His code served as the basis for the implementation of the Scheduler class. While I have significantly modified the process of job submission, by integrating it with MLXpy's launching functionality, I am grateful for Alexandre's contribution which were invaluable to the development of this project.


- `Juliette Marrie <https://www.linkedin.com/in/juliette-marrie-5b8a59179/?originalSubdomain=fr>`_ tested a premature version of MLXPy. I am grateful for her feedback which was extremetly helpful for shaping and improving MLXPy's functionalities.  

- `Romain Ménégaux <https://www.linkedin.com/in/romain-menegaux-88a147134/?originalSubdomain=fr>`_ provided valuable feedback and suggestions to improve MLXPy. He also found and reported several bugs in the software which helped improve its quality and stability. 



Citing MLXPy
^^^^^^^^^^^^

If you use MLXPy in your research please use the following BibTeX entry:


.. code-block:: bibtex 

   @Misc{Arbel2023MLXPy,
     author = {Michae Arbel},
     title = {MLXPy},
     howpublished = {Github},
     year = {2023},
     url = {https://github.com/MichaelArbel/mlxpy}
   }

