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
- **ctx.logger**: A logger object that can be used in the code for logging variables (metrics, checkpoints, artifacts). When logging is enabled, these variables are all stored in a uniquely defined directory. 

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
   <class 'mlxp.logger.DefaultLogger'>

If the file 'config.yaml' or its parent directory 'config_path' do not exist, they will be created automatically. When created automatically,  'config.yaml' contains a single field 'seed' ('null' by default) which is intended for seeding random number generators.

.. code-block:: yaml

   seed: null
