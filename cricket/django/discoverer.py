from __future__ import absolute_import

from unittest import TestSuite

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
        def walk_suite(suite):
            for test in suite:
                if isinstance(test, TestSuite):
                    walk_suite(test)
                    continue
                # Django 1.6 introduce the new-style test runner.
                # If that test runner is in use, we use the full test name.
                # If we're still using a pre 1.6-style runner, we need to
                # drop out all everything between the app name and the test module.
                test_id = test.id()
                if issubclass(TestRunnerClass, DjangoTestSuiteRunner) and 'tests' in test_id:
                    parts = test_id.split('.')
                    tests_index = parts.index('tests')
                    print '%s.%s.%s' % (parts[tests_index - 1], parts[-2], parts[-1])
                else:
                   print test.id()

        walk_suite(self.build_suite(test_labels))

        return 0
