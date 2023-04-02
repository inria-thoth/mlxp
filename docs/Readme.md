
- First run this terminal command

sphinx-quickstart

- Then in conf.py uncomment write the following code

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

- Add the following extensions to conf.py

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'
]


- Run the following command from the main directory

sphinx-apidoc -o docs experimentalist/


- Add modules to the file index.rst

- Run the command make html



- If you made some change and want to genrate new doc, run 
make clean html
followed by 
make html


