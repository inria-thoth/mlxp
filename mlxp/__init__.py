from mlxp.launcher import launch, Context
from mlxp.reader import Reader
from mlxp.logger import DefaultLogger
from mlxp.version_manager import GitVM

from mlxp.scheduler import Scheduler, SLURMScheduler, OARScheduler

from mlxp.data_structures.config_dict import ConfigDict
from mlxp.data_structures.data_dict import DataDictList


__all__ = [
    "launch", 
    "Reader",
    "DefaultLogger",
    "Scheduler",
    "ConfigDict",
    "Context",
    "DataDictList",
    "OARScheduler",
    "SLURMScheduler",
    "GitVM"
]



VERSION = (0, 1, 0)
PROJECT = 'MLXP'
AUTHOR = "Michael Arbel"
AUTHOR_EMAIL = "michael.n.arbel@gmail.com"
URL = "https://github.com/MichaelArbel/mlxp"
LICENSE = "MIT License"
VERSION_TEXT = ".".join(str(x) for x in VERSION)
COPYRIGHT = "Copyright (C) 2023 " + AUTHOR


VERSION_STATUS = ""
RELEASE = VERSION_TEXT + VERSION_STATUS


__version__ = VERSION_TEXT
__author__ = AUTHOR
__copyright__ = COPYRIGHT 
__credits__ = ["Romain Ménégaux",
                "Alexandre Zouaoui",
                "Juliette Marrie",
                "Pierre Wolinski"]

