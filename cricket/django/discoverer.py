from __future__ import absolute_import

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
from django.test.utils import get_runner

# Dynamically retrieve the test runner class for this project.
TestRunnerClass = get_runner(settings, None)


class TestDiscoverer(TestRunnerClass):
    """A Django test runner that prints out all the test that will be run.

    Doesn't actually run any of the tests.
    """
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        for test in self.build_suite([]):
            # Django 1.6 introduce the new-style test runner.
            # If that test runner is in use, we use the full test name.
            # If we're still using a pre 1.6-style runner, we need to
            # drop out all everything between the app name and the test module.
            if issubclass(TestRunnerClass, DjangoTestSuiteRunner):
                parts = test.id().split('.')
                tests_index = parts.index('tests')
                print '%s.%s.%s' % (parts[tests_index - 1], parts[-2], parts[-1])
            else:
                print test.id()

        return 0
