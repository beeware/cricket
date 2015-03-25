# This is for backwards compatibility with Python version < 2.7 only
# for Python 2.7 and 3.x the default unittest is the correct package
# to use. unittest2 is a backport of this package to be used in
# versions < 2.7.
# Use
#       from cricket.compat import unittest
#
# to make versions work with all version of Python. This will be slowly
# deprecated in the future as Python < 2.7 becomes more and mor
# obsolete.
from __future__ import absolute_import
import unittest  # NOQA
if not hasattr(unittest.TestCase, 'assertIsNotNone'):
    import unittest2 as unittest  # NOQA
