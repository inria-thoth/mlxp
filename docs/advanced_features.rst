4- Advanced features
--------------------



Launching jobs using a scheduler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


If you have access to an HPC cluster, then you probably use a job scheduler for submitting jobs. 
MLXP allows you to combine the 'multirun' capabilities of `hydra <https://hydra.cc/>`_ with job scheduling to easily submit multiple experiments to a cluster.



Configuring the scheduler
"""""""""""""""""""""""""

The scheduler's options are stored in the MLXP settings file './configs/mlxpy.yaml'. By default, the option 'use_scheduler' is set to 'False', which means that jobs will not be submitted using a scheduler. Additionally, the field 'scheduler.name' is set to 'NoScheduler' which means that no valid scheduler is defined.
If the settings file './configs/mlxpy.yaml' does not exist or if you set the option 'mlxpy.user_scheduler' to true while still leaving the 'scheduler.name' field in the 'mlxpy.yaml' as 'NoScheduler', you will have access to an interactive platform to set up the scheduler's options from the terminal when executing the 'main.py' file:

.. code-block:: console

    python main.py +mlxpy.use_scheduler=True

    No scheduler is configured by default
    
    Would you like to select a default job scheduler now ?  (y/n):
    
    y: The job scheduler configs will be stored in the file ./configs/mlxpy.yaml
    n: No scheduler will be selected by default.
    
    Please enter your answer (y/n):

MLXP provides two options: 'y' or 'n'. If you choose 'n', then MLXP skips configuration and tries to execute code without a scheduler. If you choose 'y', you'll be able to set up a scheduler. Let's select 'y':


.. code-block:: console

    You can either choose one of the job schedulers available by default,
    or define a custom one by inheriting from the abstract class <class 'mlxpy.scheduler.Scheduler'> (see documentation)

    For a default scheduler, you can choose one from this list:
    
    ['OARScheduler', 'SLURMScheduler']
    
    For a custom scheduler, you must provide the full name of the user-defined Scheduler subclass (ex. my_app.CustomScheduler):
    
     Please enter your choice (or hit Enter to skip) :


By default, MLXP supports two job schedulers 'OAR' and 'SLURM'.  You can also specify your custom scheduler by defining a class inheriting from the abstract class 'mlxpy.scheduler.Scheduler' and providing the full name of the class so that MLXP can import it. Here, we select,'OARScheduler', one of the default schedulers provided by MLXP as we have access to a cluster using the OAR scheduler:

.. code-block:: console

    Please enter your choice (or hit Enter to skip): OARScheduler

    Setting Scheduler to OARScheduler

    Default settings for MLXP will be created in ./configs/mlxpy.yaml

MLXP then sets up the scheduler, updates/creates the MLXP settings file './configs/mlxpy.yaml' with an option for using 'OARScheduler' and continues execution of the code (see next section for what is executed). We can double-check that the MLXP settings file './configs/mlxpy.yaml' was correctly modified: 


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

After configuring the scheduler or if it was already configured in the MLXP file settings, MLXP falls back into scheduling mode and creates a script for the job that is then launched using the scheduler (here: 'OAR'). 
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


Under the woods MLXP first assigns a 'log_id' to the run and then creates its corresponding log directory './logs/log_id' (, using the logger). 
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

1. The first line of the script specifies the shell used for running the script. It is determined by the scheduler's option 'shell_path' of the 'mlxpy.yaml' file settings. We chose to set it to '/bin/bash'. 
2. The next lines specify the OAR resource option provided in 'option_cmd'. When the script is created,  the OAR directive '#OAR' is automatically added before these options so that the scheduler can interpret them. You can have a look at the OAR documentation for how to set those options. 
3. The first instruction is to go to the 'working directory' set by the launcher (which can be different from the current working directory if we are using the version manager).
4. Finally, we find the instructiosn for executing the 'main.py' file with some additional options:
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
   │   │   └── .keys/
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

1. `hydra <https://hydra.cc/>`_ performs a cross-product of the options provided and creates as many jobs are needed (3x4).
2. The MLXP's logger creates a separate directory for each one of these jobs. Each directory is assigned a unique log_id.
3. The scheduler creates a script for each of these jobs in their corresponding directory, then submits these scripts to the cluster queue.


Version management
^^^^^^^^^^^^^^^^^^

Sometimes, there can be a delay between the time when a job is submitted and when it gets executed. This typically happens when submitting jobs to a cluster queue. 
Meanwhile, the development code might have already changed, with some potential bugs introduced! 
Without careful version management, it is hard to know for sure what code was used to produce the results.

MLXP's version manager
"""""""""""""""""""""""

MLXP proposes a simple way to avoid these issues by introducing two features:

- Systematically checking for uncommitted change/ untracked files.
- Systematically copying the code from the git repository containing the executable to another 'safe' location based on the latest commit. The code is then run from this location to avoid any interference with changes introduced later to the development code and before executing a job.

Using MLXP's version manager
"""""""""""""""""""""""""""""

Let's see how this works! We simply need to set the option 'use_version_manager' to true. This launches an interactive session where the user can tell the version manager what to do.

.. code-block:: console

   $ python main.py +mlxpy.use_version_manager=True
    
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


.. code-block:: console
    
    There are uncommitted changes in the repository:
    
    tutorial/main.py
    
    How would you like to handle uncommitted changes? (a/b/c)
    
    a: Create a new automatic commit before launching jobs.
    b: Check again for uncommitted changes (assuming you manually committed them).
    c: Ignore uncommitted changes.
    
    [Uncommitted changes]: Please enter your choice (a/b/c):

We see that there is one uncommitted change. The user can either ignore this, commit the changes from a different interface and check again or commit the changes from the version manager interface. Here, we just choose the option ‘a’ which creates an automatic commit of the changes.


.. code-block:: console

    Committing changes....
    
    [master e22179c] MLXP: Automatically committing all changes

     1 files changed, 2 insertions(+), 1 deletions(-)
    
    No more uncommitted changes!
    

Finally, the version manager asks if we want to create a 'safe' copy (if it does not already exist) based on the latest commit and from which code will be executed. If not, the code is executed from the current directory.

.. code-block:: console

    Where would you like to run your code from? (a/b):
    
    a: Create a copy of the repository based on the latest commit and execute code from there.
    The copy will be created in absolute_path_to/.workdir/mlxpy/commit_hash
    b: Execute code from the main repository
    
    Please enter your answer (a/b):




We choose the safe copy! 
The copy is created in a directory named after the latest commit hash during execution time (here, the last commit was the one created by the version manager). MLXP then proceeds to execute the code from that copy:


.. code-block:: console

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

.. code-block:: console
   
   $ python main.py +optimizer.lr=1e-3,1e-2,1e-1 +seed=1,2,3,4  +mlxpy.use_scheduler=True +mlxpy.use_version_manager=True

In this case, MLXP will go through the following step:

1. MLXP first asks the user to set up a scheduler, if not already configured. 
2. The version manager asks the user to decide how to handle untracked/uncommitted files and whether or not to create a 'safe' directory from which the code will be run. 
3. Once the user's choices are entered, the jobs are submitted to the scheduler, and you only need to wait for the results to come!
