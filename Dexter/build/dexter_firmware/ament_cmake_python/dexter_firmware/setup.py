from setuptools import find_packages
from setuptools import setup

setup(
    name='dexter_firmware',
    version='0.0.0',
    packages=find_packages(
        include=('dexter_firmware', 'dexter_firmware.*')),
)
