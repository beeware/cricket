import os
import sys

from cricket.model import TestSuite, TestModule, TestCase, TestMethod


class PyTestTestSuite(TestSuite):
    def __init__(self, options=None):
        super(PyTestTestSuite, self).__init__()

    def discover_commandline(self):
        "Command line: Discover all available tests in a project."
        return ['pytest', '--cricket', 'discover']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        args = ['pytest', '--cricket', 'execute']
        # if self.coverage:
        #     args.append('--coverage')
        if labels is None:
            return args
        return args + labels

    def split_test_id(self, test_id):
        dirparts = test_id.split(os.sep)
        pathparts = dirparts[-1].split('::')

        parts = [
            (TestModule, dirpart)
            for dirpart in dirparts[:-1]
        ]

        if len(pathparts) == 2:
            parts.extend([
                (TestModule, pathparts[0]),
                (TestMethod, pathparts[1]),
            ])
        elif len(pathparts) == 3:
            parts.extend([
                (TestModule, pathparts[0]),
                (TestCase, pathparts[1]),
                (TestMethod, pathparts[2]),
            ])
        else:
            raise Exception("Don't know how to handle test with {} parts.".format(len(pathparts)))

        return parts

    def join_path(self, parent, klass, part):
        if parent.path is None:
            return part
        else:
            if klass == TestModule:
                join_char = os.sep
            else:
                join_char = '::'

            return '{}{}{}'.format(parent.path, join_char, part)
