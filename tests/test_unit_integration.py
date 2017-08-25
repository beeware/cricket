import subprocess
import unittest

import cricket

from cricket.unittest import discoverer
from cricket.unittest import executor
from cricket.unittest.model import UnittestProject
from cricket.executor import Executor
from cricket.model import TestMethod

class TestTestsCoverage(unittest.TestCase):

    def setUp(self):
        super(TestTestsCoverage, self).setUp()
        self.project = UnittestProject()
        self.project.refresh([
            'tests.test_unit_integration.TestCollection.test_testCollection',
            'tests.test_unit_integration.TestExecutorCmdLine.test_labels',
            'tests.test_unit_integration.TestTestsCoverage.test_run_methods_tests_in_different_tests_cases',
            'tests.test_unit_integration.TestStubToTestCoverage.test_stub1',
            'tests.test_unit_integration.TestStubToTestCoverage.test_stub2',
            'tests.test_unit_integration.TestStubToTestCoverage.test_stub3',
        ])

        self.labels = [
            'tests.test_unit_integration.TestCollection.test_testCollection',
            'tests.test_unit_integration.TestStubToTestCoverage.test_stub1',
            'tests.test_unit_integration.TestStubToTestCoverage.test_stub2',
            'tests.test_unit_integration.TestStubToTestCoverage.test_stub3',
        ]

    def test_run_methods_tests_in_different_tests_cases(self):
        '''
        Test coverage in a test module, selecting test methods from different tests cases (but not all tests cases from a test module)
        '''

        count, new_labels = self.project.find_tests(True, None, self.labels)
        self.executor = Executor(self.project, count, new_labels)
        self.executor.poll()
        self.assertEquals(
            self.executor.result_count.get(TestMethod.STATUS_PASS, 0), 4)

class TestStubToTestCoverage(unittest.TestCase):

    def test_stub1(self):
        self.assertTrue(True)

    def test_stub2(self):
        self.assertTrue(True)

    def test_stub3(self):
        self.assertTrue(True)

class TestCollection(unittest.TestCase):

    def test_testCollection(self):
        '''
        Confirm that the pytest discovery mechanism is capable of
        finding this test
        '''

        PTD = discoverer.PyTestDiscoverer()
        PTD.collect_tests()
        tests = str(PTD).split('\n')

        test_found = False
        for test in tests:
            test_found |= 'test_testCollection' in test
        self.assertTrue(test_found)


class TestExecutorCmdLine(unittest.TestCase):

    def test_labels(self):
        '''
        Test that the command-line API is respecting the labels
        being targetted for testing
        '''

        labels = ['tests.test_unit_integration.TestCollection']
        cmdline = ['python', '-m', 'cricket.unittest.executor'] + labels

        runner = subprocess.Popen(
            cmdline,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        output = ''
        for line in runner.stdout:
            output += line.decode('utf-8')

        self.assertIn('tests.test_unit_integration.TestCollection',
                       output)
        self.assertNotIn('tests.test_unit_integration.TestExecutorCmdLine',
                          output)




# This is a magic test which can be un-commented and run manually.
# It recursively calls the text executor, and fouls up normal
# output, so it had to be disabled as I am not smart enough
# to actually understand and fix the issue

# class TestExecutor(unittest.TestCase):

#     def test_suite_execution(self):
#         '''
#         Note, it's hard to test full suite discovery because
#         it will include this test and infinite loop. So just
#         testing on a single test until I can figure out something
#         smarter.
#         '''

#         run_only = [
#             'tests.test_unit_integration.TestDiscoverer'
#         ]

#         PTE = test_executor.PyTestExecutor()
#         PTE.run_only(run_only)
#         PTE.stream_results()

if __name__ == '__main__':
    unittest.main()
