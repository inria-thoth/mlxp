MLXP
====

What is MLXP?
^^^^^^^^^^^^^

MLXP (Machine Learning eXperimentalist for Python) package is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. A full documentation is available in the `MLXP's project page <https://inria-thoth.github.io/mlxp/>`_.  


Key functionalities
^^^^^^^^^^^^^^^^^^^

1. Launching several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs by adding a single decorator to the main task function.   
2. Logging outputs (metrics, artifacts, checkpoints) of a job in a uniquely assigned directory along with all metadata and configuration options to reproduce the experiment.
3. Code version management by automatically generating a deployment version of the code based on the latest git commit. 
4. Submitting jobs to a cluster using a job scheduler. 
5. Exploiting the results of several experiments by easily reading, querying, grouping, and aggregating the output of several jobs. 



Installing MLXP
^^^^^^^^^^^^^^^^

You can install MLXP in a virtualenv/conda environment where pip is installed (check which pip):


Stable release
--------------

.. code-block:: console
   
   $ pip install MLXP


Main branch
-----------

.. code-block:: console
   
   $ pip install git+https://github.com/inria-thoth/mlxp@master#egg=mlxp


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


Documentation
^^^^^^^^^^^^^

A full documentation is available in the `MLXP's official  documentation website <https://inria-thoth.github.io/mlxp/>`_.  
See the following pages for more detailled information:

`Quick start guide <https://inria-thoth.github.io/mlxp/getting_started.html>`_:  
for a simple example of how to use MLXP. 
`Tutorial <https://inria-thoth.github.io/mlxp/tutorial.html>`_: 
to get a better understanding of all functionalities provided by MLXP.
`Documentation <https://inria-thoth.github.io/mlxp/mlxp.html>`_: 
for detailed documentation.



Acknowledgments
^^^^^^^^^^^^^^^

- `Alexandre Zouaoui <https://azouaoui.me/>`_ kindly shared his python implementation for creating job scripts and submiting them to a cluster. His code served as the basis for the implementation of the Scheduling functionality. 

- `Juliette Marrie <https://www.linkedin.com/in/juliette-marrie-5b8a59179/?originalSubdomain=fr>`_, `Romain Ménégaux <https://www.linkedin.com/in/romain-menegaux-88a147134/?originalSubdomain=fr>`_ and `Pierre Wolinski <https://pierre-wolinski.fr/>`_ provided valuable feedback and suggestions to improve MLXP. 


License
^^^^^^^

MLXP is distributed under MIT license.


