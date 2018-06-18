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


class UnittestExecutor:
    '''
    This is a thing which, when run, produces a stream
    of well-formed test result outputs. Its processing is
    initiated by the top-level Executor class
    '''

    def __init__(self):

        # Allows the executor to run a specified list of tests
        self.specified_list = None

    def run_only(self, specified_list):
        self.specified_list = specified_list

    def stream_suite(self, suite):
        pipes.PipedTestRunner().run(suite)

    def stream_results(self):
        '''
        1.) Discover all tests if necessary
        2.) Otherwise fetch specific tests
        3.) Execute-and-stream
        '''

        loader = unittest.TestLoader()

        if not self.specified_list:
            suite = loader.discover('.')
            self.stream_suite(suite)
        else:
            for module in self.specified_list:
                suite = loader.loadTestsFromName(module)
                self.stream_suite(suite)


class UnittestCoverageExecutor(UnittestExecutor):
    '''
    A version of UnittestExecutor that gathers coverage data.
    '''
    def stream_suite(self, suite):
        cov = coverage()
        cov.start()
        super(UnittestCoverageExecutor, self).stream_suite(suite)
        cov.stop()
        cov.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--coverage", help="Generate coverage data for the test run", action="store_true")
    parser.add_argument(
        'labels', nargs=argparse.REMAINDER,
        help='Test labels to run.'
    )

    options = parser.parse_args()

    if options.coverage:
        executor = UnittestCoverageExecutor()
    else:
        executor = UnittestExecutor()

    if options.labels:
        executor.run_only(options.labels)
    executor.stream_results()
