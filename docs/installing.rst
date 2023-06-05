Installing MLXPy
^^^^^^^^^^^^^^^^

You can install MLXPy either from PyPI or by cloning the GitHub.


From PyPI
---------

You can simply run the following command:

.. code-block:: console
   
   $ pip install MLXPy


From GitHub
-----------

You can install this package by cloning it from the GitHub repository
and then installing it with `pip`. 


1. Clone the repository:

.. code-block:: console
   
   $ git clone git@github.com:MichaelArbel/mlxpy.git

2. Change to the package directory:

.. code-block:: console
   
   $ cd mlxpy

3. Install the requirements using `pip`:

.. code-block:: console
   
   $ pip install -r requirements.txt

4. Install the package:

.. code-block:: console
   
   $ pip install .

Note: You may need to use `pip3` instead of `pip` depending on your setup.




Before installing MLXPy, make sure you the requirements are installed.


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
