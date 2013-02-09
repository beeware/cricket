from django.test.simple import DjangoTestSuiteRunner

from cricket.pipes import PipedTestRunner


class TestDiscoverer(DjangoTestSuiteRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """A test runner that prints out all the test that will be run.

        Doesn't actually run any of the tests.
        """
        for test in self.build_suite([]):
            parts = test.id().split('.')
            tests_index = parts.index('tests')

            print '%s.%s.%s' % (parts[tests_index - 1], parts[-2], parts[-1])

        return 0


class TestDatabaseSetup(DjangoTestSuiteRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Set up the test databases.

        Doesn't actually run any of the tests.

        TODO: Make this actually work :-)
        """
        old_config = self.setup_databases()
        return 0


class TestExecutor(DjangoTestSuiteRunner):
    def run_suite(self, suite, **kwargs):
        return PipedTestRunner().run(suite)

    # def run_tests(self, test_labels, extra_tests=None, **kwargs):
    #     """Run the test in the test suite.

    #     Returns the number of tests that failed.
    #     """
    #     self.setup_test_environment()
    #     suite = self.build_suite(test_labels, extra_tests)
    #     result = PipedTestRunner().run(suite)
    #     self.teardown_test_environment()
    #     return self.suite_result(suite, result)


class TestDatabaseTeardown(DjangoTestSuiteRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Tear down the test databases.

        Doesn't actually run any of the tests.

        TODO: Make this actually work :-)
        """
        self.teardown_databases(old_config)
        return 0
