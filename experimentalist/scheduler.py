import os
import subprocess
from hydra.core.hydra_config import HydraConfig
from datetime import datetime
import omegaconf
from omegaconf.errors import OmegaConfBaseException
import abc
from typing import List, Union




class Scheduler(abc.ABC):
    """
    An abstract class whose children allow to submit jobs 
    using a particular job scheduler such as OAR or SLURM. 

    .. py:attribute:: directive
        :type: str 

        The string that preceeds the command options of a scheduler in a script. 
        (e.g.: '#OAR' for OAR and '#SBATCH' for SLURM)

    .. py:attribute:: submission_cmd
        :type: str 

        The command for submitting a job defined in a script to the scheduler.
        (e.g.: 'oarsub -S' for OAR and 'sbatch' for SLURM).


    .. py:attribute:: cleanup_cmd
        :type: str 

        A command used in a script to prepare the environment before executing the main code.
        (e.g.: 'module purge' for SLURM)  

    .. py:attribute:: option_cmd
        :type: List[str] 
        
        A list of strings containing the scheduler's options for the job. 
        This allows to specify the desired resources to the scheduler such as
        the duration of the job, the quantity and type of resources, etc. 

    """


    def __init__(self, 
                directive: str, 
                submission_cmd: str,
                shell_path: str ="/bin/bash", 
                shell_config_cmd:str ="",
                env_cmd:str="",
                cleanup_cmd: str ="", 
                option_cmd:List[str]=[]):
        """
        Constructor

        :param directive: The string that preceeds the command options of a scheduler in a script. 
        :param submission_cmd: The command for submitting a job defined in a script to the scheduler.
        :param cleanup_cmd: A command for cleaning up the environment before executing code.
        :param option_cmd: A list of strings containing the scheduler's options for the job.


        :type directive: str
        :type submission_cmd: str
        :type cleanup_cmd: str
        :type option_cmd: List[str] 

        """



        self.directive = directive
        self.cleanup_cmd = cleanup_cmd
        self.submission_cmd = submission_cmd
        self.option_cmd = option_cmd
        self.shell_config_cmd = shell_config_cmd
        self.shell_path = shell_path
        self.env_cmd = env_cmd

    @abc.abstractmethod
    def make_job_details(self, log_dir:str)->List[str]:
        """
        Returns a list of three strings specifying the job name, the paths to the log.stdout and log.stderr files.   
        
        :param log_dir: The directory where the logs (e.g.: std.out, std.err) are saved.  
        :type log_dir: str
        :return: a list of three strings specifying information about the job: job name, path towards log.stdout and log.stderr.
        :rtype: List[str] 

        """
        pass 

    @abc.abstractmethod
    def get_job_id(self,process_output):
        """
            Returns the scheduler's job id of the submited job.

            :param process_output: The output string returned by self.submit_job
            :type process_output: str
            :return: The job id assigned by the scheduler to the submited job.
            :rtype: int 
   
        """    

        pass


    def submit_job(self,main_cmd, log_dir):
        """
            Submits the job to the scheduler and returns 
            a string containing the output of the submission command. 

            .. note:: There is generally no need to customize this function.

            :param job_path: A path to an existing script defining the job.
            :type job_path: str
            :return: The output of the job submission command. 
            :rtype: str 

        """ 
        cmd = self._make_job(main_cmd,log_dir)
        print(cmd)

        job_path = job_path = os.path.join(log_dir, "script.sh")
        with open(job_path, "w") as f:
            f.write(cmd)

        try:
            chmod_cmd = f"chmod +x {job_path!r}"
            subprocess.check_call(chmod_cmd, shell=True)
            launch_cmd = f"{self.submission_cmd}  {job_path!r}"
            process_output = subprocess.check_output(launch_cmd, shell=True).decode("utf-8")
            print(process_output)
            print("Job launched!")
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise JobSubmissionError(e)

        return process_output

    def _make_job(self,main_cmd,log_dir):
        job_command = [main_cmd]

        ## Setting shell   
        shell_cmd = [f"#!{self.shell_path}\n"]
        
        ## Setting scheduler options
        
        option_cmd = self.make_job_details(log_dir)
        option_cmd += self.option_cmd
        option_cmd = [f"{self.directive} {val}\n" for val in option_cmd]
        option_cmd= ["".join(option_cmd)]
        
        ## Setting environment
        env_cmds = [f"{self.shell_config_cmd}\n", 
                    f"{self.cleanup_cmd}\n"]
        try:
            env_cmds += [f"{self.env_cmd}\n"]
        except OmegaConfBaseException:
            pass

        cmd = "".join(shell_cmd + option_cmd + env_cmds + job_command)
        return cmd


class NoScheduler(Scheduler):

    def __init__(self,shell_path="", 
                  shell_config_cmd="",
                  env_cmd="", 
                  cleanup_cmd="", 
                  option_cmd = []):
        super().__init__(
                        directive="", 
                        submission_cmd="",
                        shell_path=shell_path, 
                        shell_config_cmd=shell_config_cmd,
                        env_cmd=env_cmd,
                        cleanup_cmd=cleanup_cmd, 
                        option_cmd = option_cmd)  

    def make_job_details(self, log_dir:str)->List[str]:
        """
        Returns a list of three strings specifying the job name, the paths to the log.stdout and log.stderr files.   
        
        :param log_dir: The directory where the logs (e.g.: std.out, std.err) are saved.  
        :type log_dir: str
        :raises Exception: This is not a valid scheduler, it does nothing 

        """
        raise Exception( 'No scheduler is defined! Please set the option experimentalist.scheduler.name to a valid scheduler (default OARScheduler or SLURMScheduler) ' ) 


    def get_job_id(self,process_output):
        """
            Returns the scheduler's job id of the submited job.

            :param process_output: The output string returned by self.submit_job
            :type process_output: str
            :raises Exception: This is not a valid scheduler, it does nothing 
        """

    
        raise Exception( 'No scheduler is defined! Please set the option experimentalist.scheduler.name to a valid scheduler (default OARScheduler or SLURMScheduler) ' )


    def submit_job(self,main_cmd, log_dir):
        """
            Submits the job to the scheduler and returns 
            a string containing the output of the submission command. 

            .. note:: There is generally no need to customize this function.

            :param job_path: A path to an existing script defining the job.
            :type job_path: str
            :raises Exception: This is not a valid scheduler, it does nothing 

        """  
        raise Exception( 'No scheduler is defined! Please set the option experimentalist.scheduler.name to a valid scheduler (default OARScheduler or SLURMScheduler) ' )

class OARScheduler(Scheduler):
    """
        OAR job scheduler, see documentation in: http://oar.imag.fr/docs/2.5/#ref-user-docs
    """


    def __init__(self,shell_path="/bin/bash", 
                      shell_config_cmd="",
                      env_cmd="", 
                      cleanup_cmd="", 
                      option_cmd = []):
        super().__init__(
                        directive="#OAR", 
                        submission_cmd="oarsub -S",
                        shell_path=shell_path, 
                        shell_config_cmd=shell_config_cmd,
                        env_cmd=env_cmd,
                        cleanup_cmd=cleanup_cmd, 
                        option_cmd = option_cmd)
    
    def get_job_id(self,process_output:str)->int:
        return process_output.split("\n")[-2].split("=")[-1]

    def make_job_details(self,log_dir):
        job_name = log_dir.split(os.sep)
        job_name = os.sep.join(job_name[-2:])
        # Creating job string
        err_path = os.path.join(log_dir, "log.stderr")
        out_path = os.path.join(log_dir, "log.stdout")


        values = [
            f"-n {job_name}",
            f"-E {err_path}",
            f"-O {out_path}",
        ]
        return values





class SLURMScheduler(Scheduler):
    """
    SLURM job scheduler, see documentation in: https://slurm.schedmd.com/documentation.html
    """


    def __init__(self,shell_path="/bin/bash", 
                      shell_config_cmd="",
                      env_cmd="", 
                      cleanup_cmd="module purge", 
                      option_cmd=[]):
        super().__init__(
                        directive="#SBATCH", 
                        submission_cmd="sbatch",
                        shell_path=shell_path, 
                        shell_config_cmd=shell_config_cmd,
                        env_cmd=env_cmd,
                        cleanup_cmd=cleanup_cmd, 
                        option_cmd= option_cmd)

    def make_job_details(self,log_dir):
        job_name = log_dir.split(os.sep)
        job_name = os.sep.join(job_name[-2:])
        # Creating job string
        err_path = os.path.join(log_dir, "log.stderr")
        out_path = os.path.join(log_dir, "log.stdout")

        values = [
            f"--job-name={job_name}",
            f"--output={out_path}",
            f"--error={err_path}",
        ]
        return values

class JobSubmissionError(Exception):
    """Raised when failed to submit a job using a scheduler"""
    pass 





