Getting started
===============

Introduction
------------
Experimentalist is an open-source python framework for managing multiple experiments with complex option structure from launching, logging to querying results. 


Key functionalities
-------------------
  - Creating several jobs automatically using hydra and hierarchical configs. 
  - Submitting jobs using a job scheduler whenerver available. 
  - Enhancing code management and reproducibility of experiments by automatically generating a deployment version of the code based on the latest git commit. 
  - Logging all outputs of a job in a uniquely assigned directory, along with all metadata and  configuration options to reproduce the experiment.
  - Managing potential job failures by providing the ability to easily resume them from their latest state.
  - Exploiting the results of several experiments by easily reading, querying, grouping and aggregating the output of several jobs. 


Quick start guide
-----------------

To use Experimentalist for launching and logging, you need to import it in the main python file that will be executed:

.. code-block:: python
   :caption: main.py

   import experimentalist as expy

   @expy.launch(config_name="config.yaml", config_path="./configs")
   def main(logger: expy.Logger)->None:
     cfg = logger.config # getting a hydra-like config structure
     print(cfg)

   if __name__ == "__main__":
     main()


The logger object will be automatically created on the fly during excecution and will store the configurations options provided in "config.yaml" of the directory "./configs". If the file "config.yaml" or its parent directory "./configs" do not exist, they will be created automatically. The user can then custumize "config.yaml". Otherwise, the configurations contained in "config.yaml" will be provided to the logger object. You can also provide configuration options in the command-line just like in hydra:

.. code-block:: console
   :caption: Example command to run the 'main.py' file with user defined options.

   $ python main.py ++custom.n_iter=5


'config.yaml' is created automatically if it does not exits and contains the main fields that the user can customize:

.. code-block:: yaml
   :caption: Default content of the file 'config.yaml' when automatically created created 

   custom: ???
   seed: ???

The field custom can contain 


   



