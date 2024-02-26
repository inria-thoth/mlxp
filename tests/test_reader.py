import pytest
import pathlib
import os
import sys
import subprocess
import mlxp


from mlxp.reader import Reader

# Unit tests for the class Reader in mlxp/reader.py
tutorial_path = os.path.join(str(pathlib.Path(os.getcwd()).parent),'tutorial')


def _delete_directory(log_dir):
	import shutil
	import os
	if os.path.exists(log_dir):
		try:
			shutil.rmtree(log_dir)
		except:
			pass

@pytest.fixture
def launch():
	# Launching toy experiments

	# Delete directory ./logs/ if it exists 
	log_dir = os.path.join(tutorial_path,'logs')
	_delete_directory(log_dir)
	scripts = pathlib.Path(tutorial_path).resolve().glob('launch_script.sh')

	for script in scripts:
		parent_path = str(script.parent)
		sys.path.insert(0,parent_path)

	parent_path = str(script.parent)
	sys.path.insert(0,parent_path)

	with open(script, 'r') as file:
		script_code = file.read()
	rc = subprocess.call([f"cd {tutorial_path}\n"+script_code] , shell=True)

	assert rc==0
	yield rc

	_delete_directory(log_dir)


@pytest.fixture
def reader(launch):
	# Create reader object 


	parent_log_dir = os.path.join(tutorial_path,'logs')
	reader = mlxp.Reader(parent_log_dir)
	
	assert reader.src_dir == os.path.abspath(parent_log_dir)

	# assert that fields is a pandas df that is not empty
	assert not reader.fields.empty
	assert not reader.searchable.empty
	
	# assert that searchable fields are subsets of fields that start with info or config 

	assert set(reader.searchable.index) <= set(reader.fields.index)
	assert all(reader.searchable.index.str.startswith('info') | reader.searchable.index.str.startswith('config'))

	yield reader


def test_filter(reader):
	# Test the method filter of a Reader object

	# Querying 
	query = "info.status in ['COMPLETE', 'RUNNING'] & config.optimizer.lr > 0.1"
	results = reader.filter(query_string=query)

	# Assert that restults keys are equal to the reader's fields
	assert set(results.keys()) == set(reader.fields.index)

	# Assert info.staus is in ['COMPLETE', 'RUNNING']
	assert all(res in ['COMPLETE', 'RUNNING'] for res in results[:]['info.status'])
	# Assert optimizer.lr > 0.1
	assert all(lr > 0.1 for lr in results[:]['config.optimizer.lr'])
	# Assert df has 8 elements
	assert len(results) == 18

	# Test equality query

	query = " config.seed == 0 "
	results = reader.filter(query_string=query)

	# Assert seed==0
	assert all(seed==0 for seed in results[:]['config.seed'])

	# Test negation query

	query = " config.seed != 0 "
	results = reader.filter(query_string=query)

	assert all(seed!=0 for seed in results[:]['config.seed'])

	# Test less than query

	query = " config.optimizer.lr < 1. "
	results = reader.filter(query_string=query)

	assert all(lr<1. for lr in results[:]['config.optimizer.lr'])

	# Test greater than query

	query = " config.optimizer.lr > 1. "
	results = reader.filter(query_string=query)

	assert all(lr>1. for lr in results[:]['config.optimizer.lr'])

	# Test less than or equal to query

	query = " config.optimizer.lr <= 1. "
	results = reader.filter(query_string=query)

	assert all(lr<=1. for lr in results[:]['config.optimizer.lr'])

	# Test greater than or equal to query

	query = " config.optimizer.lr >= 1. "
	results = reader.filter(query_string=query)

	assert all(lr>=1. for lr in results[:]['config.optimizer.lr'])

	# Test in query

	query = " config.seed in [1,4] "
	results = reader.filter(query_string=query)

	assert all(seed in [1,4] for seed in results[:]['config.seed'])


	# Test not in query

	query = " ~ config.seed in [1,4] "
	results = reader.filter(query_string=query)

	assert all(seed not in [1,4] for seed in results[:]['config.seed'])

	# Test and query

	query = " config.seed == 0 & config.optimizer.lr > 1. "
	results = reader.filter(query_string=query)

	assert all(seed==0 for seed in results[:]['config.seed'])
	assert all(lr>1. for lr in results[:]['config.optimizer.lr'])

	# Test or query

	query = " config.seed == 0 | config.optimizer.lr > 1. "
	results = reader.filter(query_string=query)

	assert all(seed==0 for seed in results[:]['config.seed']) or all(lr>1. for lr in results[:]['config.optimizer.lr'])


	# Test parenthesis query

	query = " (config.seed == 0 | config.optimizer.lr > 1.) & config.optimizer.lr < 1. "
	results = reader.filter(query_string=query)

	assert all((seed==0 or lr>1.) and lr<1. for seed,lr in zip(results[:]['config.seed'],results[:]['config.optimizer.lr']))

	# Test empty query

	query = ""
	results = reader.filter(query_string=query)

	assert len(results) == 18



def test_diff(reader):
	
	results = reader.filter()

	diffs = results.diff()
	assert set(diffs)==set(['config.model.num_units','config.optimizer.lr', 'config.seed'])

def test_dataframe_groupby(reader):
	results = reader.filter()
	group_keys = ['config.optimizer.lr']
	grouped_results = results.groupby(group_keys)
	
	assert len(grouped_results.keys()) == 2
	assert all(key in [(10.,),(1.,)] for key in grouped_results.keys())
	assert all(len(res)==9 for key,res in grouped_results.items())


def test_dataframe_aggregate(reader):
	results = reader.filter()
	group_keys = ['config.optimizer.lr']
	grouped_results = results.groupby(group_keys)
	
	def mean(x):
		import numpy as np
		x = np.array(x)
		return np.mean(x,axis=0)
	agg_maps = (mean,('train.loss','train.epoch'))
	agg_results = grouped_results.aggregate(agg_maps)
	assert len(agg_results.keys()) == 2
	assert all(key in [(10.,),(1.,)] for key in agg_results.keys())
	assert all(len(res)==1 for key,res in agg_results.items())

	manual_agg = {key: mean(value[:]['train.loss']) for key,value in grouped_results.items()}
	assert all(sum(agg_results[key][0]['fmean.train.loss'] == manual_agg[key])==manual_agg[key].shape[0] for key in agg_results.keys())

def test_dataframe_filter(reader):
	results = reader.filter()
	group_keys = ['config.model.num_units','config.optimizer.lr']
	grouped_results = results.groupby(group_keys)
	
	def mean(x):
		import numpy as np
		x = np.array(x)
		return np.mean(x,axis=0)
	agg_maps = (mean,('train.loss','train.epoch'))
	agg_results = grouped_results.aggregate(agg_maps)

	def my_min(x):
		import numpy as np
		x = np.array(x)
		return np.min(x[:,-1])

	def argmin(x):
		import numpy as np
		x = np.array(x)
		return x[:,-1]==np.min(x[:,-1])
	methods_keys = ['config.model.num_units']
	agg_results = grouped_results.aggregate((mean,'train.loss'))
	best_results = agg_results.filter((argmin,'fmean.train.loss'), bygroups = methods_keys)
	import numpy as np
	methods_groups = agg_results.ungroup().groupby(methods_keys)
	manual_filter = {key: my_min(values[:]['fmean.train.loss']) for key,values in methods_groups.items()}
	for key, value in best_results.items():
		array_val = np.array(value[:]['fmean.train.loss']) 
		assert array_val[:,-1] == manual_filter[(key[0],)]




