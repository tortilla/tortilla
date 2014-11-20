# -*- coding: utf-8 -*-

from setuptools import setup
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='tortilla',
    version='0.1.0.dev1',
    description='A tiny library for creating wrappers around external APIs',
    long_description=long_description,
    url='https://github.com/redodo/tortilla',
    author='Hidde Bultsma',
    author_email='dodo@gododo.co',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
    ],
    keywords='api wrapper',
    packages=['tortilla'],
    install_requires=[
        'bunch',
        'colorclass',
        'requests',
    ],
)
