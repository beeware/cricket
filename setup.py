#/usr/bin/env python
import io
import re
from setuptools import setup, find_packages


with io.open('./cricket/__init__.py', encoding='utf8') as version_file:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")


with io.open('README.rst', encoding='utf8') as readme:
    long_description = readme.read()


setup(
    name='cricket',
    version=version,
    description='A graphical tool to assist running test suites.',
    long_description=long_description,
    author='Russell Keith-Magee',
    author_email='russell@keith-magee.com',
    url='http://pybee.org/cricket',
    packages=find_packages(exclude='tests'),
    py_modules=['pytest_cricket'],
    package_data={
        'cricket': ['icons/*'],
    },
    include_package_data=True,
    install_requires=[
        'toga==0.3.0.dev9',
        'setuptools>=39.1.0',
    ],
    tests_require=[
        'django~=1.11',
        'pytest>=3.6',
    ],
    python_requires='>=3.4',
    scripts=[],
    entry_points={
        'console_scripts': [
            'cricket-django = cricket.django.__main__:run',
            'cricket-unittest = cricket.unittest.__main__:run',
            'cricket-pytest = cricket.pytest.__main__:run',
        ],
        'pytest11': [
            'cricket = cricket.pytest.pytest_cricket',
        ],
    },
    license='New BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
    ],
    test_suite='tests',
    package_urls={
        'Funding': 'https://pybee.org/contributing/membership/',
        'Documentation': 'http://cricket.readthedocs.io/en/latest/',
        'Tracker': 'https://github.com/pybee/cricket/issues',
        'Source': 'https://github.com/pybee/cricket',
    },
)
