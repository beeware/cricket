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


START_SYMBOL = '\x02'  # <--- Start of test outputs but not first line
SEP_SYMBOL = '\x1f'  # <--- Separator
END_SYMBOL = '\x03'  # <--- Last blank line

class WellFormedResult:
    '''
    A class which renders to:

    {   "path": "auth.AnonymousUserBackendTest.test_get_all_permissions", 
        "start_time": 1373247333.570757
    }
    {
        "status": "OK", 
        "output": "", 
        "end_time": 1373247333.570895, 
        "description": "No description"
    }
    <SEP_SYMBOL>
    '''

    def __init__(self, **params):
        '''
        We know how to handle:
            -- alias
            -- path
            -- magicdots
            -- status
        '''

        # Fail gracefully-ish
        self.params = defaultdict('not recorded')
        
        for item in params:
            self.params = params[item]

    def __str__(self):

        part1_str = {'path': self.params['path'], 
                     'start_time': self.params['start_time']
                    }

        part2_str = {
            'status': self.params['status'],
            'output': self.params['output'],
            'end_time': self.params['end_time'],
            'description': self.params['description']
        }

        valuestr = '\n'.join([part1_str, part2_str, SEP_SYMBOL])

        return valuestr



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
        1.) Execute the call to py.test
        2.) Scrape the output
        3.) Stream a sequence of well-formed outputs
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

    PTE = PyTestExecutor()
    PTE.stream_results()