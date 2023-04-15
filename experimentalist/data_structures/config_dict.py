import omegaconf
from typing import Dict, Any
from datetime import datetime
import socket
import os
import yaml

class ConfigDict(dict):
    def __init__(self, *args, **kwargs):
        super(ConfigDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
       
    def __repr__(self):
        # Define custom string representation for ConfigDict objects
        return f'{yaml.dump(convert_dict(self,src_class=ConfigDict,dst_class=dict))}'
    def to_dict(self):
        return convert_dict(self,src_class=ConfigDict,dst_class=dict)

    def update_dict(self,new_dict: Dict[str,Any])->None:
        new_dict = convert_dict(new_dict, src_class=dict)
        for key, value in new_dict.items():
            if key in self.keys():
                if isinstance(value, dict):
                    if isinstance(self[key], ConfigDict):
                        self[key].update_dict(value)
                    else:
                        self[key] = convert_dict(value,src_class=dict)
                else: 
                    self[key] = value
            else:
                if isinstance(value, dict):
                    self[key] = convert_dict(value,src_class=dict)
                else:
                    self[key] = value



    def set_starting_run_info(self):
        now = datetime.now()
        date = now.strftime("%d/%m/%Y")
        time = now.strftime("%H:%M:%S")
        info = {'hostname': socket.gethostname(),
        'process_id': os.getpid(),
        'start_date':date,
        'start_time':time}
        self.update_dict({'run_info':info})


def convert_dict(config: Any, src_class=omegaconf.dictconfig.DictConfig, dst_class=ConfigDict)-> Any:
    """
    Converts an instance of the class omegaconf.dictconfig.DictConfig
    to a dictionary
    
    :param config: The metadata for the run in immutable form
    :type config: omegaconf.dictconfig.DictConfig
    :rtype: Dict[str, Any]
    :return: The metadata for the run in mutable form
    """


    done = False
    out_dict = {}
    for key, value in config.items():
        if isinstance(value, src_class):
            out_dict[key] = convert_dict(value, 
                                src_class=src_class,
                                dst_class=dst_class)
        else:
            if isinstance(value, omegaconf.listconfig.ListConfig):
                value = list(value)
            out_dict[key] = value
    out_dict = dst_class(out_dict)
    return out_dict



