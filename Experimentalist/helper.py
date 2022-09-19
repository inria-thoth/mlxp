import pandas as pd
import matplotlib.pyplot as plt
#%matplotlib inline
import seaborn as sns
import numpy as np
import matplotlib
from matplotlib import cm
import os
import json
from functools import reduce
import matplotlib.colors as mpl_colors
from math import log10
from Experimentalist.reader import Reader
import matplotlib as mpl

def load_dict_from_json(json_file_name):
    out_dict = {}
    try:
        with open(json_file_name) as f:
            for line in f:
                cur_dict = json.loads(line)
                keys = cur_dict.keys()
                for key in keys:
                    if key in out_dict:
                        out_dict[key].append(cur_dict[key])
                    else:
                        out_dict[key] = [cur_dict[key]]
    except Exception as e:
        print(str(e))


def compute_time_to_eps(data,val_key,epsilon, avg_time_dict=None):
	values = np.array(data[val_key])
	#print(values[0])
	values = values/values[0]
	index = next((i for i, x in enumerate(values<epsilon) if x), None)
	prefix = ''
	if index is None:
		time_to_eps_dict = {'real_time': np.inf,
							'idealized_time': np.inf}
	else:
		if avg_time_dict is not None:
			t1,t2,t3,t4 = avg_time_dict['cost_outer_grad'][0],\
						avg_time_dict['cost_inner_grad'][0],\
						avg_time_dict['cost_inner_hess'][0],\
						avg_time_dict['cost_inner_jac'][0]
		else:
			t1,t2,t3,t4 = 1.,1.,1.,1.

		real_time = data[prefix+'time'][index]
		idealized_time = data[prefix+'outer_grad'][index]*t1\
						+ data[prefix+'inner_grad'][index]*t2\
						+ data[prefix+'inner_hess'][index]*t3\
						+ data[prefix+'inner_jac'][index]*t4
		time_to_eps_dict = {'real_time': real_time,
							'idealized_time': idealized_time}
	return time_to_eps_dict


def compute_error_at_time(data, val_key, time, b_size, avg_time_dict=None):
	idealized_time = compute_idealized_time(data,avg_time_dict, b_size) 
	values = np.array(data[val_key])
	values = values/values[0]
	values_at_time_dict = {}
	for time_key,value in time.items():
		if time_key =='idealized_time':
			time_array =  np.array(idealized_time)
		else:
			time_array =  np.array(data[time_key])
		index = next((i for i, x in enumerate(time_array>value) if x), len(time_array)-1)
		#import pdb
		#pdb.set_trace()
		values_at_time_dict['err_at_'+time_key] = values[index]
	return values_at_time_dict

def compute_idealized_time(data, avg_time_dict,b_size, prefix=''):
	O,G,H,J = data[prefix+'outer_grad'],\
				data[prefix+'inner_grad'],\
				data[prefix+'inner_hess'],\
				data[prefix+'inner_jac']
	if avg_time_dict is not None:
		t1,t2,t3,t4 = avg_time_dict['cost_outer_grad'][0],\
					avg_time_dict['cost_inner_grad'][0],\
					avg_time_dict['cost_inner_hess'][0],\
					avg_time_dict['cost_inner_jac'][0]
	else:
		t1,t2,t3,t4 = 1.,1.,1.,1.
		avg_time_dict = {}
		avg_time_dict['cost_outer_grad']  =[1.]
		avg_time_dict['cost_inner_grad']  =[1.]
		avg_time_dict['cost_inner_hess']  =[1.]
		avg_time_dict['cost_inner_jac']  =[1.]

	idealized_time = [b_size*(o*t1+g*t2+h*t3+j*t4) for o,g,h,j in zip(O,G,H,J) ]
	return idealized_time


def get_path(data, value_keys, exp_dir):
	path= os.path.join(exp_dir,str(data['logs_log_id']))
	return {'path':path}


def get_scalar_data( data, val_keys, mode='last'):

	if mode=='last':
		def operation(a):
			return a[-1]
	elif mode=='first':
		def operation(a):
			return a[1]
	elif mode=='min':
		def operation(a):
			return min(a)
	elif mode=='max':
		def operation(a):
			return max(a)
	else:
		raise NotImplementedError
	def safe_op(a):
		try:
			return operation(a)
		except:
			return 'Not existing'

	return {val_key: safe_op( data[val_key]) for val_key in val_keys}






def compute_mean_and_std(data_list):
	index = None # mean and std does not result an index unlike min and max.
	if len(data_list)==1:
		out = {key:value for key,value in data_list[0]}
		out.update({'std_'+key: np.zeros(value.size) for key,value in data_list[0]})
		return out,index
	keys = list(data_list[0].keys())
	out = {}
	for i,p in enumerate(data_list):
		for key in keys:
			if i==0:
				len_data = len(p[key])
				out[key] = np.zeros(len_data)
				out['std_'+key] = np.zeros(len_data)
			else:
				len_data = min(out[key].size,len(p[key]))

			new_array = np.asarray(p[key])[:len_data]
			out[key] = out[key][:len_data] + new_array
			out['std_'+key] = out['std_'+key][:len_data] + new_array**2

	for key in keys:
		out[key] = out[key]/(i+1)
		out['std_'+key] = out['std_'+key]/(i+1) - (out[key])**2
	return out,index


def safe_float(potential_float):
    try:
        return float(potential_float)

    except ValueError:
        return potential_float

def safe_argmin(data,val_key):
    index = -1
    a = data[val_key[0]]#eval_hkey(val_key,data) 
    try:
        index = np.nanargmin(np.asarray(a))
        return a[index],index
    except:
        return a[index], index
def safe_argmax(data,val_key):
    index = -1
    a = data[val_key[0]]#eval_hkey(val_key,data)
    try:
        index = np.nanargmax(np.asarray(a))
        return a[index],index
    except:
        return a[index], index





