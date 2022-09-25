import os
import numpy as np
class Map:
    def __init__(self):
        self.keys = []
        self.name = 'metadata'
    def apply(self,data):
        ### takes a dict of list where each list contains data corresponding to a config
        ### returns a list of 
        return NotImplementedError
    def make_name(self):
        return NotImplementedError


class Path(Map):
    def __init__(self,abs_path):
        self.abs_path=abs_path
        self.keys = ['metadata.logs.log_id']
        self.name= 'metadata.logs.path'
    def apply(self,data):
        id_key = self.keys[0]
        path= os.path.join(self.abs_path,str(data[id_key]))
        return {self.name:path}
        #config['flattened'][path_key]=path

class Last(Map):
    def __init__(self,key):
        self.keys=[key]
        self.name = 'metadata.'+key+'_last'
    def apply(self,data):
        key = self.keys[0]
        try:
            return {self.name:data[key][-1]}
        except:
            return {}

class AggMap:
    def __init__(self, func, value_keys, args = {},name=None ):
        self.func = func
        self.value_keys=value_keys
        self.args = args
        if not name:
            name = '_'.join(value_keys)
        self.name = name
    def apply(self,data):
        ### takes a dict of list where each list contains data corresponding to a config
        ### returns a dict of outputs
        return self.func(data,self.value_keys,**self.args)
    def make_name(self):
        return NotImplementedError

class AggMin(AggMap):
    def __init__(self,key):
        self.keys = [key]
        self.name = key+'_aggmin'
    def apply(self,data):
        index = -1
        #selected_data = data[self.keys[0]]
        selected_data = [d[self.keys[0]] for d in data]
        try:
            index = np.nanargmin(np.asarray(selected_data),axis=0)
            
        except:
            pass
        return {self.name:selected_data[index]},index
        
class AggMax(AggMap):
    def __init__(self,key):
        self.keys = [key]
        self.name = key+'_aggmax'
    def apply(self,data):
        index = -1
        #selected_data = data[self.keys[0]]
        selected_data = [d[self.keys[0]] for d in data]
        try:
            index = np.nanargmax(np.asarray(selected_data),axis=0)
            
        except:
            pass
        return {self.name:selected_data[index]},index


class AggAvgStd(AggMap):
    def __init__(self,key):
        self.keys = [key]
        self.name = key + '_avgstd'
    def apply(self,data):

        data = [{key:d[key] for key in self.keys} for d in data]
        out, _ = _compute_mean_and_std(data)
        return out, None

def _compute_mean_and_std(data_list):
    index = None # mean and std does not result an index unlike min and max.
    if len(data_list)==1:
        out = {key+'_avg':value for key,value in data_list[0].items()}
        out.update({key+'_std': np.zeros(len(value)) for key,value in data_list[0].items()})
        return out,index
    keys = list(data_list[0].keys())
    out = {}
    for i,p in enumerate(data_list):
        for key in keys:
            if i==0:
                len_data = len(p[key])
                out[key+'_avg'] = np.zeros(len_data)
                out[key+'_std'] = np.zeros(len_data)
            else:
                len_data = min(out[key+'_avg'].size,len(p[key]))

            new_array = np.asarray(p[key])[:len_data]
            out[key+'_avg'] = out[key+'_avg'][:len_data] + new_array
            out[key+'_std'] = out[key+'_std'][:len_data] + new_array**2

    for key in keys:
        out[key+'_avg'] = out[key+'_avg']/(i+1)
        out[key+'_std'] = out[key+'_std']/(i+1) - (out[key+'_avg'])**2
    return out,index     
