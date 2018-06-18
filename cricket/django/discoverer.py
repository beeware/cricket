import unittest

from django.conf import settings
from django.test.utils import get_runner

# Dynamically retrieve the test runner class for this project.
TestRunnerClass = get_runner(settings, None)


class TestDiscoverer(TestRunnerClass):
    """A Django test runner that prints out all the test that will be run.

    Doesn't actually run any of the tests.
    """
    def _output_suite(self, suite):
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                self._output_suite(test)
            else:
                print(test.id())

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        self._output_suite(self.build_suite(test_labels))
        return 0
