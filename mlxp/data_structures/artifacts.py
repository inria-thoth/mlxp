"""Artifacts objects that can be saved by a Logger object."""

import os

import dill as pkl


class Artifact:
    def __init__(self, name, path, load, save):
        self.name = name
        self.path = path
        self._load = load
        self._save = save

    def load(self):
        return self._load(os.path.join(self.path, self.name))


def _save_pickle(obj: object, name: str) -> None:
    import dill as pkl

    with open(name, "wb") as f:
        pkl.dump(obj, f)


def _save_numpy(obj: object, name: str) -> None:
    import numpy as np

    np.savez(name, **obj)


def _save_image(obj: object, name: str) -> None:
    import matplotlib

    assert isinstance(obj, matplotlib.figure.Figure)
    obj.savefig(name, bbox_inches="tight")


def _save_torch(obj: object, name: str) -> None:
    import torch

    torch.save(obj, name)


def _load_pickle(name: str) -> object:
    import dill as pkl

    with open(name, "rb") as f:
        return pkl.load(f)


def _load_numpy(name: str) -> object:
    import numpy as np

    return np.load(name)


def _load_image(name: str) -> object:
    import matplotlib.image as mpimg

    # Load the PNG image
    return mpimg.imread(name)


def _load_torch(name: str) -> object:
    import torch

    # Load the PNG image
    return torch.load(name)


Artifact_types = {
    "pickle": {"save": _save_pickle, "load": _load_pickle},
    "numpy": {"save": _save_numpy, "load": _load_numpy},
    "torch": {"save": _save_torch, "load": _load_torch},
    "image": {"save": _save_image, "load": _load_image},
}
