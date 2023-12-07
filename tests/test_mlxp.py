



import pathlib
import runpy
import os
import sys
import pytest
import subprocess


scripts = pathlib.Path('.').resolve().glob('script.sh')

@pytest.mark.parametrize('script', scripts)
def test_launching(script):

    parent_path = str(script.parent)
    sys.path.insert(0,parent_path)

    with open(script, 'rb') as file:
        script_code = file.read()
    rc = subprocess.call(script_code, shell=True)
    assert rc==0

