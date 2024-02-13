"""Enumerations."""

from enum import Enum


class SearchableKeys(Enum):
    """Keys that can be searched by Reader object."""

    Info = "info."
    Config = "config."


class DataFrameType(Enum):
    """Types of data that can be returned by the method filter of a Reader object."""

    Pandas = "pandas"
    DataDictList = "datadict"


class DefaultSchedulers(Enum):
    """Schedulers supported by default by MLXP."""

    OARScheduler = "OARScheduler"
    SLURMScheduler = "SLURMScheduler"


class Directories(Enum):
    """The sub-directories created by the logger for each run.

    - Metrics: (Value: "metrics") A directory containing the JSON files created when calling the method log_metrics of a Logger object.
    - Metadata: (Value: "metadata") A directory containing three files 'info.yaml', 'mlxp.yaml' and 'config.yaml'.
    - Artifacts: (Value: "artifacts") A directory containing sub-directories created when calling the method log_artifacts of a Logger object.
    """

    Metrics = "metrics"
    Metadata = "metadata"
    Artifacts = "artifacts"
    Sessions = "sessions"


class Status(Enum):
    """Status of a run.

    The status can take the following values:

    - STARTING: The metadata for the run have been created.
    - RUNNING: The experiment is currently running.
    - COMPLETE: The run is  complete and did not through any error.
    - FAILED: The run stoped due to an error.
    """

    STARTING = "STARTING"
    COMPLETE = "COMPLETE"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
