# -*- coding: utf-8 -*-

from setuptools import setup
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='tortilla',
    version='0.4.0',
    description='A tiny library for creating wrappers around web APIs',
    long_description=long_description,
    url='https://github.com/redodo/tortilla',
    author='Hidde Bultsma',
    author_email='me@redodo.io',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet',
    ],
    keywords='api wrapper',
    packages=['tortilla'],
    install_requires=[
        'colorclass',
        'requests',
        'formats',
        'six',
    ],
)
