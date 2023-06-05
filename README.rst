Introduction
^^^^^^^^^^^^

MLXPy (Machine Learning eXperiments Python) package is an open-source Python framework for managing multiple experiments with a flexible option structure from launching, and logging to querying results. A full documentation is available in the `MLXPy's official  documentation website <https://michaelarbel.github.io/mlxpy/>`_. 



Key functionalities
^^^^^^^^^^^^^^^^^^^

1. Launching several jobs automatically using `hydra <https://hydra.cc/>`_ and hierarchical configs by adding a single decorator to the main task function.   
2. Logging outputs (metrics, artifacts, checkpoints) of a job in a uniquely assigned directory along with all metadata and configuration options to reproduce the experiment.
3. Code version management by automatically generating a deployment version of the code based on the latest git commit. 
4. Submitting jobs to a cluster using a job scheduler. 
5. Exploiting the results of several experiments by easily reading, querying, grouping, and aggregating the output of several jobs. 


License
^^^^^^^

MLXPy is distributed under MIT license.

Citing MLXPy
^^^^^^^^^^^^

Even though this is non-legally binding, the author kindly ask users to cite MLXPy in their publications if they use 
it in their research as follows:


.. code-block:: bibtex 

   @Misc{Arbel2023MLXPy,
     author = {Michae Arbel},
     title = {MLXPy: },
     howpublished = {Github},
     year = {2023},
     url = {https://github.com/MichaelArbel/mlxpy}
   }


.. include:: docs/installing.rst


Acknowledgments
^^^^^^^^^^^^^^^

I would like to acknowledge the following contributors for their contributions to the development of this package:

- `Alexandre Zouaoui <https://azouaoui.me/>`_ kindly shared his python implementation for creating job scripts and submiting them to a cluster. His code served as the basis for the implementation of the Scheduler class. While I have significantly modified the process of job submission, by integrating it with MLXpy's launching functionality, I am grateful for Alexandre's contribution which were invaluable to the development of this project.


- `Juliette Marrie <https://www.linkedin.com/in/juliette-marrie-5b8a59179/?originalSubdomain=fr>`_ tested a premature version of MLXPy. I am grateful for her feedback which was extremetly helpful for shaping and improving MLXPy's functionalities.  

- `Romain Ménégaux <https://www.linkedin.com/in/romain-menegaux-88a147134/?originalSubdomain=fr>`_ provided valuable feedback and suggestions to improve MLXPy. He also found and reported several bugs in the software which helped improve its quality and stability. 







