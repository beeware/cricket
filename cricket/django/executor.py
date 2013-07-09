from __future__ import absolute_import

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
from django.test.utils import get_runner

from cricket.pipes import PipedTestRunner

# Dynamically retrieve the test runner class for this project.
TestRunnerClass = get_runner(settings, None)


# class TestDatabaseSetup(TestRunnerClass):
#     """A Django test runner that sets up the test databases.

#     Doesn't actually run any of the tests.

#     TODO: Actually use this.
#     """
#     def run_tests(self, test_labels, extra_tests=None, **kwargs):
#         old_config = self.setup_databases()
#         return 0


class TestExecutor(TestRunnerClass):
    """A Django test runner that runs the test suite.

    Formats output in a machine-readable format.
    """
    def run_suite(self, suite, **kwargs):
        # Django 1.6 introduce the new-style test runner.
        # If that test runner is in use, we use the full test name.
        # If we're still using a pre 1.6-style runner, we need to
        # drop out all everything between the app name and the test module.
        use_old_discovery = issubclass(TestRunnerClass, DjangoTestSuiteRunner)
        return PipedTestRunner(use_old_discovery=use_old_discovery).run(suite)

    # def run_tests(self, test_labels, extra_tests=None, **kwargs):
    #     """Run the test in the test suite.

    #     Returns the number of tests that failed.
    #     """
    #     try:
    #         config_json = raw_input()
    #         print 'CONFIG', config_json
    #         db_mappings, mirrors = json.loads(config_json)

    #         for alias in connections:
    #             connection = connections[alias]
    #             if connection.settings_dict['NAME'] in db_mappings:
    #                 connection.settings_dict['NAME'] = db_mappings[connection.settings_dict['NAME']][0]

    #         for alias, mirror_alias in mirrors.items():
    #             connections[alias].settings_dict['NAME'] = (
    #                 connections[mirror_alias].settings_dict['NAME'])

    #     except ValueError:
    #         print 'VALUE ERROR'

    #         old_config, mirrors = self.setup_databases()
    #         db_mappings = dict(
    #             (old_name, (connection.settings_dict['NAME'], destroy))
    #             for connection, old_name, destroy in old_config
    #         )
    #         print json.dumps([db_mappings, mirrors])

    #     self.setup_test_environment()
    #     suite = self.build_suite(test_labels, extra_tests)
    #     result = PipedTestRunner().run(suite)
    #     self.teardown_test_environment()
    #     return self.suite_result(suite, result)


# class TestDatabaseTeardown(TestRunnerClass):
#     """A Django test runner that tears down the test databases.

#     Doesn't actually run any of the tests.

#     TODO: Actually use this.
#     """
#     def run_tests(self, test_labels, extra_tests=None, **kwargs):
#         self.teardown_databases(old_config)
#         return 0
