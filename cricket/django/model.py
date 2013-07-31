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

    def __init__(self, options=None):
        self.settings = None
        if options and hasattr(options, 'settings'):
            self.settings = options.settings
        super(DjangoProject, self).__init__()

    @classmethod
    def add_arguments(cls, parser):
        """Add Django-specific settings to the argument parser.
        """
        settings_help = ("The Python path to a settings module, e.g. "
                         "\"myproject.settings.main\". If this isn't provided, the "
                         "DJANGO_SETTINGS_MODULE environment variable will be "
                         "used.")
        parser.add_argument('--settings', help=settings_help)

    def discover_commandline(self):
        "Command lineDiscover all available tests in a project."
        command = ['python', 'manage.py', 'test',
                   '--testrunner=cricket.django.discoverer.TestDiscoverer']
        if self.settings:
            command.append('--settings={0}'.format(self.settings))
        return command

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        command = ['python', 'manage.py', 'test',
                   '--testrunner=cricket.django.executor.TestExecutor',
                   '--noinput'] + labels
        if self.settings:
            command.append('--settings={0}'.format(self.settings))
        return command
