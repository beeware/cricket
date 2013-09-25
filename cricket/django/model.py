'''
In general, you would expect that there would only be one project class
specified in this file. It provides the interface to executing test
collecetion and execution.
'''
import os
import sys

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

    @property
    def script(self):
        if os.path.exists(os.path.join(os.getcwd(), 'manage.py')):
            # We're running the test suite on a normal Django project
            script = ['manage.py', 'test', '--noinput']
        elif os.path.exists(os.path.join(os.getcwd(), 'runtests.py')):
            # We're running Django's own test script
            script = [os.path.join(os.path.dirname(__file__), 'django_runtests.py')]
            os.environ['PYTHONPATH'] = os.getcwd()
            if self.settings is None:
                self.settings = 'test_sqlite'
        else:
            raise Exception("Can't find a Django test suite to execute.")
        return script

    def discover_commandline(self):
        "Command lineDiscover all available tests in a project."

        command = [sys.executable] + self.script

        if self.settings:
            command.append('--settings={0}'.format(self.settings))

        command.append('--testrunner=cricket.django.discoverer.TestDiscoverer')

        return command

    def execute_commandline(self, labels):
        "Return the command line to execute the specified test labels"
        command = [sys.executable] + self.script

        if self.settings:
            command.append('--settings={0}'.format(self.settings))

        if self.coverage:
            command.append('--testrunner=cricket.django.executor.TestCoverageExecutor')
        else:
            command.append('--testrunner=cricket.django.executor.TestExecutor')
        command.extend(labels)

        return command
