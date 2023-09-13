

from urllib.request import urlopen

_conf_url = \
        "https://raw.githubusercontent.com/inducer/sphinxconfig/main/sphinxconfig.py"
with urlopen(_conf_url) as _inf:
    exec(compile(_inf.read(), _conf_url, "exec"), globals())


ver_dic = {}
exec(
    compile(
        open("../mlxp/version.py").read(), "../mlxp/version.py", "exec"
    ),
    ver_dic,
)
version = ver_dic["VERSION_TEXT"]
release = ver_dic["RELEASE"]
project = ver_dic["PROJECT"]
author = ver_dic["AUTHOR"]
copyright = ver_dic["COPYRIGHT"]




intersphinx_mapping = {
    "https://docs.python.org/3": None,
    "https://numpy.org/doc/stable/": None,
    "https://documen.tician.de/codepy/": None,
}

# -- Project information -----------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath('../../'))





extensions = ['sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'autodocsumm']




autodoc_member_order = 'bysource'
autodoc_inherit_docstrings = True



