import csv
import sys
import os
import time
from datetime import datetime
import pprint
import socket
import json
import pickle as pkl
from torch.autograd import Variable
import pdb







class Config(object):
	def __init__(self):




    def get_host_config(self):
    	host_config = {'hostname':   socket.gethostname(),
    					'process_id': os.getpid(),
    					}

    	return host_config