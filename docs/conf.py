

from urllib.request import urlopen
import os 
_conf_url = \
        "https://raw.githubusercontent.com/inducer/sphinxconfig/main/sphinxconfig.py"
with urlopen(_conf_url) as _inf:
    exec(compile(_inf.read(), _conf_url, "exec"), globals())



ver_dic = {}
parent_dir = os.path.dirname(os.getcwd())
path_project_info_file = os.path.join(parent_dir,"project_info.py")
path_version_file = os.path.join(parent_dir,"VERSION")

exec(
    compile(
        open(path_project_info_file).read(), path_project_info_file, "exec"
    ),
    ver_dic,
)

with open(path_version_file) as version_file:
    version = version_file.read().strip()


VERSION = tuple([int(s) for s in version.split('.')])
RELEASE = version


release = RELEASE
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
    'autodocsumm',
    'sphinx_multiversion']


templates_path = [
    "_templates",
]

html_sidebars = {
    '**': [
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/scroll-start.html",
        "sidebar/navigation.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
        #"sidebar/variant-selector.html",
        "versioning.html", 
    ],
}

autodoc_member_order = 'bysource'
autodoc_inherit_docstrings = True
 

# Use tags for versioning
smv_tag_whitelist = None#r'^\d+\.\d+\.\d+$'
# Use regex for smv_branch_whitelist to include master branch and branches of the form release/*
smv_branch_whitelist= r'(master|release/.*)'
smv_remote_whitelist=None

