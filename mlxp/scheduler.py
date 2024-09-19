"""The scheduler allows submitting several jobs to a cluster queue using hydra."""

import abc
import os
import platform
import subprocess
from copy import deepcopy
from typing import Any, Dict, List

from mlxp.errors import InvalidShellPathError, JobSubmissionError, UnknownSystemError


def _get_info_null(process_output: str) -> Dict[str, Any]:
    assert isinstance(process_output, str)
    return {}


def get_info_oar(process_output: str) -> Dict[str, Any]:
    """Return a dictionary containing the job_id assigned to the run by the scheduler.

    :return: A dictionary containing the job_id assigned to the run by the scheduler.
    :rtype: Dict[str,Any]
    """
    assert isinstance(process_output, str)
    if process_output:
        scheduler_job_id = process_output.split("\n")[-2].split("=")[-1]
        return {"scheduler_job_id": scheduler_job_id}
    return {}


SLURM = {
    "name": "SLURMScheduler",
    "directive": "#SBATCH",
    "submission_cmd": "sbatch",
    "job_name_cmd": "--job-name=",
    "output_file_cmd": "--output=",
    "error_file_cmd": "--error=",
    "get_info": _get_info_null,
}

OAR = {
    "name": "OARScheduler",
    "directive": "#OAR",
    "submission_cmd": "oarsub -S",
    "job_name_cmd": "-n ",
    "output_file_cmd": "-O ",
    "error_file_cmd": "-E ",
    "get_info": get_info_oar,
}


PBS = {
    "name": "PBSScheduler",
    "directive": "#PBS",
    "submission_cmd": "qsub",
    "job_name_cmd": "-N ",
    "output_file_cmd": "-o ",
    "error_file_cmd": "-e ",
    "get_info": _get_info_null,
}


SGE = {
    "name": "SGEScheduler",
    "directive": "#$",
    "submission_cmd": "qsub",
    "job_name_cmd": "-N ",
    "output_file_cmd": "-o ",
    "error_file_cmd": "-e ",
    "get_info": _get_info_null,
}

MWM = {
    "name": "MWMScheduler",
    "directive": "#MSUB",
    "submission_cmd": "msub",
    "job_name_cmd": "-N ",
    "output_file_cmd": "-o ",
    "error_file_cmd": "-e ",
    "get_info": _get_info_null,
}


LSF = {
    "name": "LSFScheduler",
    "directive": "#BSUB",
    "submission_cmd": "bsub",
    "job_name_cmd": "-J ",
    "output_file_cmd": "-o ",
    "error_file_cmd": "-e ",
    "get_info": _get_info_null,
}


Schedulers_dict = {"#OAR": OAR, "#SBATCH": SLURM, "#BSUB": LSF, "#MSUB": MWM, "#$": SGE, "#PBS": PBS}


class _Scheduler(abc.ABC):
    """An abstract class whose children allow to submit jobs using a particular job
    scheduler such as OAR or SLURM. Can be used as a parent class of a custom scheduler.

    .. py:attribute:: directive
        :type: str

        The string that preceeds the command options of a scheduler in a script.
        (e.g.: '#OAR' for OAR and '#SBATCH' for SLURM)

    .. py:attribute:: submission_cmd
        :type: str

        The command for submitting a job defined in a script to the scheduler.
        (e.g.: 'oarsub -S' for OAR and 'sbatch' for SLURM).


    .. py:attribute:: option_cmd
        :type: List[str]

        A list of strings containing the scheduler's options for the job.
        This allows to specify the desired resources to the scheduler such as
        the duration of the job, the quantity and type of resources, etc.

    .. py:attribute:: env_cmd
        :type: str

        Command for activating the working environment.
        (e.g.: 'conda activate my_env')
        By default no environment is activated.

    .. py:attribute:: shell_path
        :type: Any

        Path to the shell used for submitting a job using a scheduler. (default '/bin/bash')
    """

    def __init__(self, specs: Dict[str, Any]):
        """Create a scheduler object from a dictionary of specifications.

        :param directive: The string that preceeds the command options of a scheduler in
            a script.
        :param submission_cmd: The command for submitting a job defined in a script to
            the scheduler.
        :param shell_path: Path to the shell used for submitting a job using a
            scheduler.
        :param env_cmd: A command for activating the working environment.
        :param option_cmd: A list of strings containing the scheduler's options for the
            job.
        :type directive: str
        :type submission_cmd: str
        :type shell_path: str
        :type env_cmd: str
        :type option_cmd: List[str]
        """

        for key, value in specs.items():
            setattr(self, key, value)

        self.directive = specs['directive']
        self.job_name_cmd = specs['job_name_cmd']
        self.output_file_cmd = specs['output_file_cmd']
        self.error_file_cmd = specs['error_file_cmd']
        self.submission_cmd = specs['submission_cmd']
        self.option_cmd = specs['option_cmd']
        self.shell_path = specs['shell_path']
        self.env_cmd = specs['env_cmd']

        self.process_output = None

    @abc.abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Return the scheduler's job id of the submited job.

        :return: The job id assigned by the scheduler to the submited job.
        :rtype: int
        """
        raise NotImplementedError

    def make_job_details(self, log_dir: str) -> List[str]:
        """Return a list of three strings specifying the job name, the paths to the
        log.stdout and log.stderr files.

        :param log_dir: The directory where the logs (e.g.: std.out,
            std.err) are saved.
        :type log_dir: str
        :return: a list of three strings specifying information about
            the job: job name, path towards log.stdout and log.stderr.
        :rtype: List[str]
        """
        job_name = log_dir.split(os.sep)
        job_name = os.sep.join(job_name[-2:])
        # Creating job string
        err_path = os.path.join(log_dir, "log.stderr")
        out_path = os.path.join(log_dir, "log.stdout")

        values = [
            self.job_name_cmd + job_name,
            self.error_file_cmd + err_path,
            self.output_file_cmd + out_path,
        ]
        return values

    def submit_job(self, main_cmd, log_dir) -> None:
        """Submit the job to the scheduler and returns a string containing the output of
        the submission command.

        .. note:: There is generally no need to customize this function.

        :param main_cmd: A string of the main bash command to be executed.
        :param log_dir: The log directory where the main script will be saved. The job will be launched from their.
        :type main_cmd: str
        :type log_dir: str
        :raises JobSubmissionError: if the scheduler failed to submit the job.
        """
        cmd = self._make_job(main_cmd, log_dir)
        print(cmd)

        job_path = job_path = os.path.join(log_dir, _get_script_name())
        with open(job_path, "w") as file:
            file.write(cmd)

        try:
            chmod_cmd = _cmd_make_executable(job_path)
            subprocess.check_call(chmod_cmd, shell=True)
            launch_cmd = f"{self.submission_cmd}  {job_path!r}"
            process_output = subprocess.check_output(launch_cmd, shell=True).decode("utf-8")
            print(process_output)
            print("Job launched!")
        except subprocess.CalledProcessError as error:
            print(error.output)
            raise JobSubmissionError(error)
        self.process_output = process_output

    def _cmd_shell_path(self):
        system = platform.system()
        if system in ["Linux", "Darwin"]:
            return f"#!{self.shell_path}\n"
        elif system == "Windows":
            return ""
        raise UnknownSystemError()

    def _make_job(self, main_cmd, log_dir):
        job_command = [main_cmd]

        # Setting shell
        if not self.shell_path:
            raise InvalidShellPathError()
        shell_cmd = [self._cmd_shell_path()]

        # Setting scheduler options

        option_cmd = self.make_job_details(log_dir)
        if self.option_cmd:
            option_cmd += self.option_cmd
        option_cmd = [f"{self.directive} {val}\n" for val in option_cmd]
        option_cmd = ["".join(option_cmd)]

        # Setting environment
        if len(self.env_cmd)>0:
            env_cmds = [f"{cmd}\n" for cmd in self.env_cmd]
        else:
            env_cmds = [f"\n"]

        cmd = "".join(shell_cmd + option_cmd + env_cmds + job_command)
        return cmd



def _get_script_name():
    system = platform.system()
    if system in ["Linux", "Darwin"]:
        return "script.sh"
    elif system == "Windows":
        return "script.bat"
    raise UnknownSystemError()

def _cmd_make_executable(script):
    system = platform.system()
    if system in ["Linux", "Darwin"]:
        return f"chmod +x {script!r}"
    elif system == "Windows":
        return ""
    raise UnknownSystemError()

def _create_scheduler(scheduler_spec):
    specs = deepcopy(scheduler_spec)
    class_name = specs.pop("name")
    info_method = specs.pop("get_info")

    class _ChildScheduler(_Scheduler):
        def __init__(self, shell_path="/bin/bash", env_cmd="", option_cmd=None):
            specs.update(
                {"shell_path": shell_path, "env_cmd": env_cmd, "option_cmd": option_cmd,}
            )

            super().__init__(specs)

        def get_info(self):
            return info_method(self.process_output)

    _ChildScheduler.__name__ = class_name
    globals()[class_name] = _ChildScheduler  # Add the subclass to the global namespace
