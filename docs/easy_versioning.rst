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

Let's see how this works! We simply need to set the option 'use_version_manager' to true. If the interactive mode is active (interactive_mode=True), an interactive session is created where the user can tell the version manager what to do.

First, the version manager asks if we want to create a 'safe' copy (if it does not already exist) based on the latest commit and from which code will be executed. If not, the code is executed from the current directory.

.. code-block:: console

   $ python main.py +mlxp.use_version_manager=True
    
    Would you like to execute code from a backup copy based on the latest commit? (y/n):
    y: Yes (Recommended option)
    n: No. (Code will be executed from the main repository)
    Please enter you answer (y/n): y

We choose the safe copy!


.. code-block:: console

    Run will be executed from a backup directory based on the latest commit



Then, the version manager checks for untracked files and asks the user whether untracked files should be added to the git repository. 


.. code-block:: console

    There are untracked files in the repository:
    docs/easy_scheduling.rst
    docs/easy_versioning.rst
    Would you like to add untracked files? (y/n)
    y: Yes.
    n: No. Untracked files will be ignored. (Before selecting this option, please make sure to manually add untracked files)
    [Adding untracked files]: Please enter your choice (y/n): y

Here, we just choose option 'y'. As a result, the user is invited to enter the files to be tracked. 

.. code-block:: console

    Untracked files:
    docs/easy_scheduling.rst
    docs/easy_versioning.rst
    Please select files to be tracked (comma-separated) and hit Enter to skip:  




The next step is to check for uncommitted changes. 


.. code-block:: console
    
    There are uncommitted changes in the repository:

    tutorial/script.sh
    Would you like to create an automatic commit for all uncommitted changes? (y/n)
    y: Yes.
    n: No. Uncommitted changes will be ignored. (Before selecting this option, it is recommanded to manually handle uncommitted changes.)
    [Automatic commit]: Please enter your choice (y/n):

We see that there is one uncommitted change. The user can either ignore this, commit the changes from a different interface and check again or commit the changes from the version manager interface. Here, we just choose the option ‘a’ which creates an automatic commit of the changes.


.. code-block:: console

    Committing changes....
    
    [master e22179c] MLXP: Automatically committing all changes

     1 files changed, 2 insertions(+), 1 deletions(-)
    
    No more uncommitted changes!
    






The copy is created in a directory named after the latest commit hash during execution time (here, the last commit was the one created by the version manager). MLXP then proceeds to execute the code from that copy:


.. code-block:: console

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

If other jobs are submitted later, and if the code did not change meanwhile, then these jobs will also be executed from this same working directory. This avoids copying the same content multiple times. 

Finally, a copy of the dependencies used by the code along with their versions is also made in the field 'requirements' if the option 'mlxp.version_manager.compute_requirements' is set to 'True'.


Using the version manager with a job scheduler 
""""""""""""""""""""""""""""""""""""""""""""""

You can combine both features to run several reproducible jobs with a controlled version of the code they use.  

.. code-block:: console
   
   $ python main.py +optimizer.lr=1e-3,1e-2,1e-1 +seed=1,2,3,4  +mlxp.use_scheduler=True +mlxp.use_version_manager=True

In this case, MLXP will go through the following step:

1. MLXP first asks the user to set up a scheduler, if not already configured. 
2. The version manager asks the user to decide how to handle untracked/uncommitted files and whether or not to create a 'safe' directory from which the code will be run. 
3. Once the user's choices are entered, the jobs are submitted to the scheduler, and you only need to wait for the results to come!
