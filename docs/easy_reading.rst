3- Reading
----------

Here we assume that we run a number of experiments by running the following python command:


.. code-block:: console

   $ python main.py model.num_units=2,3,4 optimizer.lr=10.,1. seed=1,2,3


We can access this information easily using MLXP's reader module, which allows querying results, grouping, and aggregating them. Let's do this interactively!



Creating a result database
^^^^^^^^^^^^^^^^^^^^^^^^^^

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
   └── database.json


This database allows, for instance, obtaining general information about the runs contained in the log directory :samp:`parent_log_dir`, such as the number of runs or the list of fields that are stored in the various files of the log directories: (e.g. in :samp:`config.yaml` , :samp:`info.yaml` or :samp:`metrics/`): 


.. code-block:: ipython

   In [3]: # Displaying the number of runs accessible to the reader
      ...: len(reader)
   Out[3]: 3

   In [4]: # Displaying all fields accessible in the database.
      ...: print(reader.fields)
   Out[4]:
                                    Type
   Fields
   config.data.d_int         '<class 'int'>'
   config.data.device        '<class 'str'>'
   config.model.num_units    '<class 'int'>'
   config.num_epoch          '<class 'int'>'
   config.optimizer.lr     '<class 'float'>'
   config.seed               '<class 'int'>'
   info.app                  '<class 'str'>'
   info.cmd                  '<class 'str'>'
   info.end_date             '<class 'str'>'
   info.end_time             '<class 'str'>'
   info.exec                 '<class 'str'>'
   info.hostname             '<class 'str'>'
   info.log_dir              '<class 'str'>'
   info.log_id               '<class 'int'>'
   info.process_id           '<class 'int'>'
   info.start_date           '<class 'str'>'
   info.start_time           '<class 'str'>'
   info.status               '<class 'str'>'
   info.user                 '<class 'str'>'
   info.work_dir             '<class 'str'>'
   train.epoch                    'LAZYDATA'
   train.loss                     'LAZYDATA'
   test.loss                      'LAZYDATA'
   test.epoch                     'LAZYDATA'

For instance, the method :samp:`fields` displace a table of existing fields along with their type. 
You can see that all the user config options are preceded by the prefix :samp:`config`. 
The table also contains all fields stored in the files :samp:`info.yaml` of the metadata directory for each run. 
Finally, all keys stored by the logger when calling the method :samp:`log_metrics` are also available. 
Note that these keys are of type :samp:`LAZYDATA`, meaning that the database does not store these data but only a reference to them (more on this later). 


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


The :samp:`searchable` fields must start with the prefixes: :samp:`info.` or :samp:`config.` to indicate that they correspond to keys in the files :samp:`config.yaml` and :samp:`info.yaml` of the directories :samp:`metadata` of the logs.  Let's make a simple query and use the :samp:`filter` method: 


.. code-block:: ipython
    
    In [6]: # Searching using a query string
       ...: query = "info.status == 'COMPLETE' & config.optimizer.lr <= 100."
       ...: results = reader.filter(query_string=query, result_format="pandas")

    In [7]: # Display the result as a pandas dataframe 
       ...: results 
    Out[7]:
       config.data.d_int  ...                                         train.loss
    0                 10  ...  [0.007952751591801643, 0.0046330224722623825, ...
    1                 10  ...  [0.03218596801161766, 0.019587023183703423, 0....

    [18 rows x 44 columns]

Here, we call the method :samp:`filter` with the option :samp:`result_format` set to :samp:`pandas`. This allows to return the result as a pandas dataframe where the rows correspond to runs stored in the :samp:`parent_log_dir` and matching the query. If the query is an empty string, then all entries of the database are returned.  


The dataframe's column names correspond to the fields contained in  :samp:`reader.fields`. These names are constructed as follows:

- The dot-separated flattened keys of the hierarchical options contained in the YAML file :samp:`metadata.yaml` preceded by the prefix :samp:`metadata`.  
- The keys of the dictionaries stored in the files contained in the :samp:`metrics`  directories (here :samp:`train.json`) preceded by the file name as a suffix (here: :samp:`train.`). 

As you can see, the dataframe loads the content of all keys in the files :samp:`train.json` (contained in the :samp:`metrics` directories of each run), which might not be desirable if these files are large. 
This can be avoided using **lazy evaluation** which we describe next.

Lazy evaluation
^^^^^^^^^^^^^^^

Instead of returning the result of the search as a pandas dataframe, which loads all the content of the, possibly large, :samp:`train.json` file, we can return a :samp:`mlxp.DataFrame` object. 
This object can also be rendered as a dataframe but does not load the :samp:`train.json` files in memory unless the corresponding fields are explicitly accessed. 



.. code-block:: ipython

    In [8]: # Returning a DataFrame as a result
       ... results = reader.filter(query_string=query)

    In [9]: # Display the result as a pandas dataframe 
       ...: results 
    Out[9]:
       config.data.d_int config.data.device  ...  train.epoch train.loss
    0                 10                cpu  ...     LAZYDATA    LAZYDATA
    1                 10                cpu  ...     LAZYDATA    LAZYDATA

    [18 rows x 44 columns]

As you can see, the content of the columns :samp:`train.epoch` and :samp:`train.loss` is simply marked as :samp:`LAZYDATA`, meaning that it is not loaded for now. If we try to access a specific column (e.g. :samp:`train.loss`), :samp:`DataFrame` will automatically load the desired result:


.. code-block:: ipython

    In [10]: # Access a particular column of the results 
       ...: results[0]['train.loss'] 
    Out[10]:
    [0.007952751591801643, 0.0046330224722623825, 0.002196301706135273, 0.0019588489085435867, 0.0023327688686549664, 0.002409915439784527, 0.0011680149473249912, 0.004345299676060677, 0.05447549372911453, 1.3118325471878052]

The object results should be viewed as a list of dictionaries. Each element of the list corresponds to a particular run in the :samp:`parent_log_dir` directory. The keys of each dictionary in the list are the columns of the dataframe. Finally, it is always to convert a :samp:`DataFrame` object to a pandas dataframe using the method :samp:`toPandas`. 

Finally, it is possible to get a list of all configurations that vary accross the different runs;

.. code-block:: ipython

    In [10]: # Inspect configurations that vary accross runs
       ...: results.config_diff()
    Out[10]:
    ['config.model.num_units', 'config.optimizer.lr', 'config.seed']



Grouping and aggregation
^^^^^^^^^^^^^^^^^^^^^^^^

While it is possible to directly convert the results of a query to a pandas dataframe which supports grouping and aggregation operations, 
MLXP also provides basic support for these operations. Let's see how this works:


.. code-block:: ipython


    In [11]: # List of group keys.
       ...: group_keys = ['config.optimizer.lr']

    In [12]: # Grouping the results 
       ...: grouped_results = results.groupby(group_keys)
       ...: print(grouped_results)
    Out[12]:
                           config.data.d_int config.data.device   config.model.num_units  config.num_epoch  ...   test.epoch  test.loss train.epoch train.loss
    config.optimizer.lr                                                                                     ...
    1.0                 0                 10                 cpu                       3                10  ...    LAZYDATA   LAZYDATA     LAZYDATA   LAZYDATA
                        1                 10                 cpu                       3                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        2                 10                 cpu                       3                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        3                 10                 cpu                       4                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        4                 10                 cpu                       4                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        5                 10                 cpu                       4                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        6                 10                 cpu                       2                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        7                 10                 cpu                       2                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        8                 10                 cpu                       2                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
    10.0                0                 10                 cpu                       2                10  ...    LAZYDATA   LAZYDATA     LAZYDATA   LAZYDATA
                        1                 10                 cpu                       4                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        2                 10                 cpu                       4                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        3                 10                 cpu                       4                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        4                 10                 cpu                       2                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        5                 10                 cpu                       2                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        6                 10                 cpu                       3                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        7                 10                 cpu                       3                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
                        8                 10                 cpu                       3                10  ...     LAZYDATA   LAZYDATA    LAZYDATA   LAZYDATA
 
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
                                                            fmean.train.loss                                     fmean.train.epoch
    config.optimizer.lr
    1.0                 0  [0.022193991630855534, 0.014857375011261966, 0...  [ 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, ...
    10.0                0  [0.022193991630855534, 0.006496786553826597, 0...  [ 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, ...


Here, we compute the average and standard deviation of the field :samp:`train.loss` which contains a list of loss values. The loss values are averaged per group and the result is returned as a :samp:`DataFrame` object whose columns consist of:

- The resulting fields: :samp:`fmean.train.loss` and :samp:`fmean.train.epoch`
- The original group key: :samp:`config.optimizer.lr`.

Of course, one can always convert these structures to a pandas dataframe at any time!


Selecting and filtering
^^^^^^^^^^^^^^^^^^^^^^^

Dataframes and their grouped versions come with two  powerful methods: filter and select. the filter method  allows to filter a dataframe (even by groups) according to some user-defined filter function. Finally, the select method of a grouped dataframe allows extracting groups given their keys. 

We will now combine all these methods to find the best performing learning rate for each model choice according to the average training loss and compute the average test loss of the best performing learning rate for each model choice. 



.. code-block:: ipython


    In [15]: # Finding the best performing hyper-parameters
        ...: def maximum(x):
        ...:    import numpy as np
        ...:    x = np.array(x)
        ...:    return x[:,-1]==np.max(x[:,-1])
        ...: group_keys = ['config.model.num_units','config.optimizer.lr']         
        ...: methods_keys = ['config.model.num_units']

        ...: best_keys = results.groupby(group_keys)\
        ...:                      .aggregate((mean,'train.loss'),ungroup=True)\
        ...:                      .filter((maximum,'fmean.train.loss'), bygroups = methods_keys)\
        ...:                      .groupby(group_keys).keys()

    In [16]: # Extracting the best results 
        ...: filtered_results = results.groupby(group_keys)\
        ...:                     .select(best_keys)\
        ...:                     .aggregate((mean,'test.loss'),ungroup=True)\
        ...:                     .groupby(methods_keys)
        ...: print(filtered_results)
    Out[16]:
                                                                fmean.test.loss  c onfig.model.num_un its  config.optimi zer.lr
    config.model.num_units
    2                      0  [0.0017979409814658706,  0.0001486237729694757,...                       2                 10.0
    3                      0  [0.0007184867955337895,  0.00029363077399803143...                       3                  1.0
    4                      0  [0.00011732726838105476,  2.5671832071494935e-0...                       4                 10.0


