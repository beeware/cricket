'''
This is a thing which, when run, produces a stream
of well-formed test result outputs. Its processing is
initiated by the top-level Executor class.

Its main API is the command line, but it's just as sensible to
call into it. See __main__ for usage
'''

from cricket import pipes
import subprocess
import sys
import unittest

from cricket.pipes import PipedTestRunner

class PyTestExecutor:
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


if __name__ == '__main__':

    run_only = None
    if len(sys.argv) > 1:
        run_only = sys.argv[1:]

    PTE = PyTestExecutor()

    if run_only:
        PTE.run_only(run_only)
    PTE.stream_results()