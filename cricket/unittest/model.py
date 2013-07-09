from cricket.model import Project

class PyTestProject(Project):

    def discover_commandline(self):
        "Command line: Discover all available tests in a project."
        return ['python', '-m', 'cricket.unittest.discoverer']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        return ['python', '-m', 'cricket.unittest.executor'] + labels