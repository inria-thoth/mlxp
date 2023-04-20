Tutorial
========

In this example we would like to train a simple neural network on a regression task. 



1- Easy launching
-----------------

Let's have a look at the main python file to be executed.
We can import mlxpy as 'expy' for simplicity. 
To use mlxpy, we only need to use the decorator 'expy.launch' above the main function to be executed. In this case, our function 'train' will optimize a network. It must be defined as a function taking an object 'ctx' of type 'expy.Context' as argument, although it will be later call without explicity passing any argument. 
The object 'ctx' will be created on the fly during execution and will contain a logger object and a structure containing the user configuration for the run. 

.. code-block:: python
    :caption: main.py

    import mlxpy as expy
    from core_app import DataLoader, Network, Optimizer, Loss

    @expy.launch(config_path='./configs')
    def train(ctx: expy.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        num_epoch = cfg.num_epoch
        
        model = Network(n_layers = cfg.model.num_layers)
        optimizer = Optimizer(model,lr = cfg.optimizer.lr)
        dataloader = DataLoader()
        loss = Loss()
         

        for epoch in range(num_epoch):
            for iteration, data in enumerate(dataloader):
                x,y = data
                pred = model(x)
                train_err = loss(pred, y)
                train_err.backward()
                optimizer.step()
                logger.log_metrics({'loss': train_err.item(),
                'iter': iteration,
                'epoch': epoch}, log_name= 'train')

            logger.log_checkpoint({'model': model,
                                   'epoch':epoch}, log_name = 'last_ckpt')
        print(f"Completed training with learing rate: {cfg.optimizer.lr}")
    
    if __name__ == "__main__":
        train()
        

During execution, the configuration will be read from the file 'config.yaml' located in the directory './configs'. This file contains user provided values for the options 'num_layers', 'lr' and 'num_epoch' used by the function 'train' and access from the field 'config' of the 'ctx' object. Let's  inspect the 'config.yaml':

.. code-block:: yaml
   :caption: ./configs/config.yaml
  
   seed: null
   model:
     num_layers: 4
   optimizer:
     lr: 1e-3
   num_epoch: 2

We are now ready to run the code! 


.. code-block:: console

   $ python main.py

   Completed training with learing rate: 1e-3

We want to run the code again with different learning rates (say: 1e-2 and 1e-1). Just like with hydra, we can do this from the command-line by providing multiple values (0.01,0.1) to the option 'optimizer.lr': 

.. code-block:: console

   $ python main.py +optimizer.lr=0.01,0.1

   Completed training with learing rate: 1e-2

   Completed training with learing rate: 1e-1

The above instruction executes the code twice: once using a learning rate of 1e-2 and second time using 1e-1. 
That's it, launching a job using mlxpy is as easy as this! 


2- Easy logging 
---------------

By default, the logger was activated and logging the outputs of the run in a directory located in './logs'. To see this, we can inspect the file 'mlxpy.yaml' located by default in the directory './configs'. This file contains the configurations for mlxpy. There, we see that the variable 'use_logger' is set to 'true' and that the variable logger.parent_log_dir is set to './logs': 


.. code-block:: yaml
   :caption: ./configs/mlxpy.yaml

   logger:
     name: DefaultLogger
     parent_log_dir: ./logs
     forced_log_id: -1
     log_streams_to_file: false
   scheduler: ... 
   version_manager: ...
   use_version_manager: false
   use_scheduler: false
   use_logger: true


First, the logger assigns a 'log_id' to the run. Everytime we 'main.py' is executed with an active logger, the log_id of the new run is incremented by 1 starting from 1. Then a new sub-directory of './logs' is created and named after the assigned log_id. 
Since we executed the code three times in total, we should expect three sub-directories under './logs' called '1', '2' and '3', all having the same structure:

.. code-block:: text
   :caption: ./logs/

   logs/
   ├── 1/...
   ├── 2/...
   └── 3/...

Let's have a closer look at the content of these sub-directories:

.. code-block:: text
   :caption: ./logs/

   logs/
   ├── 1/
   │   ├── metadata/
   │   │   ├── config.yaml
   │   │   ├── info.yaml
   │   │   └── mlxpy.yaml
   │   ├── metrics/
   │   │   └── train.json
   │   ├── artifacts/
   │   │   └── Checkpoint/
   │   │       └── last_ckpt.pkl
   │   └── .keys/
   │       └── metrics.yaml
   ├── 2/...
   └── 3/...

The hidden directory '.keys' is used by the reader module of mlxpy and is not something to worry about here. Instead we inspect the remaining files and directories below. 


The 'metrics' directory
^^^^^^^^^^^^^^^^^^^^^^^

This directory contains json files created when calling the logger's method 'log_metrics(dict, log_name)'. Each file is named after the variable 'log_name' and stores the dictionaries provided as input to the'log_metrics' method. 


.. code-block:: json
   :caption: ./logs/1/metrics/train.json

   {
    "train_loss": 1.2,
    "iter": 0,
    "epoch": 0
   }
   {
    "train_loss": 1.19,
    "iter": 1,
    "epoch": 0
   }

   {
    "train_loss": 0.1,
    "iter": 29,
    "epoch": 9
   }


The 'metadata' directory
^^^^^^^^^^^^^^^^^^^^^^^^

The 'metadata' directory contains three yaml files: 'config', 'info' and 'mlxpy', each storing the content of the corresponding fields of the context object 'ctx'. 
'config' stores the user config of the run, 'info' stores general information about the run such as the assinged 'log_id' and the absolute path to the logs of the run 'log_dir', while 'mlxpy' stores the mlxpy's settings used for the run (e.g. the logger settings). 


.. code-block:: yaml
   :caption: ./logs/1/metadata/config.yaml

    seed: null
    model:
      num_layers: 4
    optimizer:
      lr: 1e-3
    num_epoch: 2

.. code-block:: yaml
   :caption: ./logs/1/metadata/info.yaml

    log_id: 1
    log_dir: absolute_path_to/logs/1/
    ...

.. code-block:: yaml
   :caption: ./logs/1/metadata/mlxpy.yaml

    use_logger: true
    ...

The 'artifacts' directory 
^^^^^^^^^^^^^^^^^^^^^^^^

The directory 'artifacts' is where all data passed to the logger's methods 'log_artifact' and 'log_checkpoint' are stored. These are stored in different directories depending on the artifact type. In this example, since we used the reserved method 'log_checkpoint', the logged data are considered as checkpoint objects, hence the sub-directory 'Checkpoint'. You can see that it contains the pickle file 'last_ckpt.pkl' which is the name we provided when calling the method 'log_checkpoint' in the 'main.py' file. 

Checkpointing can be particularly useful if you need to restart a job from its latest state without having to re-run it form scratch. To do this, you only need to slightly modify the 'train' to load the latest checkpoint by default:

.. code-block:: python
    :caption: main.py

    import mlxpy as expy
    from core_app import DataLoader, Network, Optimizer, Loss

    @expy.launch(config_path='./configs')
    def train(ctx: expy.Context)->None:


    try:
        checkpoint = logger.load_checkpoint()
        num_epoch = cfg.num_epoch - checkpoint['epoch']-1
        model = checkpoint['model']
    except:
        num_epoch = cfg.num_epoch
        model = Network(n_layers = cfg.model.num_layers)

        optimizer = Optimizer(model,lr = cfg.optimizer.lr)
        dataloader = DataLoader()
        loss = Loss()

    print(f"Starting from epoch {num_epoch}")

    for epoch in range(num_epoch):
        ...

    if __name__ == "__main__":
        train()

Of course if you execute 'main.py' without further options, the logger will create a new 'log_id' where there is no checkpoint yet, so it cannot resume a previous job. Instead, you need to force the 'log_id' using the option: 'logger.forced_log_id' 

.. code-block:: console

   $ python main.py +mlxpy.logger.forced_log_id=1

   Starting from epoch 9

   Completed training with learing rate: 1e-3



3- Easy reading
---------------

.. code-block:: ipython

    In [1]: import mlxpy as expy

    In [2]: # Create a reader object to access the results stored by the logger.
       ...: parent_log_dir = './logs/'
            reader = expy.Reader(parent_log_dir)

    In [3]: # Perform a query search on the logs.
       ...: query = "config.optimizer.lr <= 1e-2 & info.status == 'COMPLETE'"
        results = reader.search(query_string=query, asPandas = True)

    In [3]: # Display the result as a pandas dataframe 
       ...: results 
    Out[3]:
    +-----------+-------------------+-----+-------------+
    |info.log_id|config.optimizer.lr| ... | train.loss  |
    +-----------+-------------------+-----+-------------+
    |     1     |       1e-3        | ... |[0.3,...,0.1]|
    |     2     |       1e-2        | ... |[0.3,...,0.1]|
    +-----------+-------------------+-----+-------------+


The search method of the reader results a pandas dataframe whose rows correspond to a run stored in the 'parent_log_dir' and matching the provided query. 
The dataframe's column names consist of:
- The dot-separaed flattened keys of the hierarchical options contained in the yaml file 'metadata.yaml' preceeded by the prefix 'metadata'.  
- The keys of the dictionaries stored in the file 'metrics.json' preceeded by the suffix 'metrics'. 
As you can see, the dataframe loads the content of all keys in the  'metrics.json' file as a list, which might not be desirable if the file is large. 
This can be avoided using 'lazy loading' which we describe next.

Lazy evaluation
^^^^^^^^^^^^^^^

Instead of returning the result of the search as a pandas dataframe, which loads all the content of the, possibly large, 'metrics.json' file, we can return a 'expy.ConfigList' object. 
This object can also be rendered as a dataframe but does not load the 'metrics.json' files in memory unless the corresponding fields are explicitly accessed. 



.. code-block:: ipython

    In [1]: import mlxpy as expy

    In [2]: # Create a reader object to access the results stored by the logger.
       ...: parent_log_dir = './logs/'
            reader = expy.Reader(parent_log_dir)

    In [3]: # Perform a query search on the logs.
       ...: query = "config.optimizer.lr <= 1e-2 & info.status == 'COMPLETE'"
        results = reader.search(query_string=query)

    In [3]: # Display the result as a pandas dataframe 
       ...: results 
    Out[3]:
    +-----------++-----------+-------------------+-----+-----------+
    |info.log_id||info.status|config.optimizer.lr| ... |train.loss |
    +-----------++-----------+-------------------+-----+-----------+
    |     1     || COMPLETED |       1e-3        | ... |LAZYLOADING|
    |     2     || COMPLETED |       1e-2        | ... |LAZYLOADING|
    +-----------++-----------+-------------------+-----+-----------+

    In [4]: # Accessing the column 'metrics.train_loss'
       ...: results[0]['train.loss']
    Out[4]:


4- Reproducibility
------------------

Experimentalist provides three main features for enhanced reproducibility:

    - Config logs: By storing the configs of each run into the 'config.yaml', one can keep track of what parameters were used to obtain are result. A good practice is to avoid hard-coding any parameter and systematically providing those as options. 
    - Seeding: Experimentalist allows to easily seed the random number generators globally by passing a 'seeding function' to the the launcher. (More on this below).
    - Version management: Experimentalist provides a version manager that relies on git to check for uncommitted changes and untracked files interactively. Once all changes are committed, the version manager created a copy of the repository based on the latest commit and run the jobs from there.

Seeding
^^^^^^^

In our example, the initialization of the model uses random initial parameters which might change from a run to another. To avoid this, the user can provide a function 'set_seed' to the expy.launch decorator to set the global seeds of whathever random number generator is used. 


.. code-block:: python
    :caption: main.py

    import mlxpy as expy
    from core_app import DataLoader, Network, Optimizer, Loss

    def set_seeds(seed):
        import torch
        torch.manual_seed(seed)

    @expy.launch(config_path='./configs',
                seeding_function=set_seeds)
    def train(ctx: expy.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        ...

    if __name__ == "__main__":
        train()


The function 'set_seeds' will be called by mlxpy before executing the function 'train'. The parameter seed is read from the user-defined option: ctx.config.seed. 
Note that this object can be an integer or a dictionary or any object that can be stored in a yaml file. 
Of course it is also possible to perform seeding inside the function 'train', but this allows to do it systematically. 


.. code-block:: console

   $ python main.py +seed=1

   Completed training with learing rate: 1e-3


Version management
^^^^^^^^^^^^^^^^^^

Sometimes, there can be a delay between the time when a job is submitted and when it gets executed. This typically happens when submitting jobs to a cluster queue. 
Meanwhile, the development code might have already changed, with some potential bugs introduced! 
Without careful version management, it is hard to know for sure what code was used to produce the results. Experimentalist proposes a simple way to avoid these issues by introducing two features:
- Systematically checking for uncommitted change/ untracked files
- Sytematically copying the code from the git repository containing the executable to another 'safe' location based on the latest commit. The code is then run from this location to avoid any interference with changed that could be introduced to the development code before executing a job. 

Let's see how this work! We simply need to set the option 'use_version_manager' to true. This launches an interactive seesion where the user can tell the version manager what to do.

.. code-block:: console

   $ python main.py +mlxpy.use_version_manager=True

   



First, the version manager checks for untracked files and asks to user what to do: either ignore or add the files to git. Let's say we choose to ignore the added files. 


.. code-block:: console

   $ python main.py +mlxpy.use_version_manager=True



The next step is to check for uncommitted changes. We see that there is one change that is uncommitted. The user can either ignore this, commit the changes from a different iterface and check again, or commit the changes from the version manager interface. Here, we just choose option 'a' which creates an automatic commit of the changes. 



.. code-block:: console

   $ python main.py +mlxpy.use_version_manager=True

Finally, the version manager asks if we want to create a 'safe' copy based on the latest commit and from which code will be executed. If not, the code is excuted from the current directory. We choose the safe copy! Experimentalist proceed to excecute the code from that copy:


.. code-block:: console

   Completed training with learing rate: 1e-3


We can double check where the code were executed from by inspecting the 'info.yaml' file (Note that this is the 4th run, so the file should be located in ./logs/4/)


.. code-block:: yaml
   :caption: ./logs/4/metadata/info.yaml

    log_id: 4
    log_dir: absolute_path_to/logs/4/
    work_dir: 


You can see that the workin directory during execution of the job was '' which is different from the initial directory from which we run the commang 'python main.py +mlxpy.use_version_manager=True'. The directory is named after the latest commit hash during execution time (the one that was created when interacting with the version manager). We can inspect that directory and see that it contains a full copy of the committed files contained in the repository (except untracked files). 
If other jobs are submitted later, and if the code did not change meanwhile, then these jobs will also be executed from this same working directory. This avoids copying the exact same content multiple times. 

Finally, a copy of the dependencies used by the code is also stored along with their versions in the fields 'requirements'. 



5- Advanced launching using a scheduler
---------------------------------------


If you have access to an HPC cluster, then you probably use a job scheduler for submiting jobs. 
Using mlxpy, you can combine the 'multirun' capabilities of hydra with job scheduling to perform large scale experiments involving large grid search over multiple hyper-parameters.


Configuring the scheduler
^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Experimentalist supports two job schedulers 'OAR' and 'SLURM'.  You can also specify your own custom scheduler and we will see later. 
For now, let's use assume we are using one of the default schedulers: 'OAR'. 
Since, the scheduler settings are unlikely to change much during your project, I  recommand to directly edit those settings in the './configs/mlxpy.yaml': 



.. code-block:: yaml
   :caption: ./configs/mlxpy.yaml

   logger: ... 
  
   scheduler:
     name: OARScheduler
     shell_path: '/bin/bash'
     shell_config_cmd: ''
     env_cmd: ''
     cleanup_cmd: ''
     option_cmd: ["-l core=1,walltime=15:00:00",
        "-t besteffort",
        "-t idempotent",
        "-p gpumem>'16000'"
      ]

   version_manager: ...


Here, we set the option 'name' to 'OARScheduler', which is the class  implemented by mlxpy to handle OAR.
Then, we need to provide some options to the scheduler: 'shell_path',  'shell_config_cmd', 'env_cmd', 'cleanup_cmd' and 'option_cmd' that we'll discuss soon. 
The most important command is the 'option_cmd' which specifies the resources required by the job using OAR's syntax. 
It contains a list of strings, each string providing some instruction to OAR (e.g.: number of cores, walltime, gpu memory). You can have a look at the OAR documentation for how to set those options. 


Submitting job to a cluster queue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can now submit jobs using OAR scheduler assuming we have access to it. We only need to set the option 'use_scheduler' to True: 

.. code-block:: console

   $ python main.py +mlxpy.use_scheduler=True


Under the woods mlxpy first assigns a 'log_id' to the run and creates its corresponding log directory './logs/log_id'. Here, log_id=5, since this is the 5th run that we launched in './logs'. Then instead of executing the job, the scheduler creates a script 'script.sh' that is saved in './logs/log_id'. This script is then submitted automatically to the OAR cluster queue using the command: 'sbatch .script.sh'. At this point, the program exits with a message 'Submitted 1 job to the cluster queue!'.
Let's have a look at the content of the script:


.. code-block:: sh   
    :caption: ./logs/5/script.sh

    #!/bin/bash
    #OAR -n logs/5
    #OAR -E absolute_path_to/logs/5/log.stderr
    #OAR -O absolute_path_to/logs/5/log.stdout
    #OAR -l core=1,walltime=15:00:00
    #OAR -p gpumem>'16000'
    
    cd absolute_path_to/work_dir

    python main.py 
    +mlxpy.logger.forced_log_id=5 
    +mlxpy.logger.parent_log_dir=absolute_path_to/logs
    +mlxpy.use_scheduler=False
    +mlxpy.use_version_manager=False

Let's now go through this script:

- The first line of the script specifies the shell used for running the script. It is determined by the scheduler's option 'shell_path' of the 'mlxpy.yaml' file settings. We chose to set it to '/bin/bash'. 
- The next lines specify the OAR resource option provided in 'option_cmd'. 
- The first instruction is to go to the work_directory set by the launcher (which can be different from the current working directory if we are using the version manager). 
- Finally, we find the instruction for executing the 'main.py' file with some additional options. 
    - First, the log_id is forced to be the same as the one asigned for the job during launching (here log_id=5). 
    - Then, we make sure that the 'parent_log_dir' is also the same as the one we used during job submission to the cluster. 
    - Finally, the job must not use any scheduler or version manager anymore! That is because this script was already submitted to a queue using the scheduler and must readily be executed once a resource is allocated. 

This script is submitted automatically to the OAR cluster queue, so there is no need, in priciple, to worry about it. It is only useful in case you need to debug or re-run an experiment. 

We can check that the job is assigned to a cluster queue using the command 'oarstat':

.. code-block:: console

   $ oarstat

   Job id    S User     Duration   System message
   --------- - -------- ---------- ----------------------------------------

   684627    R username 1:15:42 R=1,W=192:0:0,J=B (Karma=0.064,quota_ok)



Once, the job finishes execution, we can double check that everything went well by inspecting the directory './logs/5' which should contain the usual logs and two additional files 'log.stdout' and 'log.stderr':



.. code-block:: text
   :caption: ./logs/
   
   logs/
   ├── 5/
   │   ├── metadata/
   │   │   ├── config.yaml
   │   │   ├── info.yaml
   │   │   └── mlxpy.yaml
   │   ├── metrics/
   │   │   └── train.json
   │   ├── artifacts/
   │   │   └── Checkpoint/
   │   │       └── last_ckpt.pkl
   │   ├── .keys/
   │   │   └── metrics.yaml
   │   ├── log.stderr
   │   ├── log.stdout
   │   └── script.sh
   │
   ├──...


Submitting several jobs to a cluster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also fire several jobs to the cluster from a single command! Let's say, you want to vary the learning rate and use different seeds to test the robustness of the results. You can leverage the power of hydra for this!

.. code-block:: console

   $ python main.py +optimizer.lr=1e-3,1e-2,1e-1 +seed=1,2,3,4  +mlxpy.use_scheduler=True

Here is what happens:

1- Hydra performs a cross product of the options provided and creates as many jobs are needed (3x4).
2- The mlxpy logger create a separate directory for each one of these jobs (by assigning a unique log_id to each one of them).
3- The scheduler creates a script for each of these jobs in the corresponding directory (created by the logger) then submits these scripts to the cluster queue.

You only need to wait for the results to come!



Combining the scheduler with the version manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Finally, you can combine both features to run several reproducible jobs with a controlled version of the code they use.  

   $ python main.py +optimizer.lr=1e-3,1e-2,1e-1 +seed=1,2,3,4  +mlxpy.use_scheduler=True +mlxpy.use_version_manager=True


In this case, mlxpy first runs the version manager 
with an interactive 





























