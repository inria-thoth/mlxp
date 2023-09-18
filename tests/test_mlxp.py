



import pathlib
import runpy
import os
import sys
import pytest


scripts = pathlib.Path('test_examples').resolve().glob('*.py')


@pytest.mark.parametrize('script', scripts)
def test_usage(script):

    parent_path = str(script.parent)
    sys.path.insert(0,parent_path)
    runpy.run_path(str(script),run_name='__main__')


