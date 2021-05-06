from setuptools import setup, find_packages


setup(name='Experimentalist',
      version='0.1',
      description='ml exp ',
      url='git@github.com:MichaelArbel/Experimentalist.git',
      author='Michael Arbel',
      author_email='michael.n.arbel@gmail.com',
      license='BSD3',
      packages=find_packages('.', exclude=["*tests*", "*.develop"]),
      zip_safe=False)