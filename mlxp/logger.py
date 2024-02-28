"""The logger can saves the configs and outputs of an experiment."""


import abc
import json
import marshal
import os
import random
import sys
from time import sleep
from typing import Any, Callable, Dict, Union

import dill as pkl
import yaml

from mlxp.data_structures.artifacts import Artifact_types
from mlxp.data_structures.config_dict import ConfigDict
from mlxp.enumerations import Directories
from mlxp.errors import InvalidArtifactError, InvalidKeyError

invalid_metrics_file_names = ["info", "config", "mlxp", "artifacts"]


class Logger(abc.ABC):
    """A logger that allows saving outputs of the run in a uniquely assigned directory
    for the specific run.

    The logger creates a directory with a default file structure:

    .. code-block:: console

        parent_log_dir/log_id:
        ├── metadata/
        │   └── metadata.yaml : Contains the configs of the run
        ├── metrics/
        │   ├── 'file_name'.json : Contains a the outputs stored
        │   │                   when running the method log_metrics(metrics_dict, file_name)
        │   └── .keys/ Directory of yaml files containing the keys of dictionaries saved using log_metrics.
        │            Each file 'file_name'.yaml corresponds to a json file 'file_name'.json containing the dictionaries.
        ├── artifacts/ : A directory where each subdirectory contains objects of the same subclass of Artifact saved using the method log_artifacts.
        ├── log.stderr: Contains error logs (Only if job is submitted in bacth mode to a scheduler)
        ├── log.stdout: Contains output logs (Only if job is submitted in bacth mode to a scheduler)
        └── script.sh: Contains the script for running the job (Only if job is submitted using a job scheduler)

    .. py:attribute:: parent_log_dir
        :type: str

        The parent directory where the directory of the run is created.
    """

    def __init__(self, parent_log_dir, forced_log_id=-1, log_streams_to_file=False):
        """Create a logger object.

        :param parent_log_dir: The parent directory where the directory of the run is
            created.
        :param forced_log_id: A forced log_id for the run. When forced_log_id is
            positive, the log_id of the run is set forced_log_id. If forced_log_id is
            negative, then the logger assigns a new unique log_id for the run.
        :param log_streams_to_file: When true, the stdout and stderr files are saved in
            files 'log_dir/log.stdout' and 'log_dir/log.stderr'.
        :type parent_log_dir: str
        :type forced_log_id: int
        :type log_streams_to_file: bool
        """
        self.parent_log_dir = os.path.abspath(parent_log_dir)
        self.forced_log_id = forced_log_id
        self._metric_dict_keys = {}
        self._artifact_types = Artifact_types
        self._log_id, self._log_dir = _make_log_dir(forced_log_id, self.parent_log_dir)

        self.metrics_dir = os.path.join(self._log_dir, Directories.Metrics.value)
        self.artifacts_dir = os.path.join(self._log_dir, Directories.Artifacts.value)
        self.metadata_dir = os.path.join(self._log_dir, Directories.Metadata.value)
        self.session_dir = os.path.join(
            self._log_dir, Directories.Artifacts.value, Directories.Sessions.value
        )
        os.makedirs(self.metrics_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

        if log_streams_to_file:
            log_stdout = open(os.path.join(self._log_dir, "log.stdout"), "w", buffering=1)
            sys.stdout = log_stdout
            log_stderr = open(os.path.join(self._log_dir, "log.stderr"), "w", buffering=1)
            sys.stderr = log_stderr

    def _log_configs(self, config: ConfigDict) -> None:
        file_name = os.path.join(self.metadata_dir, "config")
        with open(file_name + ".yaml", "w") as f:
            yaml.dump(config.config.to_dict(), f)
        file_name = os.path.join(self.metadata_dir, "info")
        with open(file_name + ".yaml", "w") as f:
            yaml.dump(config.info.to_dict(), f)
        # file_name = os.path.join(self.metadata_dir, "mlxp")
        # with open(file_name + ".yaml", "w") as f:
        #    yaml.dump(config.mlxp.to_dict(), f)

    def get_info(self) -> None:
        """Return a dictionary containing information about the logger settings used for
        the run.

        :return: Dictionary containing information about the logger settings used for
            the run.
        :rtype: Dict[str, Any]
        """
        return {
            "log_id": self.log_id,
            "log_dir": self.log_dir,
            "metrics_dir": self.metrics_dir,
            "metadata_dir": self.metadata_dir,
            "artifacts_dir": self.artifacts_dir,
        }

    def log_metrics(self, metrics_dict, log_name):
        """Save a dictionary of scalars to a json file named log_name+'.json' in the
        directory log_dir/metrics.

        If the file exists already, the dictionary is appended at the end of the file.

        :param metrics_dict: Dictonary of scalar values to be saved, the values can be
            either int, float of string.
        :param log_name: Name of the json file where to save the metric_dict.
        :type metrics_dict: Dict[str, Union[int, float, str]]
        :type log_name: str
        :return: None
        """
        try:
            assert log_name not in invalid_metrics_file_names
        except AssertionError:
            raise InvalidKeyError(
                f"The chosen log_nam:  {log_name} is invalid! It must be different from these protected names: {invalid_metrics_file_names} "
            )

        self._log_metrics_key(metrics_dict, log_name)
        file_name = os.path.join(self.metrics_dir, log_name)
        return self._log_metrics(metrics_dict, file_name)

    def _log_metrics(self, metrics_dict: Dict[str, Union[int, float, str]], file_name: str) -> None:
        with open(file_name + ".json", "a") as f:
            json.dump(metrics_dict, f)
            f.write(os.linesep)

    def log_artifacts(self, artifact: object, artifact_name: str, artifact_type: str) -> None:
        """Save an artifact object into a destination file: 'log_dir/artifacts/artifact_name', 

        The directory 'artifact_class_name' is named after
        the child class inheriting from Artifact.

        :param artifact:  An object to save.
        :param artifact_name: Name of the file where the artifact is saved. 
        :param artifact_type: Type of the artifact to save.
        :type artifact: object
        :type artifact_name: str
        :type artifact_type: str
        :return: None
        :raises InvalidArtifactError: if artifact type does not correspond to any existing type.
        """
        try:
            assert artifact_type in self._artifact_types.keys()
        except AssertionError:
            message = f"Provided type: {artifact_type} is an invalid Artifact type.\n"
            message = f"Valid types are: {list(self._artifact_types.keys())}.\n"
            message = f"To add a new artifact type, use the method register_artifact_type before calling this method."
            raise InvalidArtifactError(message)
        subdir = os.path.join(self.artifacts_dir, artifact_type, os.path.dirname(artifact_name))
        os.makedirs(subdir, exist_ok=True)
        fname = os.path.join(self.artifacts_dir, artifact_type, artifact_name)
        self._artifact_types[artifact_type]["save"](artifact, fname)
        self._log_artifact_type(artifact_name, artifact_type)

    def load_artifacts(
        self, artifact_name: str, artifact_type: Union[str, None] = None, root: Union[str, None] = None
    ) -> Any:
        """Restore an artifact from 'log_dir/artifacts/artifact_type/artifact_name' or a
        user defined directory root.

        Raises an error if it fails to do so.

        :param artifact_name: Name of the file where the checkpoint is saved.
        :type artifact_name: str (default 'checkpoint')
        :param root: Absolute path to the log directory (log_dir) (assuming it was created using a logger object).
        If set to None, then the logger in its own log_dir.
        :param artifact_type: Type of the artifact to save.
        If set to None, the method will try to infer the artifact type from the artifact_name.
        :type root: Union[str,None] (default 'None')
        :type artifact_type: Union[str,None] (default 'None')
        return: Any serializable object stored in 'root/artifacts/artifact_type/artifact_name'.
        rtype: Any
        """
        if not root:
            root = self.log_dir
        if not artifact_type:

            artifact_type_file = os.path.join(root, Directories.Artifacts.value, ".keys", "custom_types.yaml")
            artifact_dict_name = os.path.join(root, Directories.Artifacts.value, ".keys", "artifacts.yaml")

            # get the base name of the artifact
            artifact_base_name = os.path.basename(artifact_name)
            artifact_dir_name = _path_as_key(os.path.dirname(artifact_name))
            try:
                with open(artifact_dict_name, "r") as f:
                    cur_yaml = yaml.safe_load(f)
                for key, value in cur_yaml.items():
                    if artifact_dir_name in value:
                        if artifact_base_name in value[artifact_dir_name]:
                            artifact_type = key
                            break
                assert artifact_type
            except BaseException:
                message = "Could not infer artifact type! Please provide a value for artifact_type."
                raise InvalidArtifactError(message)
        artifact_path = os.path.join(root, Directories.Artifacts.value, artifact_type, artifact_name)

        return self._artifact_types[artifact_type]["load"](artifact_path)

    def register_artifact_type(
        self, name: str, save: Callable[[object, str], None], load: Callable[[str], object]
    ) -> None:
        """Register a new artifact type with a save and load method.

        Use this method when you want to save and load a custom artifact type. This
        method should be called before using log_artifacts with the new artifact type.

        :param name: Name of the artifact type.
        :param save: User-defined function to save the artifact.
        :param load: User-defined function to load the artifact.
        :type name: str
        :type save: Callable[[object, str], None]
        :type load: Callable[[str], object]
        :return: None
        """
        is_new = name not in self._artifact_types.keys()
        if is_new:
            self._artifact_types.update({name: {"load": load, "save": save}})

            code_string_load = marshal.dumps(load.__code__)
            code_string_save = marshal.dumps(save.__code__)

            artifact_type_serialized = {name: {"load": code_string_load, "save": code_string_save}}
            artifact_type_file = os.path.join(self.artifacts_dir, ".keys")
            os.makedirs(artifact_type_file, exist_ok=True)
            artifact_type_file = os.path.join(artifact_type_file, "custom_types.yaml")
            cur_yaml = {}
            try:
                with open(artifact_type_file, "r") as f:
                    cur_yaml = yaml.safe_load(f)
            except BaseException:
                pass
            cur_yaml.update(artifact_type_serialized)
            with open(artifact_type_file, "w") as f:
                yaml.dump(cur_yaml, f)

    def _log_artifact_type(self, artifact_name: str, artifact_type: str):
        # Logging new keys appearing in a metrics dict

        artifact_keys_dir = os.path.join(self.artifacts_dir, ".keys")
        os.makedirs(artifact_keys_dir, exist_ok=True)
        artifact_dict_name = os.path.join(artifact_keys_dir, "artifacts.yaml")
        cur_yaml = {}
        try:
            with open(artifact_dict_name, "r") as f:
                cur_yaml = yaml.safe_load(f)
        except BaseException:
            pass
        artifact_base_name = os.path.basename(artifact_name)
        artifact_dir = _path_as_key(os.path.dirname(artifact_name))
        if artifact_type in cur_yaml.keys():
            if artifact_dir in cur_yaml[artifact_type]:
                cur_yaml[artifact_type][artifact_dir].update({artifact_base_name: ""})
            else:
                cur_yaml[artifact_type][artifact_dir] = {artifact_base_name: ""}
        else:
            cur_yaml[artifact_type] = {artifact_dir: {artifact_base_name: ""}}

        with open(artifact_dict_name, "w") as f:
            yaml.dump(cur_yaml, f)

    @property
    def log_id(self):
        """Return the uniquely assigned id of the run.

        Ensures the log_id to be immutable.

        :rtype: int
        :return: The id of the run.
        """
        return self._log_id

    @property
    def log_dir(self):
        """Return the path to the directory where outputs of the run are saved.

        Ensures the log_dir to be immutable.

        :rtype: str
        :return: The path to the output directory of the run.
        """
        return self._log_dir

    def _log_metrics_key(self, metrics_dict: Dict[str, Union[int, float, str]], log_name: str):
        # Logging new keys appearing in a metrics dict

        if log_name not in self._metric_dict_keys.keys():
            self._metric_dict_keys[log_name] = []

        new_keys = [key for key in metrics_dict.keys() if key not in self._metric_dict_keys[log_name]]

        if new_keys:
            self._metric_dict_keys[log_name] += new_keys
            dict_file = {key: "" for key in new_keys}
            keys_dir = os.path.join(self.metrics_dir, ".keys")
            os.makedirs(keys_dir, exist_ok=True)
            log_name = os.path.join(keys_dir, log_name)
            cur_yaml = {}
            try:
                with open(log_name + ".yaml", "r") as f:
                    cur_yaml = yaml.safe_load(f)
            except BaseException:
                pass
            cur_yaml.update(dict_file)
            with open(log_name + ".yaml", "w") as f:
                yaml.dump(cur_yaml, f)


class DefaultLogger(Logger):
    """A logger that provides methods for logging checkpoints and loading them."""

    def __init__(self, parent_log_dir, forced_log_id, log_streams_to_file=False):
        super().__init__(parent_log_dir, forced_log_id, log_streams_to_file=log_streams_to_file)

    def log_checkpoint(self, checkpoint: Any, log_name: str = "checkpoint") -> None:
        """Save a checkpoint for later use, this can be any serializable object.

        This method is intended for saving the latest state of the run, thus, by
        default, the checkpoint name is set to 'last.pkl'. For custom checkpointing
        please use the method log_artifacts

        :param checkpoint: Any serializable object to be stored in
            'run_dir/artifacts/pickle/last.pkl'.
        :type checkpoint: Any
        :param log_name: Name of the file where the checkpoint is saved.
        :type log_name: str (default 'checkpoint')
        """
        self.log_artifacts(checkpoint, artifact_name=log_name, artifact_type="pickle")

    def load_checkpoint(self, log_name, root=None) -> Any:
        """Restore a checkpoint from 'run_dir/artifacts/pickle/log_name.pkl' or a user
        defined directory root.

        Raises an error if it fails to do so.

        :param log_name: Name of the file where the checkpoint is saved.
        :type log_name: str (default 'checkpoint')
        :param root: Absolute path to the checkpoint.
        If set to None, the logger looks for the checkpoint in 'run_dir/artifacts/pickle'.
        :type root: Union[str,None] (default 'None')
        return: Any serializable object stored in 'run_dir/artifacts/pickle/last.pkl'.
        rtype: Any
        """

        if root:
            checkpoint_name = os.path.join(root, log_name)
        else:
            checkpoint_name = os.path.join(self.artifacts_dir, log_name)
        return Artifact_types["pickle"]["load"](checkpoint_name)


def _make_log_dir(forced_log_id, root):
    os.makedirs(root, exist_ok=True)
    log_dir = None
    if forced_log_id < 0:
        fail_count = 0
        while log_dir is None:
            try:
                _id = _maximum_existing_log_id(root) + 1
                log_dir_tmp = os.path.join(root, str(_id))
                os.mkdir(log_dir_tmp)
                log_dir = log_dir_tmp  # set log_dir only if successful creation
            except FileExistsError:  # Catch race conditions
                sleep(random.random())
                if fail_count < 1000:
                    fail_count += 1
                else:  # expect that something else went wrong
                    raise
    else:
        assert isinstance(forced_log_id, int)
        _id = forced_log_id
        log_dir = os.path.join(root, str(_id))
        os.makedirs(log_dir, exist_ok=True)
    return _id, log_dir


def _maximum_existing_log_id(root):
    dir_nrs = [int(d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d.isdigit()]
    if dir_nrs:
        return max(dir_nrs)
    else:
        return 0


def _path_as_key(path):
    if path:
        return "." + ".".join(_split_all_directories(path))
    return ""


def _split_all_directories(file_path):
    directories = []
    while True:
        file_path, directory = os.path.split(file_path)
        if directory:
            directories.append(directory)
        else:
            if file_path:
                directories.append(file_path)
            break
    directories.reverse()
    return directories
