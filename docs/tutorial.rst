Tutorial
========



Introduction
------------

In this tutorial, we will see how to use mlxpy to run experiments using Python. 
We will go through the three main functionalities: Launching, Logging, and Reading and explain these are easily handled by mlxpy. 
Then we will see how to enhance reproducibility of experiments using the git-based version manager provided by mlxpy and how to submit several jobs to a cluster in a single command using the mlxpy's scheduler. 

To make things concrete, we will consider a simple use-case where we are interested in training a neural network on a regression task. You can find code for reproducing this tutorial by following this link https://github.com/MichaelArbel/mlxpy/tree/master/tutorial.

We will now give a quick overview of our working example, where we present the directory structure of the code and its main content. 


Directory structure
^^^^^^^^^^^^^^^^^^^

The first step is to create a directory 'tutorial' containing the code needed for this project. The directory is structured as follow:

.. code-block:: text
   :caption: tutorial/

   tutorial/
   ├── configs/
   │   └── config.yaml
   ├── core.py
   ├── main.py
   └── results.py

The directory contains three files: 'core.py', 'main.py' and 'results.py'. It also contains a directory 'configs' that will be used later by mlxpy. For now, we will only have a look at the 'core.py' and 'main.py' files.


The 'core.py' file
""""""""""""""""""

The file 'core.py' contains a PyTorch implementation of a one hidden layer network 'OneHiddenLayer' as well as a simple data loader 'DataLoader' that we will use during training. In the rest of the tutorial, we will not need to worry about the content of 'core.py', but let's just have a quick look at this file:


.. code-block:: python
    :caption: main.py

    import torch
    import torch.nn as nn

    def train_epoch(dataloader,
                    model,
                    optimizer):
        for data in dataloader:
            x,y = data
            pred = model(x)
            train_err = torch.mean((pred-y)**2)
            train_err.backward()
            optimizer.step()
        return train_err

    class Dataset(torch.utils.data.Dataset):

        def __init__(self, d_int, device):
            self.network = OneHiddenLayer(d_int, 5)
            self.device = device
            dtype = torch.float
            self.X = torch.normal(mean= torch.zeros(N_samples,d_int,dtype=dtype,device=device),std=1.)
            self.total_size = N_samples
            with torch.no_grad():
                self.Y = self.network(self.X)

        def __len__(self):
            return self.total_size 
        def __getitem__(self,index):
            return self.X[index,:],self.Y[index,:]

    def DataLoader(d_int, device):
        dataset = Dataset(d_int, device)
        return [(dataset.X, dataset.Y)]



    class OneHiddenLayer(nn.Module):
        def __init__(self,d_int, n_units):
            super(OneHiddenLayer,self).__init__()
            self.linear1 = torch.nn.Linear(d_int, n_units,bias=True)
            self.linear2 = torch.nn.Linear( 1, n_units, bias=False)
            self.non_linearity = torch.nn.SiLU()
            self.d_int = d_int
            self.n_units = n_units

        def forward(self, x):
            x = self. non_linearity(self.linear1(x))
            return torch.einsum('hi,nh->ni',self.linear2.weight,x)/self.n_units

.. _old_main_file
The 'main.py' file
""""""""""""""""""

The file 'main.py' contains code for training the model 'OneHiddenLayer' on data provided by the 'DataLoader'. Training is performed using the function 'train': 

.. code-block:: python
    :caption: main.py

    import torch
    from core import DataLoader, OneHiddenLayer

    def train(d_int = 10,
              num_units = 100,
              num_epoch = 10,
              lr = 10.,
              device = 'cpu'):

        # Building model, optimizer and data loader.
        model = OneHiddenLayer(d_int=d_int, n_units = num_units)
        model = model.to(device)
        optimizer = torch.optim.SGD(model.parameters(),lr=lr)
        dataloader = DataLoader(d_int,device)         

        # Training
        for epoch in range(num_epoch):

            train_err = train_epoch(dataloader,
                                    model,
                                    optimizer)

            print({'loss': train_err.item(),
                  'epoch': epoch})

        print(f"Completed training with learing rate: {lr}")

    if __name__ == "__main__":
        train()


Training the model
^^^^^^^^^^^^^^^^^^

If we execute the function 'main.py', we can see that the training performs 10 'epochs' and then prints a message confirming that the training is complete. 

.. code-block:: console

    $ python main.py
    {'loss': 0.030253788456320763, 'epoch': 0}
    {'loss': 0.02899891696870327, 'epoch': 1}
    {'loss': 0.026649776846170425, 'epoch': 2}
    {'loss': 0.023483652621507645, 'epoch': 3}
    {'loss': 0.019827445968985558, 'epoch': 4}
    {'loss': 0.01599641889333725, 'epoch': 5}
    {'loss': 0.012259905226528645, 'epoch': 6}
    {'loss': 0.008839688263833523, 'epoch': 7}
    {'loss': 0.005932427477091551, 'epoch': 8}
    {'loss': 0.003738593542948365, 'epoch': 9}
    Completed training with learing rate: 10.0


In this basic example, we have not used any specific tool for launching or logging. 
Next, we will see how you can use mlxpy to keep track of all options, results, and code versions seamlessly! 


1- Easy launching
-----------------

We will see how to modify the file 'main.py' to use mlxpy using the decorator 'mlxpy.launch'. 
But first, let's introduce the 'mlxpy.Context' class which allows using mlxpy's logging and configuring functionalities. 


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
Mlxpy will load this file by default, just like in `hydra <https://hydra.cc/>`_ and provide these options as a hierachical dictionary to be used in the code (more about this later!).




Adapting code for using mlxpy 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To use mlxpy, we only need to slightly change the 'main.py' file. 
The first step is to import mlxpy and use the decorator 'mlxpy.launch' above the function 'train'.
We also need to change the signature of the function 'train' so that it can accept an object 'ctx' of type 'mlxpy.Context' as an argument instead of the variables. 
Note, however, that 'train' is called later without explicitly passing any argument. 
The remaining modifications are:

 1. Using the option values stored in ctx.config as a replacement of the variables provided in the older version of the code (See: ref:`The 'main.py' file <tutorial:old_main_file>). 
 2. Using the logger 'ctx.logger' to store the results of the run (instead of printing them) and saving checkpoints. 

Here is how the code would look like:

.. code-block:: python
    :caption: main.py

    
    import torch
    from core import DataLoader, OneHiddenLayer

    import mlxpy as mlxpy

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

Mlxpy uses an object 'ctx' of the class 'mlxpy.Context' that is created on the fly during the execution of the program to store information about the run. 
More precisely, it contains 4 fields: 

- ctx.config: Stores project-specific options provided by the user. These options are loaded from a yaml file 'config.yaml' located in the directory 'config_path' provided as input to the decorator (here config_path='./configs').  
- ctx.mlxpy: Stores mlxpy's default settings for the project. Its content is loaded from a yaml file 'mlxpy.yaml' located in the same directory 'config_path'.  
- ctx.info: Contains information about the current run: ex. status, start time, hostname, etc. 
- ctx.logger: A logger object that can be used in the code for logging variables (metrics, checkpoints, artifacts). When logging is enabled, these variables are all stored in a uniquely defined directory. 



Launching code using mlxpy 
^^^^^^^^^^^^^^^^^^^^^^^^^^

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


Seeding code using mlxpy
^^^^^^^^^^^^^^^^^^^^^^^^

In our example, the initialization of the model uses random initial parameters which might change from one run to another. To avoid this, the user can provide a function 'set_seed' to the mlxpy.launch decorator to set the global seeds of whatever random number generator is used. 


.. code-block:: python
    :caption: main.py

    import mlxpy as mlxpy
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


The function 'set_seeds' will be called by mlxpy before executing the function 'train'. The parameter seed is read from the user-defined option: ctx.config.seed. If the field seed is not provided by the user and a seeding function is passed, then the code throws an error.  
Note that the field 'seed' passed to the 'set_seeds' can be an integer or a dictionary or any object that can be stored in a yaml file. 
Of course, it is also possible to perform seeding inside the function 'train', but 'seeding_function'  allows you to do it systematically. 


.. code-block:: console

   $ python main.py seed=1

   Completed training with learning rate: 1e-3

That's it, launching a job using mlxpy is as easy as this! 



The mlxpy default settings file  
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the code is executed for the first time, mlxpy creates a file 'configs/mlxpy.py' containing the defaults options for using the mlxpy in the current project. The user can customise these depending on their needs (See: ref:`Configuring mlxpy <file1:Configuring_mlxpy>).


2- Easy logging 
---------------





The parent log directory
^^^^^^^^^^^^^^^^^^^^^^^^

When the logger is activated, it stores the results of a run in a sub-directory of the parent directory './logs'. This parent directory is created automatically if it does not exists already. By default it is set to './logs', but this value can be overriden from the command-line:

.. code-block:: console

   $ python main.py mlxpy.logger.parent_log_dir='./new_logs'


Alternatively, the parent directory can be modified directly in the mlxpy default settings file 'configs/mlxpy.yaml'. This file is created automatically if it doesn't exist already and contains all the defaults options for using mlxpy in the current project:

.. code-block:: yaml
   :caption: ./configs/mlxpy.yaml

   logger:
     ...
     parent_log_dir: ./logs
     ...


Structure of the parent log directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, the logger assigns a 'log_id' to the run. Every time 'main.py' is executed with an active logger, the log_id of the new run is incremented by 1 starting from 1. Then a new sub-directory of './logs' is created and named after the assigned log_id. 
Since we executed the code three times in total, we should expect three sub-directories under './logs' called '1', '2', and '3', all having the same structure:

.. code-block:: text
   :caption: ./logs/

   logs/
   ├── 1/...
   ├── 2/...
   └── 3/...

Each log directory contains three sub-directories: 'metadata', 'metrics' and 'artifacts':

.. code-block:: text
   :caption: ./logs/

   logs/
   ├── 1/
   │   ├── metadata/
   │   │   ├── config.yaml
   │   │   ├── info.yaml
   │   │   └── mlxpy.yaml
   │   ├── metrics/
   │   │   ├── train.json
   │   │   └──.keys/
   │   │       └── metrics.yaml
   │   └── artifacts/
   │       └── Checkpoint/
   │           └── last_ckpt.pkl
   │    
   ├── 2/...
   └── 3/...

Let's go through these three directories.

The 'metrics' directory
"""""""""""""""""""""""

This directory contains JSON files created when calling the logger's method 'log_metrics(dict, log_name)'. Each file is named after the variable 'log_name' and stores the dictionaries provided as input to the 'log_metrics' method. 


.. code-block:: json
    :caption: ./logs/1/metrics/train.json

    {"loss": 0.030253788456320763, "epoch": 0}
    {"loss": 0.02899891696870327, "epoch": 1}
    {"loss": 0.026649776846170425, "epoch": 2}
    {"loss": 0.023483652621507645, "epoch": 3}
    {"loss": 0.019827445968985558, "epoch": 4}
    {"loss": 0.01599641889333725, "epoch": 5}
    {"loss": 0.012259905226528645, "epoch": 6}
    {"loss": 0.008839688263833523, "epoch": 7}
    {"loss": 0.005932427477091551, "epoch": 8}
    {"loss": 0.003738593542948365, "epoch": 9}

The hidden directory '.keys' is used by the reader module of mlxpy and is not something to worry about here. Instead, we inspect the remaining directories below. 


The 'metadata' directory
""""""""""""""""""""""""

The 'metadata' directory contains three yaml files: 'config', 'info', and 'mlxpy', each storing the content of the corresponding fields of the context object 'ctx'. 
'config' stores the user config of the run, 'info' stores general information about the run such as the assigned 'log_id' and the absolute path to the logs of the run 'log_dir'. Finally, 'mlxpy' stores the mlxpy's settings used for the run (e.g. the logger settings). 


.. code-block:: yaml
    :caption: ./logs/1/metadata/config.yaml

    seed: 0
    num_epoch: 10
    model:
     num_units: 100
    data:
     d_int: 10
     device: 'cpu'
    optimizer:
     lr: 10.

.. code-block:: yaml
    :caption: ./logs/1/metadata/info.yaml
    
    app: absolute_path_to/bin/python
    cmd: ''
    end_date: 20/04/2023
    end_time: '16:01:13'
    exec: absolute_path_to/main.py
    log_dir: absolute_path_to/logs/1
    log_id: 1
    process_id: 7100
    start_date: 20/04/2023
    start_time: '16:01:13'
    status: COMPLETE
    user: marbel
    work_dir: absolute_path_to/tutorial

.. code-block:: yaml
    :caption: ./logs/1/metadata/mlxpy.yaml

    logger:
      forced_log_id: -1
      log_streams_to_file: false
      name: DefaultLogger
      parent_log_dir: ./logs
    scheduler:
      cleanup_cmd: ''
      env_cmd: ''
      name: NoScheduler
      option_cmd: []
      shell_config_cmd: ''
      shell_path: /bin/bash
    version_manager:
      name: GitVM
      parent_target_work_dir: ./.workdir
      compute_requirements: false
    use_logger: true
    use_scheduler: false
    use_version_manager: false
    interactive_mode: true


The 'artifacts' directory 
"""""""""""""""""""""""""

The directory 'artifacts' is where all data passed to the logger's methods 'log_artifact' and 'log_checkpoint' are stored. These are stored in different directories depending on the artifact type. In this example, since we used the reserved method 'log_checkpoint', the logged data are considered as checkpoint objects, hence the sub-directory 'Checkpoint'. You can see that it contains the pickle file 'last_ckpt.pkl' which is the name we provided when calling the method 'log_checkpoint' in the 'main.py' file. 



Checkpointing
^^^^^^^^^^^^^

Checkpointing can be particularly useful if you need to restart a job from its latest state without having to re-run it from scratch. To do this, you only need to slightly modify the function 'train' to load the latest checkpoint by default:

.. code-block:: python
    :caption: main.py

    import torch
    from core import DataLoader, OneHiddenLayer

    import mlxpy as mlxpy

    @mlxpy.launch(config_path='./configs')
    def train(ctx: mlxpy.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        # Try loading from the checkpoint
        try:
            checkpoint = logger.load_checkpoint()
            start_epoch = checkpoint['epoch']+1
            model = checkpoint['model']
        except:
            start_epoch = 0
            model = Network(n_layers = cfg.model.num_layers)


        model = model.to(cfg.data.device)
        optimizer = torch.optim.SGD(model.parameters(),
                                    lr=cfg.optimizer.lr)
        dataloader = DataLoader(cfg.data.d_int,
                                cfg.data.device)         

        # Training
        print(f"Starting from epoch: {start_epoch} ")

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

Of course, if you execute 'main.py' without further options, the logger will create a new 'log_id' where there is no checkpoint yet, so it cannot resume a previous job. Instead, you need to force the 'log_id' using the option 'logger.forced_log_id':

.. code-block:: console

   $ python main.py +mlxpy.logger.forced_log_id=1
   Starting from epoch 10
   Completed training with learning rate: 1e-3



3- Easy reading
---------------

We have already stored information about 3 runs so far. 
We can access this information easily using mlxpy's reader module, which allows querying results, grouping, and aggregating them. Let's do this interactively!


Creating a result database
^^^^^^^^^^^^^^^^^^^^^^^^^^


.. code-block:: ipython

    In [1]: import mlxpy as mlxpy

    In [2]: # Creates a database of results stored by the logger that is accessible using a reader object.
       ...: parent_log_dir = './logs/'
            reader = mlxpy.Reader(parent_log_dir)


Under the woods, the reader object creates a JSON file 'database.json' in the directory parent_log_dir and stores metadata about all runs contained in that directory. 

.. code-block:: text
   :caption: ./logs/

   logs/
   ├── 1/...
   ├── 2/...
   ├── 3/...
   └── database.json


This database allows, for instance, obtaining general information about the runs contained in the log directory 'parent_log_dir', such as the number of runs or the list of fields that are stored in the various files of the log directories: (e.g. in config.yaml, info.yaml or metrics/): 


.. code-block:: ipython

    In [3]: # Displaying the number of runs accessible to the reader
       ...: len(reader)
    Out[3]: 3

    In [4]: # Displaying all fields accessible in the database.
       ...: print(reader.fields)
    Out[4]:
                                       Type
    Fields
    config.data.d_int         <class 'int'>
    config.data.device        <class 'str'>
    config.model.num_units    <class 'int'>
    config.num_epoch          <class 'int'>
    config.optimizer.lr     <class 'float'>
    config.seed               <class 'int'>
    info.app                  <class 'str'>
    info.cmd                  <class 'str'>
    info.end_date             <class 'str'>
    info.end_time             <class 'str'>
    info.exec                 <class 'str'>
    info.hostname             <class 'str'>
    info.log_dir              <class 'str'>
    info.log_id               <class 'int'>
    info.process_id           <class 'int'>
    info.start_date           <class 'str'>
    info.start_time           <class 'str'>
    info.status               <class 'str'>
    info.user                 <class 'str'>
    info.work_dir             <class 'str'>
    train.epoch                    LAZYDATA
    train.loss                     LAZYDATA


For instance, the method 'fields' displace a table of existing fields along with their type. 
You can see that all the user config options are preceded by the prefix 'config'. 
The table also contains all fields stored in the files 'info.yaml' of the metadata directory for each run. 
Finally, all keys stored by the logger when calling the method 'log_metrics' are also available. 
Note that these keys are of type 'LAZYDATA', meaning that the database does not store these data but only a reference to them (more on this later). 





Querying the database
^^^^^^^^^^^^^^^^^^^^^
Once the database is created, the reader object allows filtering the database by the values taken by some of its fields. 
Not all fields can make a valid query. Only those obtained when displaying the attribute 'searchable' are acceptable:

.. code-block:: ipython

    In [5]: # Displaying searchable fields must start with info or config
       ...: print(reader.searchable)
    Out[5]:
                                       Type
    Fields
    config.data.d_int         <class 'int'>
    config.data.device        <class 'str'>
    config.model.num_units    <class 'int'>
    config.num_epoch          <class 'int'>
    config.optimizer.lr     <class 'float'>
    config.seed               <class 'int'>
    info.app                  <class 'str'>
    info.cmd                  <class 'str'>
    info.end_date             <class 'str'>
    info.end_time             <class 'str'>
    info.exec                 <class 'str'>
    info.hostname             <class 'str'>
    info.log_dir              <class 'str'>
    info.log_id               <class 'int'>
    info.process_id           <class 'int'>
    info.start_date           <class 'str'>
    info.start_time           <class 'str'>
    info.status               <class 'str'>
    info.user                 <class 'str'>
    info.work_dir             <class 'str'>


The 'searchable' fields must start with the prefixes: 'info.' or 'config.' to indicate that they correspond to keys in the files 'config.yaml' and 'info.yaml' of the directories 'metadata' of the logs.  Let's make a simple query and use the 'filter' method: 


.. code-block:: ipython
    
    In [6]: # Searching using a query string
       ... query = "info.status == 'COMPLETE' & config.optimizer.lr <= 0.1"
       ... results = reader.filter(query_string=query, result_format="pandas")

    In [7]: # Display the result as a pandas dataframe 
       ...: results 
    Out[7]:
       config.data.d_int  ...                                         train.loss
    0                 10  ...  [0.030253788456320763, 0.03025251068174839, 0....
    1                 10  ...  [0.030253788456320763, 0.03024102933704853, 0....


Here, we call the method 'filter' with the option 'result_format' set to 'pandas'. This allows to return the result as a pandas dataframe where the rows correspond to runs stored in the 'parent_log_dir' and matching the query. If the query is an empty string, then all entries of the database are returned.  


The dataframe's column names correspond to the fields contained in 'reader.fields'. These names are constructed as follows:
- The dot-separated flattened keys of the hierarchical options contained in the YAML file 'metadata.yaml' preceded by the prefix 'metadata'.  
- The keys of the dictionaries stored in the files contained in the 'metrics' directories (here 'train.json') preceded by the file name as a suffix (here: 'train.'). 
As you can see, the dataframe loads the content of all keys in the files 'train.json' (contained in the 'metrics' directories of each run), which might not be desirable if these files are large. 
This can be avoided using 'lazy evaluation' which we describe next.

Lazy evaluation
^^^^^^^^^^^^^^^

Instead of returning the result of the search as a pandas dataframe, which loads all the content of the, possibly large, 'train.json' file, we can return a 'mlxpy.DataDictList' object. 
This object can also be rendered as a dataframe but does not load the 'train.json' files in memory unless the corresponding fields are explicitly accessed. 



.. code-block:: ipython

    In [8]: # Returning a DataDictList as a result
       ... results = reader.filter(query_string=query)

    In [9]: # Display the result as a pandas dataframe 
       ...: results 
    Out[9]:
       config.data.d_int config.data.device  ...  train.epoch train.loss
    0                 10                cpu  ...     LAZYDATA    LAZYDATA
    1                 10                cpu  ...     LAZYDATA    LAZYDATA

    [2 rows x 39 columns]

As you can see, the content of the columns 'train.epoch' and 'train.loss' is simply marked as 'LAZYDATA', meaning that it is not loaded for now. If we try to access a specific column (e.g. 'train.loss'), DataDictList will automatically load the desired result:


.. code-block:: ipython

    In [10]: # Access a particular column of the results 
       ...: results[0]['train.loss'] 
    Out[10]:
    [0.030253788456320763, 0.03025251068174839, 0.030249962583184242, 0.030246131122112274, 0.03024103306233883, 0.030234655365347862, 0.03022700361907482, 0.030218079686164856, 0.030207885429263115, 0.030196424573659897]

The object results should be viewed as a list of dictionaries. Each element of the list corresponds to a particular run in the  'parent_log_dir' directory. The keys of each dictionary in the list are the columns of the dataframe. Finally, it is always to convert a DataDictList object to a pandas dataframe using the method 'toPandasDF'. 


Grouping and aggregation
^^^^^^^^^^^^^^^^^^^^^^^^

While it is possible to directly convert the results of a query to a pandas dataframe which supports grouping and aggregation operations, 
mlxpy also provides basic support for these operations. Let's see how this works:


.. code-block:: ipython


    In [11]: # List of group keys.
       ... group_keys = ['config.optimizer.lr']

    In [12]: # Grouping the results 
       ...: grouped_results = results.groupBy(group_keys)
       ...: print(grouped_results)
    Out[12]:
                                 config.data.d_int config.data.device  ...  train.epoch  train.loss
    config.optimizer.lr                                        ...
    0.01                                10                cpu  ...     LAZYDATA    LAZYDATA
    0.10                                10                cpu  ...     LAZYDATA    LAZYDATA

    [2 rows x 38 columns]

The output is an object of type GroupedDataDicts. It can be viewed as a dictionary whose keys are given by the different values taken by the group variables. Here the group variable is the learning rate 'config.optimizer.lr' which takes the values '0.01' and '0.10'. Hence, the keys of GroupedDataDicts are '0.01' and '0.10'. Each group (for instance the group with key '0.01') is a DataDictList object containing the different runs belonging to that group.

Finally, we can aggregate these groups according to some aggregation operations:


.. code-block:: ipython


    In [13]: # Creating the aggregation maps 
        ... from mlxpy.data_structures.contrib.aggregation_maps import AvgStd
        ... agg_maps = [AvgStd('train.loss'),AvgStd('train.epoch')]


    In [14]: # Aggregating the results 
       ...: agg_results = grouped_results.aggregate(agg_maps)
       ...: print(agg_results)
    Out[14]:
                                          train.loss_avg  ... config.optimizer.lr
    0  [0.030253788456320763, 0.03024102933704853, 0....  ...                 0.1
    1  [0.030253788456320763, 0.03025251068174839, 0....  ...                0.01

    [2 rows x 3 columns]

Here, we compute the average and standard deviation of the field 'train.loss' which contains a list of loss values. The loss values are averaged per group and the result is returned as a DataDictList object whose columns consist of:
- The resulting fields: 'train.loss_avg' and 'train.loss_std'
- The original group key: 'config.optimizer.lr'.

Of course, one can always convert these structures to a pandas dataframe at any time!


4- Advanced features
--------------------



Launching jobs using a scheduler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


If you have access to an HPC cluster, then you probably use a job scheduler for submitting jobs. 
Mlxpy allows you to combine the 'multirun' capabilities of `hydra <https://hydra.cc/>`_ with job scheduling to easily submit multiple experiments to a cluster.
 

Configuring the scheduler
"""""""""""""""""""""""""

The scheduler's options are stored in the mlxpy settings file './configs/mlxpy.yaml'. By default, the option 'use_scheduler' is set to 'False', which means that jobs will not be submitted using a scheduler. Additionally, the field 'scheduler.name' is set to 'NoScheduler' which means that no valid scheduler is defined. 

If the settings file './configs/mlxpy.yaml' does not exist or if you set the option 'mlxpy.user_scheduler' to true while still leaving the 'scheduler.name' field in the 'mlxpy.yaml' as 'NoScheduler', you will have access to an interactive platform to set up the scheduler's options from the terminal when executing the 'main.py' file:

.. code-block:: console

    python main.py +mlxpy.use_scheduler=True

    No scheduler is configured by default
    
    Would you like to select a default job scheduler now ?  (y/n):
    
    y: The job scheduler configs will be stored in the file ./configs/mlxpy.yaml
    n: No scheduler will be selected by default.
    
    Please enter your answer (y/n):

Mlxpy provides two options: 'y' or 'n'. If you choose 'n', then mlxpy skips configuration and tries to execute code without a scheduler. If you choose 'y', you'll be able to set up a scheduler. Let's select 'y':


.. code-block:: console

    You can either choose one of the job schedulers available by default,
    or define a custom one by inheriting from the abstract class <class 'mlxpy.scheduler.Scheduler'> (see documentation)

    For a default scheduler, you can choose one from this list:
    
    ['OARScheduler', 'SLURMScheduler']
    
    For a custom scheduler, you must provide the full name of the user-defined Scheduler subclass (ex. my_app.CustomScheduler):
    
     Please enter your choice (or hit Enter to skip) :


By default, Mlxpy supports two job schedulers 'OAR' and 'SLURM'.  You can also specify your custom scheduler by defining a class inheriting from the abstract class 'mlxpy.scheduler.Scheduler' and providing the full name of the class so that mlxpy can import it. Here, we select one of the default schedulers provided by mlxpy 'OARScheduler' as we have access to a cluster using the OAR scheduler:

.. code-block:: console

    Please enter your choice (or hit Enter to skip): OARScheduler

    Setting Scheduler to OARScheduler

    Default settings for mlxpy will be created in ./configs/mlxpy.yaml

Mlxpy then sets up the scheduler, updates/creates the mlxpy settings file './configs/mlxpy.yaml' with an option for using 'OARScheduler' and continues execution of the code (see next section for what is executed). We can double-check that the mlxpy settings file './configs/mlxpy.yaml' was correctly modified: 


.. code-block:: yaml
   :caption: ./configs/mlxpy.yaml

   logger: ... 
  
   scheduler:
     name: OARScheduler
     shell_path: '/bin/bash'
     shell_config_cmd: ''
     env_cmd: ''
     cleanup_cmd: ''
     option_cmd: []

   version_manager: ...

You can also directly edit the 'mlxpy.yaml' file to configure the scheduler (by setting the field scheduler.name to a valid value). 
Additionally, there are other options that the scheduler need, and that are, by default, set to an empty string for most of them. The most important option is the 'option_cmd' which specifies the resources required by the job. 
It contains a list of strings, each string providing some instruction to the scheduler (e.g.: number of cores, wall time, gpu memory). These instructions must follow the syntax required by the scheduler. 
Since we are using OAR, these options must follow OAR's syntax. 



Submitting job to a cluster queue
"""""""""""""""""""""""""""""""""

After configuring the scheduler or if it was already configured in the mlxpy file settings, mlxpy falls back into scheduling mode and creates a script for the job that is then launched using the scheduler (here: 'OAR'). 
In the console, you can see the content of the script followed by a message 'Job launched!' indicating that the scheduler succeeded in launching the job:

.. code-block:: console

    #!/bin/bash
    #OAR -n logs/5
    #OAR -E absolute_path_to/logs/5/log.stderr
    #OAR -O absolute_path_to/logs/5/log.stdout



    cd absolute_path_to/tutorial
    absolute_path_to/bin/python main.py              +mlxpy.logger.forced_log_id=12            +mlxpy.logger.parent_log_dir=absolute_path_to/logs             +mlxpy.use_scheduler=False            +mlxpy.use_version_manager=False

    [ADMISSION RULE] Set default walltime to 7200.
    [ADMISSION RULE] Modify resource description with type constraints
    OAR_JOB_ID=684995

    Job launched!


Under the woods mlxpy first assigns a 'log_id' to the run and then creates its corresponding log directory './logs/log_id' (, using the logger). 
Here, log_id=5, since this is the 5th run that we launched in './logs'. Then instead of executing the job, the scheduler creates a script 'script.sh' that is saved in './logs/log_id'. This script is then submitted automatically to the OAR cluster queue using the command: 'sbatch ./script.sh'. 
At this point, the program exits after displaying the script along with a message: 'Job launched!'.
Let's have a look at the content of the script:


.. code-block:: sh   
    :caption: ./logs/5/script.sh

    #!/bin/bash
    #OAR -n logs/5
    #OAR -E absolute_path_to/logs/5/log.stderr
    #OAR -O absolute_path_to/logs/5/log.stdout



    cd absolute_path_to_work_dir
    absolute_path_to/python main.py  +mlxpy.logger.forced_log_id=5           
    +mlxpy.logger.parent_log_dir=absolute_path_to/logs             
    +mlxpy.use_scheduler=False            
    +mlxpy.use_version_manager=False


Let's now go through this script:

1. The first line of the script specifies the shell used for running the script. 
It is determined by the scheduler's option 'shell_path' of the 'mlxpy.yaml' file settings. We chose to set it to '/bin/bash'. 
2. The next lines specify the OAR resource option provided in 'option_cmd'. When the script is created,  the OAR directive '#OAR' is automatically added before these options so that the scheduler can interpret them. You can have a look at the OAR documentation for how to set those options. 
3. The first instruction is to go to the 'working directory' set by the launcher (which can be different from the current working directory if we are using the version manager).
4. Finally, we find the instruction for executing the 'main.py' file with some additional options. 

    * First, the log_id is forced to be the same as the one assigned for the job during launching (by setting mlxpy.logger.forced_log_id=5). 
    * Then, we make sure that the 'parent_log_dir' is also the same as the one we used during job submission to the cluster. 
    * Finally, the submitted job must no longer use any scheduler or version manager anymore! That is because the script was already submitted to a cluster queue using the scheduler and must readily be executed once a resource is allocated.

The script is submitted automatically to the OAR cluster queue, so there is no need, in principle, to worry about it. 
It is only useful in case you need to debug or re-run an experiment. 

We can check that the job is assigned to a cluster queue using the command 'oarstat':

.. code-block:: console

   $ oarstat

   Job id    S User     Duration   System message
   --------- - -------- ---------- ----------------------------------------

   684627    R username 1:15:42 R=1,W=192:0:0,J=B (Karma=0.064,quota_ok)


Once, the job finishes execution, we can double-check that everything went well by inspecting the directory './logs/5' which should contain the usual logs and two additional files 'log.stdout' and 'log.stderr':



.. code-block:: text
   :caption: ./logs/
   
   logs/
   ├── 5/
   │   ├── metadata/
   │   │   ├── config.yaml
   │   │   ├── info.yaml
   │   │   └── mlxpy.yaml
   │   ├── metrics/
   │   │   ├── train.json
   │       └── .keys/
   │   │        └── metrics.yaml
   │   ├── artifacts/
   │   │   └── Checkpoint/
   │   │       └── last_ckpt.pkl
   │   ├── log.stderr
   │   ├── log.stdout
   │   └── script.sh
   │
   ├──...


Submitting several jobs to a cluster
""""""""""""""""""""""""""""""""""""

You can also launch several jobs to the cluster from a single command! Let's say, you want to vary the learning rate and use different seeds to test the robustness of the results. You can leverage the power of `hydra <https://hydra.cc/>`_ for this!

.. code-block:: console

   $ python main.py optimizer.lr=1e-3,1e-2,1e-1 seed=1,2,3,4  +mlxpy.use_scheduler=True

Here is what happens:

1- `hydra <https://hydra.cc/>`_ performs a cross-product of the options provided and creates as many jobs are needed (3x4).
2- The mlxpy's logger creates a separate directory for each one of these jobs. Each directory is assigned a unique log_id.
3- The scheduler creates a script for each of these jobs in their corresponding directory, then submits these scripts to the cluster queue.


Version management
^^^^^^^^^^^^^^^^^^

Overview
""""""""

Sometimes, there can be a delay between the time when a job is submitted and when it gets executed. This typically happens when submitting jobs to a cluster queue. 
Meanwhile, the development code might have already changed, with some potential bugs introduced! 
Without careful version management, it is hard to know for sure what code was used to produce the results. Mlxpy proposes a simple way to avoid these issues by introducing two features:
- Systematically checking for uncommitted change/ untracked files.
- Systematically copying the code from the git repository containing the executable to another 'safe' location based on the latest commit. The code is then run from this location to avoid any interference with changes introduced later to the development code and before executing a job.

Using mlxpy's version manager
"""""""""""""""""""""""""""""

Let's see how this works! We simply need to set the option 'use_version_manager' to true. This launches an interactive session where the user can tell the version manager what to do.

.. code-block:: console

   $ python main.py +mlxpy.use_version_manager=True


.. code-block:: python
    
    There are untracked files in the repository:
    
    tutorial/logs/
    
    How would you like to handle untracked files? (a/b/c)
    
    a: Add untracked files directly from here?
    b: Check again for untracked files (assuming you manually added them).
    c: Ignore untracked files.
    
    [Untracked files]: Please enter your choice (a/b/c):

First, the version manager checks for untracked files and asks the user what to do: either ignore, double-check untracked files or add the files to git. 
Here, we just choose option 'c' which ignores the untracked directory './logs/'.


The next step is to check for uncommitted changes. 


.. code-block:: python
    
    There are uncommitted changes in the repository:
    
    tutorial/main.py
    
    How would you like to handle uncommitted changes? (a/b/c)
    
    a: Create a new automatic commit before launching jobs.
    b: Check again for uncommitted changes (assuming you manually committed them).
    c: Ignore uncommitted changes.
    
    [Uncommitted changes]: Please enter your choice (a/b/c):

We see that there is one uncommitted change. The user can either ignore this, commit the changes from a different interface and check again or commit the changes from the version manager interface. Here, we just choose the option ‘a’ which creates an automatic commit of the changes.


.. code-block:: python

    Committing changes....
    
    [master e22179c] mlxpy: Automatically committing all changes

     1 files changed, 2 insertions(+), 1 deletions(-)
    
    No more uncommitted changes!
    

Finally, the version manager asks if we want to create a 'safe' copy (if it does not already exist) based on the latest commit and from which code will be executed. If not, the code is executed from the current directory.

.. code-block:: python

    Where would you like to run your code from? (a/b):
    
    a: Create a copy of the repository based on the latest commit and execute code from there.
    The copy will be created in absolute_path_to/.workdir/mlxpy/commit_hash
    b: Execute code from the main repository
    
    Please enter your answer (a/b):




We choose the safe copy! 
The copy is created in a directory named after the latest commit hash during execution time (here, the last commit was the one created by the version manager). Mlxpy then proceeds to execute the code from that copy:


.. code-block:: python

    Creating a copy of the repository at absolute_path_to/.workdir/mlxpy/commit_hash
    Starting from epoch: 0
    Completed training with a learning rate of 10.0


We can double check where the code was executed from by inspecting the 'info.yaml' file (Note that this is the 4th run, so the file should be located in ./logs/4/)


.. code-block:: yaml
   :caption: ./logs/4/metadata/info.yaml

    ...
    work_dir: absolute_path_to/.workdir/mlxpy/commit_hash/tutorial
    version_manager:
        commit_hash: f02c8e5aa1a4c71d348141543a20543a2e4671b4
        repo_path: absolute_path_to_repo 
        requirements:
        - dill==0.3.6
        - GitPython==3.1.31
        - hydra-core==1.3.2
        - omegaconf==2.2.3
        - pandas==1.2.4
        - ply==3.11
        - PyYAML==6.0
        - setuptools==52.0.0.post20210125
        - tinydb==4.7.1

If other jobs are submitted later, and if the code did not change meanwhile, then these jobs will also be executed from this same working directory. This avoids copying the same content multiple times. 

Finally, a copy of the dependencies used by the code along with their versions is also made in the field 'requirements' if the option 'mlxpy.version_manager.compute_requirements' is set to 'True'.


Using both scheduler and version manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can combine both features to run several reproducible jobs with a controlled version of the code they use.  

   $ python main.py +optimizer.lr=1e-3,1e-2,1e-1 +seed=1,2,3,4  +mlxpy.use_scheduler=True +mlxpy.use_version_manager=True

In this case, mlxpy will go through the following step:

1- Mlxpy first asks the user to set up a scheduler, if not already configured. 
2- The version manager asks the user to decide how to handle untracked/uncommitted files and whether or not to create a 'safe' directory from which the code will be run. 
3- Once the user's choices are entered, the jobs are submitted to the scheduler, and you only need to wait for the results to come!


Conclusion
^^^^^^^^^^

In this tutorial, you has an overview of the main functionalities provided by mlxpy and how to use them for performing machine learning experiments. 
I hope you can find mlxpy useful, and I'd be happy to hear your feedback and suggestions!

















