Version management
------------------

Sometimes, there can be a delay between the time when a job is submitted and when it gets executed. This typically happens when submitting jobs to a cluster queue. 
Meanwhile, the development code might have already changed, with some potential bugs introduced! 
Without careful version management, it is hard to know for sure what code was used to produce the results.

MLXP's version manager
^^^^^^^^^^^^^^^^^^^^^^

MLXP proposes a simple way to avoid these issues by introducing two features:

- Requiring the code to be in a git repository
- Systematically checking for uncommitted change/ untracked files.
- Systematically copying the code from the git repository containing the executable to another 'safe' location based on the latest commit. The code is then run from this location to avoid any interference with changes introduced later to the development code and before executing a job.

Using MLXP's version manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's see how this works! We simply need to set the option 'use_version_manager' to true and make sure the code belong to a git repository. Depending on whether the interactive mode is active (mlxp.interactive_mode=True) or not, an interactive session is created where the user can tell the version manager what to do or the job is executed from on a copy of the code based on the latest commit. 

Without the interactive mode
""""""""""""""""""""""""""""

If the version manager is used without the interative mode, a copy of the code based on the latest commit is created, if it does not already exists. It is located in a directory of the form parent_work_dir/repo_name/commit_hash, where 'parent_work_dir' is provided by the user in the mlxp config file, 'repo_name' is the name of the git repository and 'commit_hash' is the latest commit's hash. 
 
MLXP then proceeds to execute the code from that copy:


.. code-block:: console

   $ python main.py +mlxp.use_version_manager=True

    Creating a copy of the repository at absolute_path_to/.workdir/mlxp/commit_hash
    Starting from epoch: 0
    Completed training with a learning rate of 10.0


We can double check where the code was executed from by inspecting the 'info.yaml' file (Note that this is the 4th run, so the file should be located in ./logs/4/)


.. code-block:: yaml
   :caption: ./logs/4/metadata/info.yaml

    ...
    work_dir: absolute_path_to/.workdir/mlxp/commit_hash/tutorial
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

If other jobs are submitted later, and if the code did not change meanwhile, these jobs will also be executed from this same working directory. This avoids copying the same content multiple times. 

Finally, a copy of the dependencies used by the code along with their versions is also made in the field 'requirements' if the option 'mlxp.version_manager.compute_requirements' is set to 'True'.



With the interactive mode
"""""""""""""""""""""""""

When the interactive mode is active, the version manager checks for untracked files and uncommited changes and asks if how to handle those before executing the code. 




First, the version manager checks for untracked files and asks the user whether untracked files should be added to the git repository. 


.. code-block:: console

    There are untracked files in the repository:
    tutorial/script.sh
    Please select files to be tracked (comma-separated) and hit Enter to skip: 

Here, we just hit Enter to skip. The next step is to check for uncommitted changes. 

.. code-block:: console
    
    There are uncommitted changes in the repository:

    tutorial/main.py
    Would you like to create an automatic commit for all uncommitted changes? (y/n)
    y: Yes.
    n: No. Uncommitted changes will be ignored. (Before selecting this option, it is recommanded to manually handle uncommitted changes.)
    [Automatic commit]: Please enter your choice (y/n):

We see that there is one uncommitted change. The user can either ignore it or create an automatic commit from the version manager interface. Here, we just choose the option ‘y’ which creates an automatic commit of the changes.


.. code-block:: console

    Commiting changes....

     1 files changed, 4 insertions(+), 3 deletions(-)
     create mode 100644 tutorial/script.sh



Then, the version manager asks if we want to create a backup copy (if it does not already exist) based on the latest commit and from which code will be executed. If not, the code is executed from the current directory.

.. code-block:: console

   $ python main.py +mlxp.use_version_manager=True
    
    Would you like to execute code from a backup copy based on the latest commit? (y/n):
    y: Yes (Recommended option)
    n: No. (Code will be executed from the main repository)
    Please enter you answer (y/n): y

We choose the safe copy!


.. code-block:: console

    Run will be executed from a backup directory based on the latest commit


Finally, the version manager creates the backup copy of the code based on the latest commit and runs it from there, just like in the non-interactive mode. 


Using the version manager with a job scheduler 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can combine both features to run several reproducible jobs with a controlled version of the code they use. For this, you can create a script (here 'script.sh') containing all the jobs you need to run as well as the options to your scheduler. You'll need to activate the version manager when executing each command.

    .. code-block:: console

      #!/bin/bash

      #OAR -l core=1, walltime=6:00:00
      #OAR -t besteffort
      #OAR -t idempotent

      python main.py  optimizer.lr=10.,1. seed=1,2 + mlxp.use_version_manager=True
      python main.py  model.num_units=100,200 seed=1,2 + mlxp.use_version_manager=True

Now you simply need to submit your jobs using mlxpsub:


    .. code-block:: console

      mlxpsub script.sh


In this case, MLXP will go through the following step:


1. The version manager asks the user to decide how to handle untracked/uncommitted files and whether or not to create a 'safe' directory from which the code will be run. 
2. Once the user's choices are entered, the jobs are created and submitted to the scheduler, and you only need to wait for the results to come!
