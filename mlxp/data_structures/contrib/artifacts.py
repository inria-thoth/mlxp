"""Implementation of some Artifact objects."""

from dataclasses import dataclass

from mlxp.logging.artifacts import Artifact


@dataclass
class NumpyArray(Artifact):
    """A subclass of Artifact for saving dictionaries of numpy arrays."""

    ext = ".npz"

    def _save(self, fname):
        import numpy as np

        np.savez(fname, **self.obj)


@dataclass
class PNGImage(Artifact):
    """A subclass of Artifact for saving a instance of matplotlib.figure.Figure."""

    ext = ".png"

    def _save(self, fname):
        import matplotlib

        assert isinstance(self.obj, matplotlib.figure.Figure)
        self.obj.savefig(f"{fname}{self.ext}", bbox_inches="tight")


@dataclass
class TorchModel(Artifact):
    """A subclass of Artifact for saving pytorch objects: Tensor, Module, or a dictionary containing the whole state of a module."""

    ext = ".pth"

    def _save(self, fname):
        import torch

        torch.save(self.obj, f"{fname}{self.ext}")
