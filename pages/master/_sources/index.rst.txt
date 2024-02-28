.. MLXP documentation master file, created by
   sphinx-quickstart on Sun Apr  2 05:53:07 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to MLXP's documentation!
================================


MLXP (Machine Learning eXperimentalist for Python) package is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. The source code is available in `MLXP's GitHub repository <https://github.com/inria-thoth/mlxp>`_. 



Key functionalities
^^^^^^^^^^^^^^^^^^^

1. Launching several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs by adding a single decorator to the main task function.   
2. Logging outputs (metrics, artifacts, checkpoints) of a job in a uniquely assigned directory along with all metadata and configuration options to reproduce the experiment.
3. Code version management by automatically generating a deployment version of the code based on the latest git commit. 
4. Submitting jobs to a cluster using a job scheduler. 
5. Exploiting the results of several experiments by easily reading, querying, grouping, and aggregating the output of several jobs. 

.. |green| image:: images/Green-checkmark.png
   :width: 20px
   :align: middle

.. |red| image:: images/red_checkmark.png
   :width: 20px
   :align: middle


+-----------------------------+-----------------+-----------------+-----------------+
| Features                    |      MLXP       | MLFlow tracking | Weights & Biases|
+=============================+=================+=================+=================+
| Configuration management    |     |green|     |      |red|      |      |red|      |
+-----------------------------+-----------------+-----------------+-----------------+
| Hyperparameter Sweeps       |     |green|     |      |red|      |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Launching/Job submission    |     |green|     |      |red|      |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Logging/Tracking            |     |green|     |     |green|     |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Experiment Search/Filtering |     |green|     |     |green|     |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Experiment Comparison       |     |green|     |     |green|     |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Lazy loading results        |     |green|     |      |red|      |      |red|      |
+-----------------------------+-----------------+-----------------+-----------------+
| Code versioning             |     |green|     |     |green|     |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Code version checking       |     |green|     |      |red|      |      |red|      |
+-----------------------------+-----------------+-----------------+-----------------+
| Model Versioning            |      |red|      |     |green|     |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Interactive Visualizations  |      |red|      |     |green|     |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+
| Collaboration and Sharing   |      |red|      |     |green|     |     |green|     |
+-----------------------------+-----------------+-----------------+-----------------+




License
^^^^^^^

MLXP is distributed under MIT license.

Citing MLXP
^^^^^^^^^^^^

Even though this is non-legally binding, the author kindly ask users to cite MLXP in their publications if they use 
it in their research as follows:


.. code-block:: bibtex 

   @Misc{mlxp2024,
     author = {Michael Arbel, Alexandre Zouaoui},
     title = {MLXP: A framework for conducting replicable Machine Learning eXperiments in Python},
     howpublished = {arXiv preprint arXiv:2402.13831},
     year = {2024},
     url = {https://arxiv.org/abs/2402.13831}
   }

Acknowledgments
^^^^^^^^^^^^^^^


The authors would like to thank the following people for their valuable feedback and contributions to the development of MLXP: 


- `Juliette Marrie <https://www.linkedin.com/in/juliette-marrie-5b8a59179/?originalSubdomain=fr>`_ tested an early version of MLXP. We are grateful for her feedback which was extremetly helpful for shaping and improving MLXP's functionalities.  

- `Romain Ménégaux <https://www.linkedin.com/in/romain-menegaux-88a147134/?originalSubdomain=fr>`_ and `Pierre Wolinski <https://pierre-wolinski.fr/>`_ provided valuable feedback and suggestions to improve MLXP. They also found and reported several bugs in the software which helped improve its quality and stability. 

- `Thomas Ryckeboer <https://www.linkedin.com/in/thomas-ryckeboer-a97ab7143/?locale=en_US>`_ for providing guidance on continuous integration of MLXP.

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
