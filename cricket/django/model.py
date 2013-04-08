from cricket.model import Project


class DjangoProject(Project):

    def discover_commandline(self):
        "Command lineDiscover all available tests in a project."
        return ['python', 'manage.py', 'test', '--testrunner=cricket.django.runners.TestDiscoverer']

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        return ['python', 'manage.py', 'test', '--testrunner=cricket.django.runners.TestExecutor', '--noinput'] + labels
