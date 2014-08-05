'''
This is a thing which, when run, produces a stream
of well-formed test result outputs. Its processing is
initiated by the top-level Executor class.

Its main API is the command line, but it's just as sensible to
call into it. See __main__ for usage
'''

import argparse
import unittest

try:
    from coverage import coverage
except ImportError:
    coverage = None

from cricket import pipes


class PyTestExecutor(object):
    '''
    This is a thing which, when run, produces a stream
    of well-formed test result outputs. Its processing is
    initiated by the top-level Executor class
    '''

    def __init__(self, start='.', pattern='test*.py', top=None, test_names=None):
        self.start = start
        self.pattern = pattern
        self.top = top
        self.test_names = test_names

    def load_suite(self):
        # Use explicit test_names if provided, other wise fall back to
        # discovery equivalent to the discoverer.
        loader = unittest.TestLoader()
        if self.test_names:
            suite = unittest.TestSuite()
            for name in self.test_names:
                suite.addTest(loader.loadTestsFromName(name))
        else:
            suite = loader.discover(self.start, self.pattern, self.top)
        return suite

    def stream_suite(self, suite):
        pipes.PipedTestRunner().run(suite)

    def stream_results(self):
        '''
        1.) Discover all tests if necessary
        2.) Otherwise fetch specific tests
        3.) Execute-and-stream
        '''
        suite = self.load_suite()
        self.stream_suite(suite)


class PyTestCoverageExecutor(PyTestExecutor):
    '''
    A version of PyTestExecutor that gathers coverage data.
    '''
    def stream_suite(self, suite):
        cov = coverage()
        cov.start()
        super(PyTestCoverageExecutor, self).stream_suite(suite)
        cov.stop()
        cov.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--coverage", help="Generate coverage data for the test run", action="store_true")
    parser.add_argument('-t', '--test-names', action='store_true',
        help='Interpret arguments as test names.')
    parser.add_argument('labels', nargs=argparse.REMAINDER,
        help='Test labels to run.')

    options = parser.parse_args()
    options.start = '.'
    options.pattern = 'test*.py'
    options.top = None

    if options.coverage:
        cls = PyTestCoverageExecutor
    else:
        cls = PyTestExecutor

    if options.test_names:
        executor = cls(test_names=options.labels)
    else:
        for name, value in zip(('start', 'pattern', 'top'), options.labels):
            setattr(options, name, value)
        executor = cls(options.start, options.pattern, options.top)

    executor.stream_results()
