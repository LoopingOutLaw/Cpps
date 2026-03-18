from setuptools import find_packages
from setuptools import setup

setup(
    name='dexter_utils',
    version='0.0.0',
    packages=find_packages(
        include=('dexter_utils', 'dexter_utils.*')),
)
