1- Launching
------------

We will see how to modify the file 'main.py' to use MLXP using the decorator 'mlxpy.launch'. 
But first, let's introduce the 'mlxpy.Context' class which allows using MLXP's logging and configuring functionalities. 


Defining a default config file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first step is to provide all default options that will be used by the code in a separate 'yaml' file named 'config.yaml' and contained in the './configs' directory. 

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

Here, we stored all options that were provided as input to the function 'train' in the 'main.py' file (such as the learning rate 'lr', number of epochs 'num_epochs', etc) into a structured yaml file. The user has the freedom to define their own structure: for instance, here we chose to group the input dimension 'd_int' and 'device' into the same 'data' group, but other (probably better choices) are possible. 
MLXP will load this file by default, just like in `hydra <https://hydra.cc/>`_ and provide these options as a hierachical dictionary to be used in the code (more about this later!).




Adapting code for using MLXP 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use MLXP, we only need to slightly change the 'main.py' file. 
The first step is to import MLXP and use the decorator 'mlxpy.launch' above the function 'train'.
We also need to change the signature of the function 'train' so that it can accept an object 'ctx' of type 'mlxpy.Context' as an argument instead of the variables. 
Note, however, that 'train' is called later without explicitly passing any argument. The remaining modifications are:

- Using the option values stored in ctx.config as a replacement of the variables provided in the older version of the code (See: :ref:`the old 'main.py' file <old_main_file>`). 
- Using the logger 'ctx.logger' to store the results of the run (instead of printing them) and saving checkpoints. 

Here is how the code would look like:

.. code-block:: python
    :caption: main.py

    
    import torch
    from core import DataLoader, OneHiddenLayer

    import mlxpy

    @mlxpy.launch(config_path='./configs')
    def train(ctx: mlxpy.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        start_epoch = 0

        # Building model, optimizer and data loader.
        model = OneHiddenLayer(d_int=cfg.data.d_int, 
                                n_units = cfg.model.num_units)
        model = model.to(cfg.data.device)
        optimizer = torch.optim.SGD(model.parameters(),
                                    lr=cfg.optimizer.lr)
        dataloader = DataLoader(cfg.data.d_int,
                                cfg.data.device)         

        # Training
        for epoch in range(start_epoch,cfg.num_epoch):

            train_err = train_epoch(dataloader,
                                    model,
                                    optimizer)

            logger.log_metrics({'loss': train_err.item(),
                                'epoch': epoch}, log_name='train')
            
            logger.log_checkpoint({'model': model,
                                   'epoch':epoch}, log_name='last_ckpt' )

        print(f"Completed training with learing rate: {cfg.optimizer.lr}")

    if __name__ == "__main__":
        train()


The Context object
""""""""""""""""""

MLXP uses an object 'ctx' of the class 'mlxpy.Context' that is created on the fly during the execution of the program to store information about the run. 
More precisely, it contains 4 fields: 

- ctx.config: Stores project-specific options provided by the user. These options are loaded from a yaml file 'config.yaml' located in the directory 'config_path' provided as input to the decorator (here config_path='./configs').  
- ctx.mlxpy: Stores MLXP's default settings for the project. Its content is loaded from a yaml file 'mlxpy.yaml' located in the same directory 'config_path'.  
- ctx.info: Contains information about the current run: ex. status, start time, hostname, etc. 
- ctx.logger: A logger object that can be used in the code for logging variables (metrics, checkpoints, artifacts). When logging is enabled, these variables are all stored in a uniquely defined directory. 



Launching using MLXP 
^^^^^^^^^^^^^^^^^^^^^

During execution, the default configurations will be read from the file 'config.yaml' located in the directory './configs' and passed to the object 'ctx.config'. The code will be executed using these option:

.. code-block:: console

   $ python main.py
   Completed training with learning rate: 10.0

Just like with `hydra <https://hydra.cc/>`_, we can run the code again with different options by overriding the default ones from the command line. For instance, we can use different learning rates and even select multiple values for it (say: 1e-2 and 1e-1). we can do this from the command line by providing multiple values (0.01,0.1) to the option 'optimizer.lr': 

.. code-block:: console

   $ python main.py optimizer.lr=0.01,0.1
   Completed training with learning rate: 0.01
   Completed training with learning rate: 0.1

In the above instruction, we added an option 'optimizer.lr=0.01,0.1' which execute the code twice: once using a learning rate of 0.01 and a second time using 0.1. 


Seeding code using MLXP
^^^^^^^^^^^^^^^^^^^^^^^^

In our example, the initialization of the model uses random initial parameters which might change from one run to another. To avoid this, the user can provide a function 'set_seed' to the mlxpy.launch decorator to set the global seeds of whatever random number generator is used. 


.. code-block:: python
    :caption: main.py

    import mlxpy
    from core import DataLoader, Network, Optimizer, Loss

    def set_seeds(seed):
        import torch
        torch.manual_seed(seed)

    @mlxpy.launch(config_path='./configs',
                seeding_function=set_seeds)
    def train(ctx: mlxpy.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        ...

    if __name__ == "__main__":
        train()


The function 'set_seeds' will be called by MLXP before executing the function 'train'. The parameter seed is read from the user-defined option: ctx.config.seed. If the field seed is not provided by the user and a seeding function is passed, then the code throws an error.  
Note that the field 'seed' passed to the 'set_seeds' can be an integer or a dictionary or any object that can be stored in a yaml file. 
Of course, it is also possible to perform seeding inside the function 'train', but 'seeding_function'  allows you to do it systematically. 


.. code-block:: console

   $ python main.py seed=1

   Completed training with learning rate: 1e-3

That's it, launching a job using MLXP is as easy as this! 
