from cricket.model import Project

class PyTestProject(Project):

    def discover_commandline(self):
        "Command line: Discover all available tests in a project."
        return ['py.test', 'tests', '--collectonly']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        return ['py.test', '-k',] + labels