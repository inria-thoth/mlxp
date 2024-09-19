3- Reading
----------

Here we assume that we run a number of experiments by running the following python command:


.. code-block:: console

   $ python main.py model.num_units=2,3,4 optimizer.lr=10.,1. seed=1,2,3


We can access this information easily using MLXP's reader module, which allows querying results, grouping, and aggregating them. Let's do this interactively!



1. Creating a result database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We first start by creating a :samp:`reader` objects that interacts with the logs of multiple runs contained in the same parent directory (here :samp:`./logs/`): 

.. code-block:: ipython

    In [1]: import mlxp

    In [2]: # Creates a database of results stored by the logger that is accessible using a reader object.
       ...: parent_log_dir = './logs/'
            reader = mlxp.Reader(parent_log_dir)


Under the woods, the reader object creates a JSON file :samp:`database.json` in the directory :samp:`parent_log_dir` and stores metadata about all runs contained in that directory. 

.. code-block:: text
   :caption: ./logs/

   logs/
   ├── 1/...
   ├── 2/...
   ├── 3/...
   ├── ...
   └── database.json


This database allows, for instance, obtaining general information about the runs contained in the log directory :samp:`parent_log_dir`, such as the number of runs or the list of fields that are stored in the various files of the log directories: (e.g. in :samp:`config.yaml` , :samp:`info.yaml` or :samp:`metrics/`): 


.. code-block:: ipython

   In [3]: # Displaying the number of runs accessible to the reader
      ...: len(reader)
   Out[3]: 18

   In [4]: # Displaying all fields accessible in the database.
      ...: print(reader.fields)
   Out[4]:
                                                   Type
    Fields
    artifact.pickle.                           Artifact
    config.data.d_int                     <class 'int'>
    config.data.device                    <class 'str'>
    config.model.num_units                <class 'int'>
    config.num_epoch                      <class 'int'>
    config.optimizer.lr                 <class 'float'>
    config.seed                           <class 'int'>
    info.current_file_path                <class 'str'>
    info.end_date                         <class 'str'>
    info.end_time                         <class 'str'>
    info.executable                       <class 'str'>
    info.hostname                         <class 'str'>
    info.logger.artifacts_dir             <class 'str'>
    info.logger.log_dir                   <class 'str'>
    info.logger.log_id                    <class 'int'>
    info.logger.metadata_dir              <class 'str'>
    info.logger.metrics_dir               <class 'str'>
    info.process_id                       <class 'int'>
    info.scheduler.scheduler_job_id       <class 'str'>
    info.start_date                       <class 'str'>
    info.start_time                       <class 'str'>
    info.status                           <class 'str'>
    info.version_manager             <class 'NoneType'>
    info.work_dir                         <class 'str'>
    test.epoch                                   METRIC
    test.loss                                    METRIC
    train.epoch                                  METRIC
    train.loss                                   METRIC

For instance, the method :samp:`fields` displace a table of existing fields along with their type. 
You can see that all the user config options are preceded by the prefix :samp:`config`. 
The table also contains all fields stored in the files :samp:`info.yaml` of the metadata directory for each run. 
Finally, all keys stored by the logger when calling the method :samp:`log_metrics` are also available. 
Note that these keys are of type :samp:`METRIC` or :samp:`ARTIFACT`, meaning that the database does not store these data but only a reference to them (more on this later). 



Refreshing the database
=======================

By default, the database file :samp:`database.json` is created only once. However, if the directory structure changed meanwhile (ex: more experiments were added), it is possible to refresh the database by setting the option :samp:`refresh` to :samp:`True` when creating the reader object: 

.. code-block:: ipython

    In [2]: # Creates a database of results stored by the logger that is accessible using a reader object.
       ...: parent_log_dir = './logs/'
            reader = mlxp.Reader(parent_log_dir, refresh=True)


Database location
=================

.. note:: By default, the database is located under the log directory containing all runs (here :samp:`./logs/`). In some cases, the user has only reading access to it, for instance, if the runs were created by a different user. In this case, the reader will fail to create the database file :samp:`database.json` under the log directory. To prevent this error from happening, it is possible to create the database file in a different directory with writing access by passing the option :samp:`dst_dir` to the reader constructor:

.. code-block:: ipython

    In [2]: # Creates a database of results stored by the logger that is accessible using a reader object.
       ...: parent_log_dir = './logs/'
            reader = mlxp.Reader(parent_log_dir, dst_dir='path/to/database/')


2. Querying the database
^^^^^^^^^^^^^^^^^^^^^^^^
Once the database is created, the reader object allows filtering the database by the values taken by some of its fields. 


Searchable field
================

Not all fields can make a valid query. Only those obtained when displaying the attribute 'searchable' are acceptable:

.. code-block:: ipython

    In [5]: # Displaying searchable fields must start with info or config
       ...: print(reader.searchable)
    Out[5]:
                                       Type
    Fields
    config.data.d_int         '<class 'int'>'
    config.data.device        '<class 'str'>'
    config.model.num_units    '<class 'int'>'
    config.num_epoch          '<class 'int'>'
    config.optimizer.lr     '<class 'float'>'
    config.seed               '<class 'int'>'
    info.executable           '<class 'str'>'
    info.cmd                  '<class 'str'>'
    info.end_date             '<class 'str'>'
    info.end_time             '<class 'str'>'    
    info.current_file_path    '<class 'str'>'
    info.hostname             '<class 'str'>'
    info.log_dir              '<class 'str'>'
    info.log_id               '<class 'int'>'
    info.process_id           '<class 'int'>'
    info.start_date           '<class 'str'>'
    info.start_time           '<class 'str'>'
    info.status               '<class 'str'>'
    info.user                 '<class 'str'>'
    info.work_dir             '<class 'str'>'


The :samp:`searchable` fields must start with the prefixes: :samp:`info.` or :samp:`config.` to indicate that they correspond to keys in the files :samp:`config.yaml` and :samp:`info.yaml` of the directories :samp:`metadata` of the logs.   

The filter method
=================

Let's make a simple query and use the :samp:`filter` method:

.. code-block:: ipython
    
    In [6]: # Searching using a query string
       ...: query = "info.status == 'COMPLETE' & config.model.num_units <4 "
       ...: results = reader.filter(query_string=query, result_format="pandas")

    In [7]: # Display the result as a pandas dataframe 
       ...: results 
    Out[7]:
                                         artifact.pickle.  ...                                         train.loss
    0   {'last_ckpt.pkl': <mlxp.data_structures.artifa...  ...  [0.007952751591801643, 0.0046330224722623825, ...
    1   {'last_ckpt.pkl': <mlxp.data_structures.artifa...  ...  [0.03218596801161766, 0.019587023183703423, 0....

    [12 rows x 44 columns]

Here, we call the method :samp:`filter` with the option :samp:`result_format` set to :samp:`pandas`. This allows to return the result as a pandas dataframe where the rows correspond to runs stored in the :samp:`parent_log_dir` and matching the query. If the query is an empty string, then all entries of the database are returned.  


The dataframe's column names correspond to the fields contained in  :samp:`reader.fields`. These names are constructed as follows:

- **Metadata columns:** They represent the options contained in the YAML files :samp:`config.yaml` and :samp:`info.yaml`. The column names are constructed as dot-separated flattened keys of the hierarchical options contained in the YAML files :samp:`config.yaml` and :samp:`info.yaml` preceded by the prefixes :samp:`config` or  :samp:`info`. 
- **Metrics columns:** They represent the content of the metrics dictionaries stored using the method :samp:`log_metrics` and wich are stored in JSON files under the :samp:`metrics` directory (ex :samp:`metrics/train.json`). The column names are constructed using the metrics dictionary keys preceded by the file name containing them as a prefix (ex: :samp:`train.loss`). Each field of a metrics column is a list of all values taken by a particular key accross all the metrics dictionaries stored in a given JSON file.
- **Artifact columns:** They represent the content of the artifacts stored using the method :samp:`log_artifacts` or :samp:`log_checkpoint` and which are stored in the :samp:`artifacts` directory. The column names are constructed as a dot-separed version of the relative parent path of each artifact w.r.t. log directory (ie: :samp:`artifact/artifact_type/path/to/parent_dir` becomes :samp:`artifact.artifact_type.path.to.parent_dir`). For more details on loading artifacts, see the section :ref:`loading_artifacts`.

As you can see, the dataframe loads the content of all keys in the files :samp:`train.json` (contained in the :samp:`metrics` directories of each run), which might not be desirable if these files are large. 
This can be avoided using **lazy evaluation** which we describe next.

3. The mlxp.DataFrame object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Instead of returning the result of the search as a pandas dataframe, which loads all the content of the, possibly large, :samp:`train.json` file, we can return a :samp:`mlxp.DataFrame` object. 
This object can also be rendered as a dataframe but does not load the :samp:`train.json` files in memory unless the corresponding fields are explicitly accessed. 



.. code-block:: ipython

    In [8]: # Returning an mlxp.DataFrame as a result
       ... results = reader.filter(query_string=query)

    In [9]: # Display the result as a pandas dataframe 
       ...: results 
    Out[9]:
       artifact.pickle.  config.data.d_int config.data.device  ...  test.loss  train.epoch  train.loss
    0          ARTIFACT                 10                cpu  ...     METRIC       METRIC      METRIC
    1          ARTIFACT                 10                cpu  ...     METRIC       METRIC      METRIC


    [18 rows x 44 columns]

Lazy evaluation of metrics
==========================

The content of the columns :samp:`train.epoch` and :samp:`train.loss` is simply marked as :samp:`METRIC`, meaning that it is not loaded for now. If we try to access a specific column (e.g. :samp:`train.loss`), :samp:`DataFrame` will automatically load the desired result:


.. code-block:: ipython

    In [10]: # Access a particular column of the results 
       ...: results[0]['train.loss'] 
    Out[10]:
    [0.007952751591801643, 0.0046330224722623825, 0.002196301706135273, 0.0019588489085435867, 0.0023327688686549664, 0.002409915439784527, 0.0011680149473249912, 0.004345299676060677, 0.05447549372911453, 1.3118325471878052]

The object results should be viewed as a list of dictionaries. Each element of the list corresponds to a particular run in the :samp:`parent_log_dir` directory. The keys of each dictionary in the list are the columns of the dataframe. Finally, it is always to convert a :samp:`DataFrame` object to a pandas dataframe using the method :samp:`toPandas`. 


.. _loading_artifacts:

Lazy loading of artifacts
=========================
The reader automatically detects all artifacts that were created and group them by their parent directories. More precisely, an artifact colum is always of the form :samp:`artifact.artifact_type.path.to.parent_dir` which is a dot separated version of the directory :samp:`artifact/artifact_type/path.to.parent_dir` containing some artifacts of the same type :samp:`artifact_type`. In our example, the column :samp:`artifact.pickle.` represents the path to the directory :samp:`artifact/pickle` containing the artifact :samp:`last_ckpt.pkl`. 

When creating the dataframe :samp:`results`, the artifacts in the directory :samp:`artifact/pickle`  :samp:`last_ckpt.pkl` are not loaded. This is indicated by the fact that the content of the field :samp:`artifact.pickle.` is simply marked as :samp:`ARTIFACT`. However, as soon as a specific artifact field is accessed, the dataframe :samp:`results` creates a dictionary containing the file names and the corresponding artifact objects. 

.. code-block:: ipython

    In [10]: # Access a particular column of the results 
       ...: art = results[0]['artifact.pickle.']
       ...: art
    Out[10]:
    {'last_ckpt.pkl': <mlxp.data_structures.artifact.Artifact at 0x7f7c3f3e9f10>}

The returned object (here: :samp:`art`) corresponds to column :samp:`artifact.pickle.` of the first row of the dataframe. It is a dictionary whose keys are the file names stored under :samp:`artifact/pickle` and the values are instances of a special :samp:`Artifact` class reprenting each file. 
Loading the actual content of each file can be done using the method :samp:`load` of the :samp:`Artifact` class, without the need for providing any additional argument: 

.. code-block:: ipython

    In [10]: # Loading an artifact
       ...: art['last_ckpt.pkl'].load()
    Out[10]:
    {'model': OneHiddenLayer(
      (linear1): Linear(in_features=10, out_features=2, bias=True)
      (linear2): Linear(in_features=1, out_features=2, bias=False)
      (non_linearity): SiLU()
    ), 'epoch': 9}

The above call returns the content of the file :samp:`last_ckpt.pkl` stored in the directory :samp:`artifact/pickle` corresponding to the first row in the results dataframe.

Under the hood, the method :samp:`load` calls the appropriate loading method depending on the artifact type (here: 'pickle'). If the artifact has a custom type, then mlxp recovers the custom load function provided by the user that was registered using :samp:`register_artifact_type` prior to saving the artifact.


Configuration differences between runs
======================================

When running multiple experiments that have a similar structure but vary only by some specific option values, tt is often useful easily recover the options that varies accross the different runs. This can be done using the method :samp:`diff` of the :samp:`DataFrame` object. 

.. code-block:: ipython

    In [10]: # Inspect configurations that vary accross runs
       ...: results.diff()
    Out[10]:
    ['config.model.num_units', 'config.optimizer.lr', 'config.seed']


The displayed keys exactly match the options passed to the python script :samp:`main.py` when running the experiments.

.. note:: By default, the method  :samp:`diff` only compares column values that start with the prefix :samp:`config`, as these are the ones that are often most relevant for the user. It is possible, however, to modify this behavior by passing a different suffix to the method :samp:`diff` using the option :samp:`start_key`.





Grouping and aggregation
========================

While it is possible to directly convert the results of a query to a pandas dataframe which supports grouping and aggregation operations, 
MLXP also provides basic support for these operations. Let's see how this works:


.. code-block:: ipython


    In [11]: # List of group keys.
       ...: group_keys = ['config.optimizer.lr']

    In [12]: # Grouping the results 
       ...: grouped_results = results.groupby(group_keys)
       ...: print(grouped_results)
    Out[12]:
                          artifact.pickle.  config.data.d_int  ... train.epoch  train.loss
    config.optimizer.lr                                        ...
    1.0                 0         ARTIFACT                 10  ...      METRIC      METRIC
                        1         ARTIFACT                 10  ...      METRIC      METRIC
                        2         ARTIFACT                 10  ...      METRIC      METRIC
                        3         ARTIFACT                 10  ...      METRIC      METRIC
                        4         ARTIFACT                 10  ...      METRIC      METRIC
                        5         ARTIFACT                 10  ...      METRIC      METRIC
                        6         ARTIFACT                 10  ...      METRIC      METRIC
                        7         ARTIFACT                 10  ...      METRIC      METRIC
                        8         ARTIFACT                 10  ...      METRIC      METRIC
    10.0                0         ARTIFACT                 10  ...      METRIC      METRIC
                        1         ARTIFACT                 10  ...      METRIC      METRIC
                        2         ARTIFACT                 10  ...      METRIC      METRIC
                        3         ARTIFACT                 10  ...      METRIC      METRIC
                        4         ARTIFACT                 10  ...      METRIC      METRIC
                        5         ARTIFACT                 10  ...      METRIC      METRIC
                        6         ARTIFACT                 10  ...      METRIC      METRIC
                        7         ARTIFACT                 10  ...      METRIC      METRIC
                        8         ARTIFACT                 10  ...      METRIC      METRIC
 
    [18 rows x 44 columns]


The output is an object of type :samp:`GroupedDataFrame`. It can be viewed as a dictionary whose keys are given by the different values taken by the group variables. Here the group variable is the learning rate :samp:`config.optimizer.lr` which takes the values  :samp:`0.01` and :samp:`0.10`. Hence, the keys of :samp:`GroupedDataFrame` are :samp:`0.01` and :samp:`0.10`. Each group (for instance the group with key :samp:`0.01`) is a :samp:`DataFrame` object containing the different runs belonging to that group.

Finally, we can aggregate these groups according to some aggregation operations:


.. code-block:: ipython


    In [13]: # Creating the aggregation map 
        ... def mean(x):
        ...    import numpy as np
        ...    x = np.array(x)
        ...    return np.mean(x,axis=0)
        ...: agg_maps = (mean,('train.loss', 'train.epoch'))


    In [14]: # Aggregating the results 
        ...: agg_results = grouped_results.aggregate(agg_maps)
        ...: print(agg_results)
    Out[14]:
                                                            fmean.train.loss                                   fmean.train.epoch
    config.optimizer.lr
    1.0                 0  [0.022193991630855534, 0.014857375011261966, 0...  [ 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, ...
    10.0                0  [0.022193991630855534, 0.006496786553826597, 0...  [ 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, ...


Here, we compute the average and standard deviation of the field :samp:`train.loss` which contains a list of loss values. The loss values are averaged per group and the result is returned as a :samp:`DataFrame` object whose columns consist of:

- The resulting fields: :samp:`fmean.train.loss` and :samp:`fmean.train.epoch`
- The original group key: :samp:`config.optimizer.lr`.

Of course, one can always convert these structures to a pandas dataframe at any time!


Selecting and filtering
=======================

Dataframes and their grouped versions come with two  powerful methods: filter and select. the filter method  allows to filter a dataframe (even by groups) according to some user-defined filter function. Finally, the select method of a grouped dataframe allows extracting groups given their keys. 

We will now combine all these methods to find the best performing learning rate for each model choice according to the average training loss and compute the average test loss of the best performing learning rate for each model choice. 



.. code-block:: ipython


    In [15]: # Finding the best performing hyper-parameters
        ...: def argmin(x):
        ...:    import numpy as np
        ...:    x = np.array(x)
        ...:    return x[:,-1]==np.min(x[:,-1])
        ...: group_keys = ['config.model.num_units','config.optimizer.lr']         
        ...: methods_keys = ['config.model.num_units']
        ...: grouped_res = results.groupby(group_keys)

        ...: best_results = grouped_res.aggregate((mean,'train.loss'))\
        ...:                           .filter((argmin,'fmean.train.loss'), bygroups = methods_keys)

    In [16]: # Extracting the best results 
        ...: filtered_results = grouped_res.select(best_results.keys())\
                        .aggregate((mean,'test.loss'))
        ...: print(filtered_results)
    Out[16]:
                                                                                    fmean.test.loss
    config.model.num_units config.optimizer.lr
    2                      1.0                 0  [0.0017979409814658706, 0.0005170967701183023,...
    3                      10.0                0  [0.0007184867955337895, 2.5653200725978367e-05...
    4                      1.0                 0  [0.00011732726838105476, 9.964336470179331e-05...


