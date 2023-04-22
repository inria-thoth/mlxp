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

	.. py:attribute:: env_cmd
		:type: str
		
		Command for activating the working environment. 
		(e.g. 'conda activate my_env')

	.. py:attribute:: shell_path
		:type: Any
		
		Path to the shell used for submitting a job using a scheduler. (default '/bin/bash')

	.. py:attribute:: shell_config_cmd
		:type: bool
		
		command for configuring the shell when submitting a job using a scheduler. 
		(default 'source ~/.bashrc')

	.. py:attribute:: cleanup_cmd
		:type: str
		
		A command for clearning the environment 
		when executing a job submitted by the scheduler.
		(e.g.: 'module purge' for SLURM)  

	.. py:attribute:: option_cmd
		:type: List[str]
		
		A list of strings containing the scheduler's options for the job. 
		This allows to specify the desired resources to the scheduler such as
		the duration of the job, the quantity and type of resources, etc. 
		
		Structure containing the arguments to instantiate the class name.
	"""
	name: str = "NoScheduler"
	shell_path: str = "/bin/bash"
	shell_config_cmd: str = ""
	env_cmd: str = ""
	cleanup_cmd: str = ""
	option_cmd: list = field(default_factory=lambda: [])


@dataclass
class ConfigVersionManager:
	"""
	Structure of the config file for the version manager.


	.. py:attribute:: name
		:type: str
		
		Name of the version manager's class. 

	
	"""


	name: str= MISSING



@dataclass
class ConfigGitVM(ConfigVersionManager):

	"""
	Configs for using the GitVM version manager. 
	It inherits the structure of the class VersionManager.

	.. py:attribute:: name
		:type: str
		
		Name of the version manager's class. 



	.. py:attribute:: parent_target_work_dir
		:type: str
		
		The target parent directory of 
        the new working directory returned by the version manager


    .. py:attribute:: store_requirements
        :type: bool 

        When set to true, the version manager stores a list of requirements and their version.

	"""

	name: str="GitVM"
	parent_target_work_dir: str = "./.workdir"
	store_requirements: bool = False


@dataclass
class Info:
	"""
	A structure storing general information about the run. 



	The following variables are assigned during execution.

	.. py:attribute:: status
		:type: str
		
		Status of a job. The status can take the following values:

		- STARTING: The metadata for the run have been created.

		- RUNNING: The experiment is currently running. 
		
		- COMPLETE: The run is  complete and did not through any error.
		
		- FAILED: The run stoped due to an error.


	
	.. py:attribute:: executable
		:type: str
		
		(private) Name of the python file being executed. 

	.. py:attribute:: app
		:type: str
		
		(Private) Path to the python app used for executing the code.

	.. py:attribute:: hostname
		:type: str
		
		(private) Name of the host from which code is executed.

	.. py:attribute:: user
		:type: str
		
		(private) User name executing the code. 

	.. py:attribute:: process_id
		:type: int
		
		Id of the process assigned to the job during execution.

	.. py:attribute:: start_date
		:type: Any
		
		(Private) Date at which job started.

	.. py:attribute:: start_time
		:type: Any
		
		(Private) Time at which job started.

	.. py:attribute:: end_date
		:type: Any
		
		(Private) Date at which job ended.

	.. py:attribute:: end_time
		:type: Any
		
		(Private) Time at which job ended.


	"""


	status: str = "STARTING"
	executable: str = ""
	app: str = ""
	hostname: str = ""
	user: str = "${oc.env:USER}"
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
	log_streams_to_file: bool = False
	parent_log_dir: str = "./logs" #os.path.join(os.getcwd(),"data","outputs")


@dataclass
class ConfigDefaultLogger(ConfigLogger):

	name: str="DefaultLogger"	

@dataclass
class MlxpyConfig:
	logger: ConfigLogger = ConfigDefaultLogger()
	scheduler: ConfigScheduler = ConfigScheduler()
	version_manager: ConfigVersionManager = ConfigGitVM()
	use_version_manager: bool= False
	use_scheduler: bool=False
	use_logger: bool=True
	interactive_mode: bool= True

@dataclass
class Metadata:
	"""
		The structure of the config file. 

	.. py:attribute:: info
		:type: Info
		
		Contains config information of the run 
		(hostname, command, application,  etc) 
		(default Info) 

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

  
	.. py:attribute:: config
		:type: Any
		
		Contains user user configs

	"""
	info: Info = Info()
	mlxpy: MlxpyConfig = MlxpyConfig()
	config: Any = None

#cs = ConfigStore.instance()
# cs.store(group="mlxpy", 
# 		 name="config", 
# 		 node=mlxpy(), 
# 		 provider="mlxpy")

# cs.store(
#     group="mlxpy",
#     name="config",
#     node=mlxpy(),
#     provider="mlxpy")

# cs.store(name="OAR", node=OARScheduler())
# cs.store(name="SLURM", node=SLURMScheduler())
# cs.store(name="", node=None)
# cs.store(name="GitVM", node=GitVM())
# cs.store(name="Logger", node=DefaultLogger())


