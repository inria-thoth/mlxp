.. MLXP documentation master file, created by
   sphinx-quickstart on Sun Apr  2 05:53:07 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome MLXP's documentation!
==============================


MLXP (Machine Learning eXperimentalist for Python) package is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. The source code is available in `MLXP's GitHub repository <https://github.com/inria-thoth/mlxp>`_. 



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
     title = {MLXP: A framework for conducting machine learning experiments in python},
     howpublished = {Github},
     year = {2023},
     url = {https://github.com/MichaelArbel/mlxp}
   }

Acknowledgments
^^^^^^^^^^^^^^^

I would like to acknowledge the following contributors for their contributions to the development of this package:

- `Alexandre Zouaoui <https://azouaoui.me/>`_ kindly shared his python implementation for creating job scripts and submiting them to a cluster. His code served as the basis for the implementation of the Scheduler class. While I have significantly modified the process of job submission, by integrating it with MLXpy's launching functionality, I am grateful for Alexandre's contribution which were invaluable to the development of this project.

- `Juliette Marrie <https://www.linkedin.com/in/juliette-marrie-5b8a59179/?originalSubdomain=fr>`_ tested a premature version of MLXP. I am grateful for her feedback which was extremetly helpful for shaping and improving MLXP's functionalities.  

- `Romain Ménégaux <https://www.linkedin.com/in/romain-menegaux-88a147134/?originalSubdomain=fr>`_ and `Pierre Wolinski <https://pierre-wolinski.fr/>`_ provided valuable feedback and suggestions to improve MLXP. They also found and reported several bugs in the software which helped improve its quality and stability. 



Tables of content
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Content:

   
   guide
   mlxp


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
