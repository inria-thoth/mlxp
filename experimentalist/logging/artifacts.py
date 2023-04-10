import abc
from typing import Any, Type
from dataclasses import dataclass


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
    def save(self, fname: str)->None:
        """Saves the attribute obj into a file named fname.
            
        :param fname: The name of the file where the object must be saved.
        :type fname: str
        :return: None

        """
        pass

@dataclass
class NumpyArray(Artifact):
    """A subclass of Artifact for saving dictionaries of numpy arrays.
    """
    ext= ".npz"
    def save(self, fname):

        import numpy as np
        np.savez(fname, **self.obj)
@dataclass
class PNGImage(Artifact):
    """An subclass of Artifact for saving a instance of matplotlib.figure.Figure.
    """
    ext= ".png"
    def save(self, fname):
        import matplotlib
        assert isinstance(self.obj, matplotlib.figure.Figure)
        self.obj.savefig(f"{fname}{self.ext}", bbox_inches="tight")
@dataclass
class TorchModel(Artifact):
    """An subclass of Artifact for saving pytorch objects: Tensor, Module, or 
    a dictionary containing the whole state of a module. 
    """
    ext= ".pth"
    def save(self, fname):
        import torch
        torch.save(self.obj, f"{fname}{self.ext}")
@dataclass
class Checkpoint(Artifact):
    """An subclass of Artifact for saving any python object that is serializable. 
    """
    ext= ".pkl"

    def save(self, fname):
        with open(f"{fname}{self.ext}", "wb") as f:
                    pkl.dump(self.obj, f)
