import os

import yaml


class _bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def _printc(color, text):
    print(color + text + _bcolors.ENDC)


class InteractiveModeHandler:
    def __init__(self, mode: bool, im_choices_file: str = "./vm_choices.yaml"):
        self._interactive_mode = mode
        self._im_choices_file = im_choices_file
        self.im_choices = {}
        if os.path.isfile(self._im_choices_file):
            with open(self._im_choices_file, "r") as file:
                self.im_choices = yaml.safe_load(file)

    @property
    def interactive_mode(self):
        return self._interactive_mode

    def save_im_choice(self):
        # if self._interactive_mode:
        with open(self._im_choices_file, "w") as f:
            yaml.dump(self.im_choices, f)

    def get_im_choice(self, choice_key):
        if choice_key in self.im_choices:
            return self.im_choices[choice_key]
        else:
            return None

    def set_im_choice(self, choice_key, choice_value):
        self.im_choices[choice_key] = choice_value
