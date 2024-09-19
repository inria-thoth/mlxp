1- Launching
------------

We will see how to modify the file :samp:`main.py` to use MLXP using the decorator :samp:`mlxp.launch`. 
But first, let's introduce the :samp:`mlxp.Context` object produced by the decorator :samp:`mlxp.launch` that allows using MLXP's logging and configuring functionalities. 


The Context object
""""""""""""""""""

MLXP uses an object :samp:`ctx` of the class :samp:`mlxp.Context` that is created on the fly during the execution of the program to store information about the run. 
More precisely, it contains 4 fields: 

- :samp:`ctx.config`: Stores project-specific options provided by the user. These options are loaded from a yaml file called :samp:`config.yaml`  located in a directory :samp:`config_path` provided as input to the decorator :samp:`mlxp.launch`.   
- :samp:`ctx.mlxp`: Stores MLXP's default settings for the project. Its content is loaded from a yaml file :samp:`mlxp.yaml`  located in the same directory :samp:`config_path`.  
- :samp:`ctx.info`: Contains information about the current run: ex. status, start time, hostname, etc. 
- :samp:`ctx.logger`: A logger object that can be used in the code for logging variables (metrics, checkpoints, artifacts). When logging is enabled, these variables are all stored in a uniquely defined directory. 


General setup
"""""""""""""

Defining a default config file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first step is to provide all default options that will be used by the code in a separate Yaml file named :samp:`config.yaml` and contained in the :samp:`./configs` directory. 

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

Here, we stored all options that were provided as input to the function :samp:`train` in the :samp:`main.py` file (such as the learning rate :samp:`lr`, number of epochs :samp:`num_epochs`, etc) into a structured Yaml file. The user has the freedom to define their own structure: for instance, here we chose to group the input dimension :samp:`d_int` and :samp:`device` into the same :samp:`data` group, but other (probably better choices) are possible. 
MLXP will load this file by default, just like in `hydra <https://hydra.cc/>`_ and provide these options as a hierachical dictionary to be used in the code (more about this later!).




Adapting code for using MLXP 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use MLXP, we only need to slightly change the :samp:`main.py` file. 
The first step is to import MLXP and use the decorator :samp:`mlxp.launch` above the function :samp:`train`.
We also need to change the signature of the function :samp:`train` so that it can accept an object :samp:`ctx` of type :samp:`mlxp.Context`  as an argument instead of the variables. 
Note, however, that :samp:`train` is called later without explicitly passing any argument. The remaining modifications are:

- Using the option values stored in :samp:`ctx.config` as a replacement to the variables provided in the older version of the code (See: :ref:`the old 'main.py' file <old_main_file>`). 
- Using the logger :samp:`ctx.logger` to store the results of the run (instead of printing them) and saving checkpoints. 

Here is how the code would look like:

.. code-block:: python
    :caption: main.py

    
    import torch
    from core import DataLoader, OneHiddenLayer

    import mlxp

    @mlxp.launch(config_path='./configs')
    def train(ctx: mlxp.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        start_epoch = 0

        # Building model, optimizer and data loader.
        model = OneHiddenLayer(d_int=cfg.data.d_int, 
                                n_units = cfg.model.num_units)
        model = model.to(cfg.data.device)
        optimizer = torch.optim.SGD(model.parameters(),
                                    lr=cfg.optimizer.lr)
        train_dataloader = DataLoader(cfg.data.d_int,
                                cfg.data.device)         

        # Training
        for epoch in range(start_epoch,cfg.num_epoch):

            train_err = train_epoch(train_dataloader,
                                    model,
                                    optimizer)
            test_err = test_epoch(train_dataloader,
                                    model)

            logger.log_metrics({'loss': train_err.item(),
                                'epoch': epoch}, log_name='train')

            logger.log_metrics({'loss': test_err.item(),
                                'epoch': epoch}, log_name='test')

            logger.log_checkpoint({'model': model,
                                   'epoch':epoch}, log_name='last_ckpt' )

        print(f"Completed training with learing rate: {cfg.optimizer.lr}")

    if __name__ == "__main__":
        train()

Seeding code using MLXP
^^^^^^^^^^^^^^^^^^^^^^^

In our example, the initialization of the model uses random initial parameters which might change from one run to another. To avoid this, the user can provide a function :samp:`seeding_function` to the :samp:`mlxp.launch` decorator to set the global seeds of whatever random number generator is used. 


.. code-block:: python
    :caption: main.py

    import mlxp
    from core import DataLoader, Network, Optimizer, Loss

    def seeding_function(seed):
        import torch
        torch.manual_seed(seed)

    @mlxp.launch(config_path='./configs',
                seeding_function=seeding_function)
    def train(ctx: mlxp.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        ...

    if __name__ == "__main__":
        train()


The function :samp:`seeding_function` will be called by MLXP before executing the function :samp:`train`. The parameter seed is read from the user-defined option: :samp:`ctx.config.seed`. If the field seed is not provided by the user and a seeding function is passed, then the code throws an error.  
Note that the field :samp:`seed` passed to the :samp:`seeding_function` can be an integer or a dictionary or any object that can be stored in a yaml file. 
Of course, it is also possible to perform seeding inside the function :samp:`train`, but :samp:`seeding_function`  allows you to do it systematically. 




.. _launching_multiruns:

Launching locally using MLXP 
""""""""""""""""""""""""""""

During execution, the default configurations will be read from the file :samp:`config.yaml` located in the directory :samp:`./configs` and passed to the object :samp:`ctx.config`. The code will be executed using these option:

.. code-block:: console

   $ python main.py
   Completed training with learning rate: 10.0

Just like with `hydra <https://hydra.cc/>`_, we can run the code again with different options by overriding the default ones from the command line. For instance, we can use different learning rates and even select multiple values for it (say: :samp:`1e-2` and :samp:`1e-1`). we can do this from the command line by providing multiple values :samp:`(0.01,0.1)` to the option :samp:`optimizer.lr`: 

.. code-block:: console

   $ python main.py optimizer.lr=0.01,0.1
   Completed training with learning rate: 0.01
   Completed training with learning rate: 0.1

In the above instruction, we added an option :samp:`optimizer.lr=0.01,0.1` which execute the code twice: once using a learning rate of :samp:`0.01` and a second time using :samp:`0.1` . 

Launching jobs to a scheduler using mlxpsub command
"""""""""""""""""""""""""""""""""""""""""""""""""""

If you have access to an HPC cluster, then you probably use a job scheduler for submitting jobs. 
MLXP allows you to combine the 'multirun' capabilities of `hydra <https://hydra.cc/>`_ with job scheduling to easily submit multiple experiments to a cluster. 
Currently, MLXP supports the following job schedulers: 
`SLURM <https://slurm.schedmd.com/documentation.html>`_,  `OAR <https://oar.imag.fr/>`_, `TORQUE <https://hpc-wiki.info/hpc/Torque>`_, `SGE <https://gridscheduler.sourceforge.net/>`_, `MWM <https://docs.oracle.com/cd/E58073_01/index.htm>`_ and 
`LSF <https://www.ibm.com/docs/en/spectrum-lsf/10.1.0>`_.


.. _mlxpsub:



Submitting jobs to a job scheduler using mlxpsub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's say, you'd like to submit multiple jobs into a job scheduler. You can do this easily using the 
mlxpsub command! 


The first step is to create a script ex.: :samp:`script.sh` in your working directory (here under :samp:`my_project/`). 
In this script, you can define the resources allocated to your jobs, using the syntax of your job scheduler, as well as the python command for executing your main python script. You can then pass different option values to your python script :samp:`main.py` as discussed earlier in 
:ref:`the launching tutorial <launching_multiruns>`:

.. code-block:: console

  #!/bin/bash

  #OAR -l core=1, walltime=6:00:00
  #OAR -t besteffort
  #OAR -t idempotent

  python main.py  optimizer.lr=10.,1. seed=1,2
  python main.py  model.num_units=100,200 seed=1,2

The above script is meant to create and exectute 8 jobs in total that will be submitted to an OAR job scheduler. The first 4 jobs correspond to the first python command using all possible combinations of option values for :samp:`optimizer.lr` and :samp:`seed`: :samp:`(10.,1)` , :samp:`(10.,2)`, :samp:`(1.,1)`, :samp:`(1.,2)`. The 4 next jobs are for the second command wich varies the options :samp:`model.num_units` and :samp:`seed`.

You only need to run the following command in the terminal:


.. code-block:: console

  mlxpsub script.sh


Requirements for using mlxpsub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use :samp:`mlxpsub`, MLXP must be installed on both the head node and all compute nodes. 
        However, application-specific modules do not need to be installed on the head node. 
        You can avoid installing them on the head node by ensuring that these modules are only 
        imported within the function that is decorated with the :samp:`mlxp.launch` decorator. In our example, the :samp:`mlxp.launch` decorator is used in the file :samp:`main.py` to decorate the function :samp:`train`. The following version of :samp:`main.py` will require :samp:`torch` and all dependencies of the module :samp:`core` to be installed in the head node:


.. code-block:: python
    :caption: main.py

    
    import torch
    from core import DataLoader, OneHiddenLayer

    import mlxp

    @mlxp.launch(config_path='./configs')
    def train(ctx: mlxp.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        ...

    if __name__ == "__main__":
        train()


To avoid installing these modules on the head node, you can make the following simple modification to the :samp:`main.py` file:

.. code-block:: python
    :caption: main.py

    import mlxp

    @mlxp.launch(config_path='./configs')
    def train(ctx: mlxp.Context)->None:
        
        import torch
        from core import DataLoader, OneHiddenLayer

        cfg = ctx.config
        logger = ctx.logger

        ...

    if __name__ == "__main__":
        train()




What happens under the hood?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Here is what happens:

1. mlxpsub command parses the script to extract the scheduler's instructions and figures out what scheduler is used, then provides those information as a context prior to executing the script. 
2. `hydra <https://hydra.cc/>`_ performs a cross-product of the options provided and creates as many jobs are needed.
3. The MLXP creates a separate directory for each one of these jobs. Each directory is assigned a unique log_id and contains a script to be submitted. 
4. All generated scripts are submitted to the job scheduler.


What should you expect?
^^^^^^^^^^^^^^^^^^^^^^^

MLXP creates a script for each job corresponding to an option setting. Each script is located in a directory of the form 
:samp:`parent_log/log_id`, where :samp:`log_id` is automatically assigned by MLXP for each job. Here is an example of the first created script in :samp:`logs/1/script.sh` where the user sets :samp:`parent_log` to :samp:`logs`. 
   
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
   
As you can see, MLXP automatically assigns values for the job's name, :samp:`stdout`  and :samp:`stderr` file paths, 
so there is no need to specify those in the original script :samp:`script.sh`.
These scripts contain the same scheduler's options 
as in :samp:`script.sh` in addition to a single python command specific to the option setting: :samp:`optimizer.lr=10. seed=1`.
Additionally, MLXP pre-processes the python command to extract the working directory and sets it explicitly in the newly created script before the python command. 


Once, the job finishes execution, we can double-check that everything went well by inspecting the directory :samp:`logs/1/` which should contain the usual logs and two additional files :samp:`log.stdout`  and :samp:`log.stderr`:


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
   │   │   └── .keys/
   │   │        └── metrics.yaml
   │   ├── artifacts/
   │   │   └── pickle/
   │   │       └── last_ckpt.pkl
   │   ├── log.stderr
   │   ├── log.stdout
   │   └── script.sh
   │
   ├──...


