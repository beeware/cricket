import sys

from cricket.model import Project


class UnittestProject(Project):

    def __init__(self, options=None):
        super(UnittestProject, self).__init__()

    def discover_commandline(self):
        "Command line: Discover all available tests in a project."
        return [sys.executable, '-m', 'cricket.unittest.discoverer']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        args = [sys.executable, '-m', 'cricket.unittest.executor']
        if self.coverage:
            args.append('--coverage')
        return args + labels
