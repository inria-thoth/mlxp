"""Structures for validating the configurations."""

import os
import subprocess
from dataclasses import dataclass, field
from typing import Any

from omegaconf import MISSING


def get_defautl_shell_path():
    try:
        command = "echo $SHELL"
        shell_path = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE, text=True).strip()
        return shell_path
    except subprocess.CalledProcessError:
        print("Error running the command {command}")
        return ""


@dataclass
class ConfigScheduler:
    """Structure of the scheduler config file.

    .. py:attribute:: name
        :type: str

        Name of the scheduler's class.

    .. py:attribute:: env_cmd
        :type: str

        Command for activating the working environment. (e.g. 'conda activate my_env')

    .. py:attribute:: shell_path
        :type: Any

        Path to the shell used for submitting a job using a scheduler. (default '/bin/bash')

    .. py:attribute:: shell_config_cmd
        :type: bool

        command for configuring the shell when submitting a job using a scheduler. (default 'source ~/.bashrc')

    .. py:attribute:: cleanup_cmd
        :type: str

        A command for clearning the environment when executing a job submitted by the scheduler. (e.g.: 'module purge' for SLURM)

    .. py:attribute:: option_cmd
        :type: List[str]

        A list of strings containing the scheduler's options for the job. This allows to specify the desired resources to the scheduler such as the duration of the job, the quantity and type of resources, etc.
    """

    name: str = "NoScheduler"
    shell_path: str = get_defautl_shell_path()
    shell_config_cmd: str = ""
    env_cmd: str = ""
    cleanup_cmd: str = ""
    option_cmd: list = field(default_factory=lambda: [])


@dataclass
class ConfigVersionManager:
    """Structure of the config file for the version manager.

    .. py:attribute:: name
        :type: str

        Name of the version manager's class.
    """

    name: str = MISSING


@dataclass
class ConfigGitVM(ConfigVersionManager):
    """Configs for using the GitVM version manager.

    It inherits the structure of the class VersionManager.

    .. py:attribute:: name
        :type: str

        Name of the version manager's class.

    .. py:attribute:: parent_work_dir
        :type: str

        The target parent directory of
        the new working directory returned by the version manager

    .. py:attribute:: compute_requirements
        :type: bool

        When set to true, the version manager stores a list of requirements and their version.
    """

    name: str = "GitVM"
    parent_work_dir: str = os.path.join(".", ".work_dir")
    compute_requirements: bool = False


@dataclass
class ConfigLogger:
    """Structure of the config file for the logs.

    The outputs for each run are saved in a directory of the form
    'parent_log_dir/log_id' which is stored in the variable 'path' during execution.

    .. py:attribute:: name
        :type: str

        Class name of the logger to use
        (default "DefaultLogger")

    .. py:attribute:: parent_log_dir
        :type: str

        Absolute path of the parent directory where the logs of a run are stored.
        (default "./logs")

    .. py:attribute:: forced_log_id
        :type: int

        An id optionally provided by the user for the run. If forced_log_id is positive,
        then the logs of the run will be stored under 'parent_log_dir/forced_log_id'. Otherwise,
        the logs will be stored in a directory 'parent_log_dir/log_id' where 'log_id'
        is assigned uniquely for the run during execution.

    .. py:attribute:: log_streams_to_file
        :type: bool

        If true logs the system stdout and stderr of a run to a file named
        "log.stdour" and "log.stderr" in the log directory.
    """

    name: str = "DefaultLogger"
    parent_log_dir: str = os.path.join(".", "logs")
    forced_log_id: int = -1
    log_streams_to_file: bool = False


@dataclass
class Info:
    """A structure storing general information about the run.

    The following variables are assigned during execution.

    .. py:attribute:: status
        :type: str

        Status of a job. The status can take the following values:

        - STARTING: The metadata for the run have been created.

        - RUNNING: The experiment is currently running.

        - COMPLETE: The run is  complete and did not through any error.

        - FAILED: The run stoped due to an error.

    .. py:attribute:: current_file_path
        :type: str

        Name of the python file being executed.

    .. py:attribute:: executable
        :type: str

        Path to the python executable used for executing the code.

    .. py:attribute:: hostname
        :type: str

        Name of the host from which code is executed.

    .. py:attribute:: process_id
        :type: int

        Id of the process assigned to the job during execution.

    .. py:attribute:: start_date
        :type: Any

        Date at which job started.

    .. py:attribute:: start_time
        :type: Any

        Time at which job started.

    .. py:attribute:: end_date
        :type: Any

        Date at which job ended.

    .. py:attribute:: end_time
        :type: Any

        Time at which job ended.

    .. py:attribute:: logger
        :type: Any

        Logger info, whenever used.

    .. py:attribute:: scheduler
        :type: Any

        scheduler info, whenever used.

    .. py:attribute:: version_manager
        :type: Any

        version_manager info, whenever used.
    """

    status: str = "STARTING"
    current_file_path: str = ""
    executable: str = ""
    hostname: str = ""
    process_id: int = -1
    start_date: Any = ""
    start_time: Any = ""
    end_date: Any = ""
    end_time: Any = ""
    work_dir: str = os.getcwd()
    logger: Any = None
    scheduler: Any = None
    version_manager: Any = None


@dataclass
class MLXPConfig:
    """Default settings of MLXP.

    .. py:attribute:: logger
        :type: ConfigLogger

        The logger's settings.
        (default ConfigLogger)

    .. py:attribute:: scheduler
        :type: ConfigScheduler

        The scheduler's settings.
        (default ConfigScheduler)

    .. py:attribute:: version_manager
        :type: ConfigVersionManager

        The version_manager's settings.
        (default ConfigGitVM)

    .. py:attribute:: use_version_manager
        :type: bool

        If true, uses the version manager.
        (default False)

    .. py:attribute:: use_scheduler
        :type: bool

        If true, uses the scheduler.
        (default False)

    .. py:attribute:: use_logger
        :type: bool

        If true, uses the logger.
        (default True)

    .. py:attribute:: interactive_mode
        :type: bool

        A variable controlling MLXP's interactive mode.

            1. If 'interactive_mode==True', MLXP uses the interactive mode whenever applicable:

                - When 'use_scheduler==True' and 'scheduler.name=="NoScheduler"':
                Asks the user to select a valid scheduler.
                - When 'use_version_manager==True': Asks the user:

                    - If untracked files should be added.
                    - If uncommitted changes should be committed.
                    - If a copy of the current repository based on the latest commit should be made (if not already existing) to execute the code from there. Otherwise, code is executed from the current directory.

            2. If 'interactive_mode==False', no interactive mode is used and current options are used:

                - When 'use_scheduler==True' and 'scheduler.name=="NoScheduler"': An error is thrown
                - When 'use_version_manager==True':

                    - Existing untracked files or uncommitted changes are ignored.
                    - A copy of the code is made based on the latest commit (if not already existing) and code is executed from there.
    """

    logger: ConfigLogger = field(default_factory=lambda: ConfigLogger())
    scheduler: ConfigScheduler = field(default_factory=lambda: ConfigScheduler())
    version_manager: ConfigVersionManager = field(default_factory=lambda: ConfigGitVM())
    use_version_manager: bool = False
    use_scheduler: bool = False
    use_logger: bool = True
    interactive_mode: bool = True


@dataclass
class Metadata:
    """The structure of the config file.

    .. py:attribute:: info
        :type: Info

        Contains config information of the run
        (hostname, command, application,  etc)
        (default Info)

    .. py:attribute:: mlxp
        :type: MLXPConfig

        Default settings of MLXP.
        (default MLXPConfig)

    .. py:attribute:: config
        :type: Any

        Contains the user's defined configs that are specific to the run.
    """

    info: Info = field(default_factory=lambda: Info())
    mlxp: MLXPConfig = field(default_factory=lambda: MLXPConfig())
    config: Any = None
