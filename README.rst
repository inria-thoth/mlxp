Introduction
^^^^^^^^^^^^

MLXP (Machine Learning eXperiments Python) package is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. A full documentation is available in the `MLXP's official  documentation website <https://michaelarbel.github.io/mlxp/>`_. 



Key functionalities
^^^^^^^^^^^^^^^^^^^

1. Launching several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs by adding a single decorator to the main task function.   
2. Logging outputs (metrics, artifacts, checkpoints) of a job in a uniquely assigned directory along with all metadata and configuration options to reproduce the experiment.
3. Code version management by automatically generating a deployment version of the code based on the latest git commit. 
4. Submitting jobs to a cluster using a job scheduler. 
5. Exploiting the results of several experiments by easily reading, querying, grouping, and aggregating the output of several jobs. 


License
^^^^^^^

MLXP is distributed under MIT license.

Citing MLXP
^^^^^^^^^^^^

Even though this is non-legally binding, the author kindly ask users to cite MLXP in their publications if they use 
it in their research as follows:


.. code-block:: bibtex 

   @Misc{Arbel2023MLXP,
     author = {Michae Arbel},
     title = {MLXP: },
     howpublished = {Github},
     year = {2023},
     url = {https://github.com/MichaelArbel/mlxp}
   }


Installing MLXP
^^^^^^^^^^^^^^^^

You can install MLXP either from PyPI or by cloning the GitHub.


From PyPI
---------

You can simply run the following command:

.. code-block:: console
   
   $ pip install MLXP


From GitHub
-----------

You can install this package by cloning it from the GitHub repository
and then installing it with `pip`. 


1. Clone the repository:

.. code-block:: console
   
   $ git clone git@github.com:MichaelArbel/mlxp.git

2. Change to the package directory:

.. code-block:: console
   
   $ cd mlxp

3. Install the requirements using `pip`:

.. code-block:: console
   
   $ pip install -r requirements.txt

4. Install the package:

.. code-block:: console
   
   $ pip install .

Note: You may need to use `pip3` instead of `pip` depending on your setup.




Before installing MLXP, make sure you the requirements are installed.


Requirements
------------


.. list-table::
   :header-rows: 1
   :class: left

   * - Requirements
   * - hydra-core
   * - omegaconf
   * - tinydb
   * - setuptools
   * - PyYAML
   * - pandas
   * - ply
   * - dill
   * - GitPython


Acknowledgments
^^^^^^^^^^^^^^^

I would like to acknowledge the following contributors for their contributions to the development of this package:

- `Alexandre Zouaoui <https://azouaoui.me/>`_ kindly shared his python implementation for creating job scripts and submiting them to a cluster. His code served as the basis for the implementation of the Scheduler class. While I have significantly modified the process of job submission, by integrating it with MLXpy's launching functionality, I am grateful for Alexandre's contribution which were invaluable to the development of this project.


- `Juliette Marrie <https://www.linkedin.com/in/juliette-marrie-5b8a59179/?originalSubdomain=fr>`_ tested a premature version of MLXP. I am grateful for her feedback which was extremetly helpful for shaping and improving MLXP's functionalities.  

- `Romain Ménégaux <https://www.linkedin.com/in/romain-menegaux-88a147134/?originalSubdomain=fr>`_ provided valuable feedback and suggestions to improve MLXP. He also found and reported several bugs in the software which helped improve its quality and stability. 







