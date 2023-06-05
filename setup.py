from setuptools import setup, find_packages
import os

ver_dic = {}
exec(
    compile(
        open("mlxp/__init__.py").read(), "mlxp/__init__.py", "exec"
    ),
    ver_dic,
)




setup(
    name=ver_dic["PROJECT"],
    version=ver_dic["VERSION_TEXT"],
    description="A framework for conducting machine learning experiments in python",
    long_description=open(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.rst")
    ).read(),
    long_description_content_type="text/x-rst",
    url=ver_dic["URL"],
    author=ver_dic["AUTHOR"],
    author_email=ver_dic["AUTHOR_EMAIL"],
    license=ver_dic["LICENSE"],
    packages=find_packages(".", exclude=["*tests*", "*.develop"]),
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
