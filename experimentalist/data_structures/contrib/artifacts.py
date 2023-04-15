import abc
from typing import Any, Type
from dataclasses import dataclass
import dill as pkl
from experimentalist.logging.artifacts import Artifact

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
        try:
            # pipreqs: exclude
            import torch
            torch.save(self.obj, f"{fname}{self.ext}")
        except ImportError:
            raise ImportError

