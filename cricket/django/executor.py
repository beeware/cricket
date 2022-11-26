from __future__ import absolute_import

try:
    from coverage import coverage
except ImportError:
    coverage = None

from django.conf import settings

try:
    from django.test.simple import DjangoTestSuiteRunner
except ImportError:
    DjangoTestSuiteRunner = None
from django.test.utils import get_runner

from cricket.pipes import PipedTestRunner

# Dynamically retrieve the test runner class for this project.
TestRunnerClass = get_runner(settings, None)


class TestExecutor(TestRunnerClass):
    """A Django test runner that runs the test suite.

    Formats output in a machine-readable format.
    """
    def run_suite(self, suite, **kwargs):
        return PipedTestRunner().run(suite)


class TestCoverageExecutor(TestExecutor):
    """A Django test runner that runs the test suite with coverage

    Formats output in a machine-readable format.
    """
    def run_suite(self, suite, **kwargs):
        cov = coverage()
        cov.start()
        result = super(TestCoverageExecutor, self).run_suite(suite, **kwargs)
        cov.stop()
        cov.save()
        return result
