import os
import pytest
from mlxp.logger import Logger
from mlxp.data_structures.config_dict import convert_dict

# Unit tests for the class Logger in mlxp/logger.py

def _delete_directory(log_dir):
	import shutil
	import os
	if os.path.exists(log_dir):
		try:
			shutil.rmtree(log_dir)
		except:
			pass

@pytest.fixture
def logger():
	# Create a logger object to log the results of the experiment
	
	# Patlform agnostic relative path 
	import os
	log_dir = os.path.abspath('logs')


	_delete_directory(log_dir)
	logger = Logger(log_dir)
	yield logger

	_delete_directory(log_dir)

def test_Logger(logger):
	# Create a logger object to log the results of the experiment
	assert logger.log_id == 1
	# get absolute path of logs/1/
	
	log_dir = os.path.abspath('logs')


	assert logger.log_dir == os.path.join(log_dir,'1')

def test_log_configs(logger):
	# Test the method log_metrics of a Logger object

	# Log the configurations
	configs = {'config':{'optimizer':{'lr':0.01,'momentum':0.9},'model':{'num_units':100}},
				'info':{'status':'COMPLETE'}}
	configsdict =  convert_dict(configs, src_class=dict)
	logger._log_configs(configsdict)
	
	# Load the yaml files that were logged
	import yaml
	with open(logger.log_dir+'/metadata/config.yaml') as file:
		config = yaml.safe_load(file)
	with open(logger.log_dir+'/metadata/info.yaml') as file:
		info = yaml.safe_load(file)

	# Assert loaded config dict is equal to the original
	assert config == configs['config']
	assert info == configs['info']


def test_log_metrics(logger):

	metric_dict = {'loss': 1., 'epoch':0}
	logger.log_metrics(metric_dict, 'train')

	# Load the yaml files that were logged
	import json
	with open(os.path.join(logger.log_dir,'metrics','train.json')) as file:
		for line in file:
			metrics = json.loads(line)

	# Assert loaded metric dict is equal to the original
	assert metrics == metric_dict

def test_log_artifacts(logger):

	# Log the artifacts
	artifacts = [1,2,3]
	logger.log_artifacts(artifacts,artifact_name='result.pkl',artifact_type='pickle')

	# Load the yaml files that were logged
	import dill as pkl
	file_path = os.path.join(logger.log_dir,'artifacts','pickle','result.pkl')
	with open(file_path,"rb") as file:
		loaded_artifacts = pkl.load(file)

	# Assert loaded artifact dict is equal to the original: these are two lists
	assert loaded_artifacts == artifacts


def test_register_artifact_type(logger):
		
	# Register a new artifact type
	def save_pickle(artifact, path):
		import dill as pkl
		with open(path, 'wb') as file:
			pkl.dump(artifact, file)
	def load_pickle(path):
		import dill as pkl
		with open(path, 'rb') as file:
			return pkl.load(file)
	# Log the artifacts

	logger.register_artifact_type('my_pickle', save_pickle, load_pickle)

	# Log the artifacts
	artifacts = [1,2,3]
	logger.log_artifacts(artifacts,artifact_name='result.pkl',artifact_type='my_pickle')

	import yaml
	import marshal, types
	artifact_type = 'my_pickle'
	artifacts_dir= os.path.join(logger.log_dir,'artifacts')
	types_file = os.path.join(artifacts_dir,'.keys','custom_types.yaml')
	with open(types_file, "r") as f:
		types_dict_marshal = yaml.safe_load(f)
	code = marshal.loads(types_dict_marshal[artifact_type]['load'])
	my_load = types.FunctionType(code, globals(), "load")
	code = marshal.loads(types_dict_marshal[artifact_type]['save'])
	my_save = types.FunctionType(code, globals(), "save")

	artifact_path = os.path.join(logger.log_dir,'artifacts','my_pickle','result.pkl')
	loaded_artifacts = my_load(artifact_path)

	# Assert loaded artifact type dict is equal to the original
	assert loaded_artifacts == artifacts




