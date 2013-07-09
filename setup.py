#/usr/bin/env python
import sys

from setuptools import setup
from cricket import VERSION

try:
    readme = open('README.rst')
    long_description = str(readme.read())
finally:
    readme.close()

required_pkgs = []
if sys.version_info < (2, 7):
    required_pkgs.append('argparse')

setup(
    name='cricket',
    version=VERSION,
    description='A graphical tool to assist running test suites.',
    long_description=long_description,
    author='Russell Keith-Magee',
    author_email='russell@keith-magee.com',
    url='http://github.com/freakboy3742/cricket',
    packages=[
        'cricket',
        'cricket.django',
        'cricket.unittest',
    ],
    install_requires=required_pkgs,
    license='New BSD',
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
    test_suite='tests'
)
