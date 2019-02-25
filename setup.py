from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='PyFFF',
    version='0.1.0'
    description='Python For Filesystem Forensics',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://gitlab.com/xinhuang/pyfff',
    author='Xin Huang',
    author_email='xinhuang@protomail.com',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['tabulate', 'hexdump'],
    extras_require={
        'dev': [],
        'test': [],
    },
)
