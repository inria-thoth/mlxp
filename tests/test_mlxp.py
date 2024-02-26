



import pathlib
import runpy
import os
import sys
import pytest
import subprocess


scripts = pathlib.Path('.').resolve().glob('launch_script*')

@pytest.mark.parametrize('script', scripts)
def test_launching(script):

    parent_path = str(script.parent)
    sys.path.insert(0,parent_path)

    with open(script, 'rb') as file:
        script_code = file.read()
    rc = subprocess.call(script_code, shell=True)

    assert rc==0




scripts = pathlib.Path('.').resolve().glob('mlxpsub_launch_script.sh')

@pytest.mark.parametrize('script', scripts)
def test_mlxpsub_launching(script):

    parent_path = str(script.parent)
    sys.path.insert(0,parent_path)

    script_name = os.path.join(parent_path,script.name)
    rc = subprocess.call(f"chmod u+x {script_name}"  , shell=True)
    process = subprocess.Popen([script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    rc = process.wait()
    output, error = process.communicate()

    assert rc==0
    ignore = "Use of uninitialized value" in error or "mlxp.errors.JobSubmissionError" in error
    if not ignore:
        assert not error




scripts = pathlib.Path('.').resolve().glob('read_script*')

@pytest.mark.parametrize('script', scripts)
def test_reading(script):

    parent_path = str(script.parent)
    sys.path.insert(0,parent_path)

    with open(script, 'rb') as file:
        script_code = file.read()
    rc = subprocess.call(script_code, shell=True)
    assert rc==0
    