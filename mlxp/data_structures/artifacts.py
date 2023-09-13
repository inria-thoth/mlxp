"""Artifacts objects that can be saved by a Logger object."""

import abc
from dataclasses import dataclass
from typing import Any

import dill as pkl


@dataclass
class Artifact(abc.ABC):
    """An abstract base class for any types of artifacts.

    This class can deal with different objects structures
    such as numpy arrays, torch tensors, checkpoints, etc.
    Instances of this class are meant to be used as inputs
    to the method log_artifact of the class Logger.
    New classes inheriting from this abstract class
    can be created by the user depending on the need.

    .. py:attribute:: obj
        :type: Any

        The structure to be saved

    .. py:attribute:: ext
        :type: str

        The extension under which the object obj is saved
    """

    obj: Any
    ext: str

    @abc.abstractmethod
    def _save(self, fname: str) -> None:
        """Save the attribute obj into a file named fname.

        :param fname: The name of the file where the object must be saved.
        :type fname: str
        :return: None
        """
        pass


@dataclass
class Checkpoint(Artifact):
    """An subclass of Artifact for saving any python object that is serializable."""

    ext = ".pkl"

    def _save(self, fname):
        """Save the attribute obj into a file named fname.

        :param fname: The name of the file where the object must be saved.
        :type fname: str
        :return: None
        """
        with open(f"{fname}{self.ext}", "wb") as f:
            pkl.dump(self.obj, f)
