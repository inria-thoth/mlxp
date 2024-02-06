from setuptools import setup, find_packages
import os

project_info = {}
exec(
    compile(
        open("project_info.py").read(), "project_info.py", "exec"
    ),
    project_info,
)


with open('VERSION') as version_file:
    version = version_file.read().strip()


setup(
    name=project_info["PROJECT"],
    version=version,
    description="A framework for conducting machine learning experiments in python",
    long_description=open(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.rst")
    ).read(),
    long_description_content_type="text/x-rst",
    url=project_info["URL"],
    author=project_info["AUTHOR"],
    author_email=project_info["AUTHOR_EMAIL"],
    license=project_info["LICENSE"],
    packages=find_packages(".", exclude=["*tests*", "*.develop"]),
    entry_points={
        'console_scripts': [
            'mlxpsub=mlxp.mlxpsub:__main__',
        ],
    },
    install_requires=["hydra-core>=1.3.2", 
                      "omegaconf>=2.2.3", 
                      "dill>=0.3.6",
                      "GitPython>=3.1.31",
                      "pandas>=1.3.4",
                      "ply>=3.11",
                      "PyYAML>=6.0",
                      "tinydb>=4.7.1"],
    python_requires='>=3.8', 
    zip_safe=False,
    classifiers=[
    'Programming Language :: Python :: 3.8',
    ]
)
