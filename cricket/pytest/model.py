import sys

from cricket.model import TestSuite


class PyTestTestSuite(TestSuite):

    def __init__(self, options=None):
        super(UnittestTestSuite, self).__init__()

    def discover_commandline(self):
        "Command line: Discover all available tests in a project."
        return ['pytest', '--cricket-mode', 'discover']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        return ['pytest', '--cricket-mode', 'execute']
        # if self.coverage:
        #     args.append('--coverage')
        return args + labels
