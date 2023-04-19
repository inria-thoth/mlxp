# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

from urllib.request import urlopen

_conf_url = \
        "https://raw.githubusercontent.com/inducer/sphinxconfig/main/sphinxconfig.py"
with urlopen(_conf_url) as _inf:
    exec(compile(_inf.read(), _conf_url, "exec"), globals())

copyright = '2023, Michael Arbel'

ver_dic = {}
exec(
    compile(
        open("../experimentalist/__init__.py").read(), "../experimentalist/__init__.py", "exec"
    ),
    ver_dic,
)
version = ".".join(str(x) for x in ver_dic["VERSION"])
# The full version, including alpha/beta/rc tags.
release = ver_dic["VERSION_TEXT"]


intersphinx_mapping = {
    "https://docs.python.org/3": None,
    "https://numpy.org/doc/stable/": None,
    "https://documen.tician.de/codepy/": None,
}


import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'experimentalist'

author = 'Michael Arbel'

# The full version, including alpha/beta/rc tags
release = '0.1' 


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages']




autodoc_member_order = 'bysource'
autodoc_inherit_docstrings = True



