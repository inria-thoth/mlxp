from dataclasses import dataclass, field
import os

from typing import Any, Callable, List
from omegaconf import MISSING

@dataclass
class SchedulerArgs:
	"""
	Configs containing arguments to instantiate the scheduler

	.. py:attribute:: cleanup_cmd
		:type: str
		
		A command for clearning the environment 
		when executing a job submitted by the scheduler.

	.. py:attribute:: option_cmd
		:type: List[str]
		
		A list of strings containing the scheduler's options for the job. 
		This allows to specify the desired resources to the scheduler such as
		the duration of the job, the quantity and type of resources, etc. 

	"""

	cleanup_cmd: str = ""
	option_cmd: list = field(default_factory=lambda: [])


@dataclass
class Scheduler:
	"""
	Structure of the scheduler config file.

	.. py:attribute:: class_name
		:type: str
		
		Name of the scheduler's class. 

	.. py:attribute:: use_scheduler
		:type: bool
		
		Uses the scheduler if set to true.

	.. py:attribute:: args
		:type: Any
		
		Structure containing the arguments to instantiate the class class_name.
	"""
	class_name: str = MISSING
	use_scheduler: bool = False
	args: Any = SchedulerArgs()

@dataclass
class OARScheduler(Scheduler):

	"""
	Configs for OAR job scheduler. See documentation in: http://oar.imag.fr/docs/2.5/#ref-user-docs 
	"""

	class_name: str = "experimentalist.launching.schedulers.OARScheduler"

@dataclass
class NoScheduler(Scheduler):
	class_name: str = "experimentalist.launching.schedulers.NoScheduler"


@dataclass
class SLURMScheduler(Scheduler):
	"""
	Configs for SLURM job scheduler. See documentation in: https://slurm.schedmd.com/documentation.html
	"""

	class_name: str = "experimentalist.launching.schedulers.SLURMScheduler"



@dataclass
class WDManager:
	"""
	Structure of the config file for the working directory manager.


	.. py:attribute:: class_name
		:type: str
		
		Name of the working directory manager's class. 


	.. py:attribute:: args
		:type: Any
		
		Structure containing the arguments to instantiate the class class_name.
	
	"""


	class_name: str= MISSING
	args: Any = MISSING

@dataclass
class GitWDMangerArgs:

	"""
	Configs containing arguments to instantiate the LastGitCommitWD working directory manager. 
	
	.. py:attribute:: parent_target_work_dir
		:type: str
		
		Name of the parent directory of the target working directory to be created.


	.. py:attribute:: forceCommit
		:type: bool
		
	   When set to true, raises an error if there are uncommited changes. 
	   Displays a warning otherwise. 

	.. py:attribute:: forceTracking
		:type: bool
		
	   When set to true, raises an error if there are untracked files. 
	   Displays a warning otherwise. 
	"""

	parent_target_work_dir: str = os.path.join(os.getcwd(), "data/.workdir") 
	forceCommit: bool = True
	forceTracking: bool = True

@dataclass
class LastGitCommitWD(WDManager):

	"""
	Configs for using the LastGitCommitWD working directory manager. 
	It inherits the structure of the class WDManager and uses GitWDMangerArgs 
	as argument during instantiation.
	"""

	class_name: str="experimentalist.launching.wd_manager.LastGitCommitWD"
	args: Any = GitWDMangerArgs()



@dataclass
class CWD(WDManager):

	"""
	Configs for using the CWD working directory manager.
	"""

	class_name: str="experimentalist.launching.wd_manager.CWD"
	args: Any = None


@dataclass
class System:
	"""
	Structure of the system config file. 

	.. py:attribute:: env
		:type: str
		
		Command for activating the working environment. 
		By default it activates the default conda environment

	.. py:attribute:: shell_path
		:type: Any
		
		Path to the shell used for submitting a job using a scheduler. (defulat '/bin/bash')

	.. py:attribute:: shell_config_cmd
		:type: bool
		
		command for configuring the shell when submitting a job using a scheduler. 
		(default 'source ~/.bashrc')

	The following variables are assigned during execution.

	.. py:attribute:: status
		:type: bool
		
		Status of a job. The status can take the following values:

		- STARTING: The metadata for the run have been created.

		- RUNNING: The experiment is currently running. 
		
		- COMPLETE: The run is  complete and did not through any error.
		
		- FAILED: The run stoped due to an error.


	
	.. py:attribute:: cmd
		:type: bool
		
		(private) Name of the python file being executed. 

	.. py:attribute:: app
		:type: bool
		
		(Private) Path to the python app used for executing the code.

	.. py:attribute:: hostname
		:type: bool
		
		(private) Name of the host from which code is executed.

	.. py:attribute:: user
		:type: str
		
		(private) User name executing the code. 

	.. py:attribute:: process_id
		:type: bool
		
		Id of the process assigned to the job during execution.

	.. py:attribute:: date
		:type: bool
		
		(Private) Date at which job started.

	.. py:attribute:: time
		:type: bool
		
		(Private) Time at which job started.

	"""



	user: str = "${oc.env:USER}"
	env: str = "conda activate '${oc.env:CONDA_DEFAULT_ENV}'"
	shell_path: str = "/bin/bash"
	shell_config_cmd: str = "source ~/.bashrc"
	status: str = MISSING
	cmd: str = MISSING
	app: str = MISSING
	hostname: str = MISSING
	process_id: int = MISSING
	date: Any = MISSING
	time: Any = MISSING


@dataclass
class Logs:
	"""
	Structure of the config file for the logs. 
	The outputs for each run are saved in a directory of the form 
	'parent_log_dir/log_name/log_id' 
	which is stored in the variable 'path' during execution.

	.. py:attribute:: parent_log_dir
		:type: str
		
		Absolute path of the parent directory where the logs of a run are stored. 
		(default "data/outputs")     

	.. py:attribute:: log_name
		:type: str
		
		Name of the directory containing the logs for all runs indexed by their log_id s  

	.. py:attribute:: log_id
		:type: Any
		
		Unique id of a run. By default it is not provided and assigned uniquely during execution. 
		If the id is provided, then the output of a run are saved in the directory with given log_id. 

	.. py:attribute:: log_to_file
		:type: bool
		
		If true logs the system stdout and stderr of a run to a file named 
		"log.txt" in the path directory.

	"""


	parent_log_dir: str = os.path.join(os.getcwd(),"data/outputs")
	log_name: str = "logs"
	log_id: Any = None
	path: str = MISSING
	log_to_file: bool = False
	
 
	
@dataclass
class Config:
	"""
		The structure of the config file. 

	.. py:attribute:: system
		:type: System
		
		Contains config information of the system 
		(environment, shell, application, command, hostname, etc) 
		(default System) 

	.. py:attribute:: logs
		:type: Logs
		
		Contains config information for the logs (log directory, etc) (default Logs) 

	.. py:attribute:: scheduler
		:type: Scheduler
		
		Contains config information for the scheduler  (default NoScheduler) 

	.. py:attribute:: wd_manager
		:type: WDManager
		
		Contains config information for the working directory manager  (default LastGitCommitWD) 
  
	.. py:attribute:: custom
		:type: Any
		
		Contains user custom configs

	"""

	system: System = System()
	logs: Logs = Logs()
	scheduler: Scheduler = NoScheduler()
	wd_manager: WDManager = LastGitCommitWD()
	custom: Any = None
