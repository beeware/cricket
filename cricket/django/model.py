'''
In general, you would expect that there would only be one project class
specified in this file. It provides the interface to executing test
collecetion and execution.
'''

from cricket.model import Project


class DjangoProject(Project):
    '''
    The Project is a wrapper around the command-line calls to interface
    to test collection and test execution
    '''

    def discover_commandline(self):
        "Command lineDiscover all available tests in a project."
        return ['python', 'manage.py', 'test', '--testrunner=cricket.django.discoverer.TestDiscoverer']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        return ['python', 'manage.py', 'test', '--testrunner=cricket.django.executor.TestExecutor', '--noinput'] + labels
