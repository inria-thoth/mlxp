.. MLXP documentation master file, created by
   sphinx-quickstart on Sun Apr  2 05:53:07 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome MLXP's documentation!
==============================


MLXP (Machine Learning eXperimentalist for Python) package is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. A full documentation is available in the `MLXP's official  documentation website <https://michaelarbel.github.io/mlxp/>`_. 



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


.. toctree::
   :maxdepth: 2
   :caption: Content:

   
   guide
   mlxp


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
