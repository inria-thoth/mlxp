import os
import json







class ConfigsList(object):
	def __init__(list_configs):
		self.list_configs = list_configs
	def __getitem__(self,items):
		return self.list_configs[items]
	def __add__(self,conflist):
		list_configs = self.list_configs +conflist.list_configs 
		return ConfigsList(list_configs)


	def default_operation(config_dict): 
        if config_dict:
            for p in config_dict:
                p['logs']['path'] = os.path.join(self.root_dir,str(p['logs']['log_id']),'metrics.json')
        return config_dict