MLXP
====

What is MLXP?
^^^^^^^^^^^^^

MLXP (Machine Learning eXperimentalist for Python) package is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. 

A full documentation along with a tutorial is available in `MLXPs project page <https://inria-thoth.github.io/mlxp/>`_. A presentation of MLXP can also be found in 
`the companion paper <https://arxiv.org/abs/2402.13831>`_.  



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


How to cite
^^^^^^^^^^^

If you use MLXP in your research, please cite the following paper:

.. code-block:: bibtex 

   @Misc{Arbel2023MLXP,
     author = {Michael Arbel, Alexandre Zouaoui},
     title = {MLXP: A framework for conducting replicable Machine Learning eXperiments in Python},
     howpublished = {arXiv preprint arXiv:2402.13831},
     year = {2024},
     url = {https://arxiv.org/abs/2402.13831}
   }



Acknowledgments
^^^^^^^^^^^^^^^

- `Juliette Marrie <https://www.linkedin.com/in/juliette-marrie-5b8a59179/?originalSubdomain=fr>`_, `Romain Ménégaux <https://www.linkedin.com/in/romain-menegaux-88a147134/?originalSubdomain=fr>`_, `Pierre Wolinski <https://pierre-wolinski.fr/>`_ and `Thomas Ryckeboer <https://www.linkedin.com/in/thomas-ryckeboer-a97ab7143/?locale=en_US>`_ provided valuable feedback and suggestions to improve MLXP. 

License
^^^^^^^

MLXP is distributed under MIT license.


