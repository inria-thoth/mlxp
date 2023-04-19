from setuptools import setup, find_packages
import os

setup(
    name="experimentalist",
    version="0.1",
    description="A framework for conducting machine learning experiments in python",
    long_description=open(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md")
    ).read(),
    long_description_content_type="text/markdown",
    url="git@github.com:MichaelArbel/experimentalist.git",
    author="Michael Arbel",
    author_email="michael.n.arbel@gmail.com",
    license="BSD3",
    packages=find_packages(".", exclude=["*tests*", "*.develop"]),
    install_requires=["hydra-core", 
                      "omegaconf", 
                      "dill",
                      "GitPython",
                      "numpy",
                      "pandas",
                      "ply",
                      "PyYAML",
                      "tinydb"],
    zip_safe=False,
)
