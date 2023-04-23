from enum import Enum

class bcolors(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'




def printc(color, text):
    print(color.value +text+ bcolors.ENDC.value)


def inputc(color, text):
    input(color.value + text + bcolors.ENDC.value)