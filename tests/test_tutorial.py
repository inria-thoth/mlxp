



import pathlib
import runpy
import os
import sys
import pytest
import subprocess
import shutil

tutorial_path = os.path.join(str(pathlib.Path(os.getcwd()).parent),'tutorial')

scripts = pathlib.Path(tutorial_path).resolve().glob('launch_script.sh')

@pytest.mark.parametrize('script', scripts)
def test_launching(script):
    try:
        shutil.rmtree(os.path.join(tutorial_path,'logs'))
    except:
        pass
    parent_path = str(script.parent)
    sys.path.insert(0,parent_path)

    with open(script, 'r') as file:
        script_code = file.read()
    rc = subprocess.call([f"cd {tutorial_path}\n"+script_code] , shell=True)

    assert rc==0




scripts = pathlib.Path(tutorial_path).resolve().glob('mlxpsub_launch_script.sh')

@pytest.mark.parametrize('script', scripts)
def test_mlxpsub_launching(script):

    try:
        shutil.rmtree(os.path.join(tutorial_path,'logs'))
    except:
        pass

    parent_path = str(script.parent)
    sys.path.insert(0,parent_path)

    with open(script, 'r') as file:
        script_code = file.read()
    result = subprocess.run([f"cd {tutorial_path}\n"+script_code] , shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    error = result.stderr

    assert result.returncode==0
    ignore = "Use of uninitialized value" in error or "mlxp.errors.JobSubmissionError" in error
    if not ignore:
        assert not error
