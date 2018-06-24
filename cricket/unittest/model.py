import sys

from cricket.model import TestSuite, TestModule, TestCase, TestMethod


class UnittestTestSuite(TestSuite):
    def __init__(self, options=None):
        super(UnittestTestSuite, self).__init__()

    def discover_commandline(self):
        "Command line: Discover all available tests in a project."
        return [sys.executable, '-m', 'cricket.unittest.discoverer']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        args = [sys.executable, '-m', 'cricket.unittest.executor']
        if self.coverage:
            args.append('--coverage')
        if labels is None:
            return args
        return args + labels

    def split_test_id(self, test_id):
        pathparts = test_id.split('.')

        return [
            (TestModule, part)
            for part in pathparts[:-2]
        ] + [
            (TestCase, pathparts[-2]),
            (TestMethod, pathparts[-1]),
        ]

    def join_path(self, parent, klass, part):
        if parent.path is None:
            return part
        else:
            return '{}.{}'.format(parent.path, part)
