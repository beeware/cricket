#!/usr/bin/env python

from distribute_setup import use_setuptools

use_setuptools()

from setuptools import setup
from cricket import VERSION

try:
    readme = open("README.rst")
    long_description = str(readme.read())
finally:
    readme.close()

setup(name="django-cricket",
    version=VERSION,
    author="Russell Keith-Magee",
    author_email="russell@keith-magee.com",
    url='http://pypi.python.org/pypi/django-cricket',
    license="New BSD",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
    ],
    platforms=["any"],
    description="A graphical tool to assist running a Django test suite.",
    long_description=long_description,
)
