from dataclasses import dataclass, field
import os

from typing import Any, Callable, List, Union
from omegaconf import MISSING
from hydra.core.config_store import ConfigStore



@dataclass
class ConfigScheduler:
	"""
	Structure of the scheduler config file.

	.. py:attribute:: name
		:type: str
		
		Name of the scheduler's class. 

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

	.. py:attribute:: cleanup_cmd
		:type: str
		
		A command for clearning the environment 
		when executing a job submitted by the scheduler.

	.. py:attribute:: option_cmd
		:type: List[str]
		
		A list of strings containing the scheduler's options for the job. 
		This allows to specify the desired resources to the scheduler such as
		the duration of the job, the quantity and type of resources, etc. 
		
		Structure containing the arguments to instantiate the class name.
	"""
	name: str = "Scheduler"
	shell_path: str = ""
	shell_config_cmd: str = ""
	env_cmd: str = ""
	cleanup_cmd: str = ""
	option_cmd: list = field(default_factory=lambda: [])


@dataclass
class ConfigOARScheduler(ConfigScheduler):

	"""
	Configs for OAR job scheduler. See documentation in: http://oar.imag.fr/docs/2.5/#ref-user-docs 
	"""

	name: str = "OARScheduler"

	
@dataclass
class ConfigSLURMScheduler(ConfigScheduler):
	"""
	Configs for SLURM job scheduler. See documentation in: https://slurm.schedmd.com/documentation.html
	"""

	name: str = "SLURMScheduler"
	


@dataclass
class ConfigVersionManager:
	"""
	Structure of the config file for the working directory manager.


	.. py:attribute:: name
		:type: str
		
		Name of the working directory manager's class. 


	.. py:attribute:: args
		:type: Any
		
		Structure containing the arguments to instantiate the class name.
	
	"""


	name: str= MISSING



@dataclass
class ConfigGitVM(ConfigVersionManager):

	"""
	Configs for using the LastGitCommitWD working directory manager. 
	It inherits the structure of the class VersionManager.

	.. py:attribute:: parent_target_work_dir
		:type: str
		
		Name of the parent directory of the target working directory to be created.


	.. py:attribute:: handleUncommitedChanges
		:type: bool
		
	   When set to true, raises an error if there are uncommited changes. 
	   Displays a warning otherwise. 

	.. py:attribute:: handleUntrackedFiles
		:type: bool
		
	   When set to true, raises an error if there are untracked files. 
	   Displays a warning otherwise. 

	"""

	name: str="GitVM"
	parent_target_work_dir: str = "./.workdir" #os.path.join(os.getcwd(), "data/.workdir") 
	skip_requirements: bool = False
	interactive_mode: bool= True

@dataclass
class RunInfo:
	"""
	A structure storing general information about the run. 



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
	status: str = "STARTING"
	cmd: str = ""
	app: str = ""
	hostname: str = ""
	process_id: int = -1
	start_date: Any = ""
	start_time: Any = ""
	log_dir: str = ""
	log_id: int = -1
	
	
@dataclass
class ConfigLogger:
	"""
	Structure of the config file for the logs. 
	The outputs for each run are saved in a directory of the form 
	'parent_log_dir/log_id' 
	which is stored in the variable 'path' during execution.

	.. py:attribute:: parent_log_dir
		:type: str
		
		Absolute path of the parent directory where the logs of a run are stored. 
		(default "data/outputs")     

	.. py:attribute:: forced_log_id
		:type: Any
		
		An id optionally provided by the user for the run. If forced_log_id is an integer, 
		then the logs of the run will be stored under 'parent_log_dir/forced_log_id'. Otherwise, 
		the logs will be stured in a directory 'parent_log_dir/log_id' where 'log_id' 
		is assigned uniquely for the run during execution. 

	.. py:attribute:: log_streams_to_file
		:type: bool
		
		If true logs the system stdout and stderr of a run to a file named 
		"log.txt" in the path directory.

	"""

	name: str=MISSING
	parent_log_dir: str = MISSING #os.path.join(os.getcwd(),"data","outputs")
	forced_log_id: int = -1
	config_file_name: str= "metadata"
	log_streams_to_file: bool = False

@dataclass
class ConfigDefaultLogger(ConfigLogger):

	name: str="DefaultLogger"
	parent_log_dir: str = "./logs" #os.path.join(os.getcwd(),"data","outputs")
	

@dataclass
class Base_config:
	logger: ConfigLogger = ConfigDefaultLogger()
	scheduler: ConfigScheduler = ConfigScheduler()
	version_manager: ConfigVersionManager = ConfigGitVM()
	use_version_manager: bool= False
	use_scheduler: bool=False
	use_logger: bool=True

@dataclass
class Metadata:
	"""
		The structure of the config file. 

	.. py:attribute:: run_info
		:type: RunInfo
		
		Contains config information of the run 
		(hostname, command, application,  etc) 
		(default RunInfo) 

	.. py:attribute:: logger
		:type: Logger
		
		Contains config information for the logs (log directory, etc) (default None) 

	.. py:attribute:: scheduler
		:type: Scheduler
		
		Contains config information for the scheduler  (default None) 

	.. py:attribute:: version_manager
		:type: WDManager
		
		Contains config information for the working directory manager  (default None) 

	.. py:attribute:: seed_config
		:type: Any
		
		Contains user defined parameters for seeding the code.
		Can a number or a more complex structure following hydra configs options.

  
	.. py:attribute:: user_config
		:type: Any
		
		Contains user user configs

	"""
	run_info: RunInfo = RunInfo()
	base_config: Base_config = Base_config()
	user_config: Any = None

#cs = ConfigStore.instance()
# cs.store(group="base_config", 
# 		 name="config", 
# 		 node=Base_config(), 
# 		 provider="base_config")

# cs.store(
#     group="experimentalist",
#     name="config",
#     node=Base_config(),
#     provider="experimentalist")

# cs.store(name="OAR", node=OARScheduler())
# cs.store(name="SLURM", node=SLURMScheduler())
# cs.store(name="", node=None)
# cs.store(name="GitVM", node=GitVM())
# cs.store(name="Logger", node=DefaultLogger())


