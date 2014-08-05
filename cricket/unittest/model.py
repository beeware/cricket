import sys

from cricket.model import Project
import cricket.unittest.options


class UnittestProject(Project):

    def __init__(self, options=None):
        self.start = getattr(options, 'start', '.')
        self.pattern = getattr(options, 'pattern', 'test*py')
        self.top = getattr(options, 'top', None)
        super(UnittestProject, self).__init__()

    @classmethod
    def add_arguments(cls, parser):
        cricket.unittest.options.add_arguments(parser)

    def discover_commandline(self):
        "Command line: Discover all available tests in a project."
        args = [sys.executable, '-m', 'cricket.unittest.discoverer',
                self.start, self.pattern]
        if self.top is not None:
            args.append(self.top)
        return args

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        args = [sys.executable, '-m', 'cricket.unittest.executor']
        if self.coverage:
            args.append('--coverage')
        if labels:
            args.extend(['-t'] + labels)
        else:
            args.extend([self.start, self.pattern])
            if self.top is not None:
                args.append(self.top)
        return args
