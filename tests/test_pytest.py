import json
import os
import subprocess
import unittest

from cricket.pytest.model import PyTestTestSuite
from cricket.model import TestModule, TestCase, TestMethod


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.join(__file__)))
SAMPLE_DIR = os.path.join(ROOT_DIR, 'sample', 'pytest')


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(SAMPLE_DIR)

    def tearDown(self):
        os.chdir(self._cwd)

    def test_discovery(self):
        suite = PyTestTestSuite()
        runner = subprocess.run(
            suite.discover_commandline(),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        found = set()
        for line in runner.stdout.decode('utf-8').split('\n'):
            if line:
                found.add(line)

        self.assertEqual(
            found,
            {
                'test_root.py::test_at_root',
                'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
                'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
                'tests/submodule/test_more_nesting.py::test_stuff',
                'tests/submodule/test_more_nesting.py::test_things',
                'tests/submodule/test_nesting.py::test_stuff',
                'tests/submodule/test_nesting.py::test_things',
                'tests/test_outcomes.py::test_assertion_item',
                'tests/test_outcomes.py::test_error_item',
                'tests/test_outcomes.py::test_failing_item',
                'tests/test_outcomes.py::test_upassed_item',
                'tests/test_outcomes.py::test_upassed_strict_item',
                'tests/test_outcomes.py::test_xfailing_item',
                'tests/test_outcomes.py::test_passing_item',
                'tests/test_outcomes.py::test_skipped_item',
                'tests/test_unusual.py::test_item_output',
                'tests/test_unusual.py::test_slow_0',
                'tests/test_unusual.py::test_slow_1',
                'tests/test_unusual.py::test_slow_2',
                'tests/test_unusual.py::test_slow_3',
                'tests/test_unusual.py::test_slow_4',
                'tests/test_unusual.py::test_slow_5',
                'tests/test_unusual.py::test_slow_6',
                'tests/test_unusual.py::test_slow_7',
                'tests/test_unusual.py::test_slow_8',
                'tests/test_unusual.py::test_slow_9',
            }
        )


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(SAMPLE_DIR)

    def tearDown(self):
        os.chdir(self._cwd)

    def execute(self, *args):
        suite = PyTestTestSuite()
        runner = subprocess.run(
            suite.execute_commandline(list(args)),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        found = set()
        results = {}
        for line in runner.stdout.decode('utf-8').split('\n'):
            try:
                payload = json.loads(line)
                if 'path' in payload:
                    found.add(payload['path'])
                elif 'status' in payload:
                    count = results.setdefault(payload['status'], 0)
                    results[payload['status']] = count + 1
                else:
                    self.fail("Unknown payload line: '{}'".format(payload))
            except json.JSONDecodeError:
                pass

        return found, results

    def test_run_all(self):
        found, results = self.execute()

        self.assertEqual(found, {
            'test_root.py::test_at_root',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
            'tests/submodule/test_more_nesting.py::test_stuff',
            'tests/submodule/test_more_nesting.py::test_things',
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
            'tests/test_outcomes.py::test_assertion_item',
            'tests/test_outcomes.py::test_error_item',
            'tests/test_outcomes.py::test_failing_item',
            'tests/test_outcomes.py::test_upassed_item',
            'tests/test_outcomes.py::test_upassed_strict_item',
            'tests/test_outcomes.py::test_xfailing_item',
            'tests/test_outcomes.py::test_passing_item',
            'tests/test_outcomes.py::test_skipped_item',
            'tests/test_unusual.py::test_item_output',
            'tests/test_unusual.py::test_slow_0',
            'tests/test_unusual.py::test_slow_1',
            'tests/test_unusual.py::test_slow_2',
            'tests/test_unusual.py::test_slow_3',
            'tests/test_unusual.py::test_slow_4',
            'tests/test_unusual.py::test_slow_5',
            'tests/test_unusual.py::test_slow_6',
            'tests/test_unusual.py::test_slow_7',
            'tests/test_unusual.py::test_slow_8',
            'tests/test_unusual.py::test_slow_9',
        })

        self.assertEqual(results, {'OK': 20, 'F': 2, 'E': 1, 'x': 1, 'u': 1, 's': 1})

    def test_single_test_method(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py::test_stuff',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
        })

        self.assertEqual(results, {'OK': 1})


    def test_multiple_test_methods(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_module(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_submodules(self):
        found, results = self.execute(
            'tests/submodule',
        )

        self.assertEqual(found, {
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
            'tests/submodule/test_more_nesting.py::test_stuff',
            'tests/submodule/test_more_nesting.py::test_things',
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 6})

    def test_single_root_test_method(self):
        found, results = self.execute(
            'test_root.py::test_at_root',
        )

        self.assertEqual(found, {
            'test_root.py::test_at_root',
        })

        self.assertEqual(results, {'OK': 1})

    def test_single_root_test_method(self):
        found, results = self.execute(
            'test_root.py',
        )

        self.assertEqual(found, {
            'test_root.py::test_at_root',
        })

        self.assertEqual(results, {'OK': 1})

    # PyTest doesn't filter test naming overlaps.
    # This is (arguably) a bug in PyTest itself.
    @unittest.expectedFailure
    def test_overlap(self):
        found, results = self.execute(
            'tests/submodule/test_nesting.py',
            'tests/submodule/test_nesting.py::test_things',
        )

        self.assertEqual(found, {
            'tests/submodule/test_nesting.py::test_stuff',
            'tests/submodule/test_nesting.py::test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_mixed(self):
        found, results = self.execute(
            'tests/submodule/subsubmodule/test_deep_nesting.py',
            'tests/submodule/test_nesting.py::test_stuff',
        )

        self.assertEqual(found, {
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff',
            'tests/submodule/subsubmodule/test_deep_nesting.py::test_things',
            'tests/submodule/test_nesting.py::test_stuff',
        })

        self.assertEqual(results, {'OK': 3})


class SuiteSplitTests(unittest.TestCase):
    def test_split_root(self):
        suite = PyTestTestSuite()
        parts = suite.split_test_id('tests.py::test_stuff')

        self.assertEqual(
            parts,
            [
                (TestModule, 'tests.py'),
                (TestMethod, 'test_stuff'),
            ]
        )

    def test_split_root_unittest(self):
        suite = PyTestTestSuite()
        parts = suite.split_test_id('tests.py::TestClass::test_stuff')

        self.assertEqual(
            parts,
            [
                (TestModule, 'tests.py'),
                (TestCase, 'TestClass'),
                (TestMethod, 'test_stuff'),
            ]
        )

    def test_split_minimal(self):
        suite = PyTestTestSuite()
        parts = suite.split_test_id('tests/test_module.py::test_stuff')

        self.assertEqual(
            parts,
            [
                (TestModule, 'tests'),
                (TestModule, 'test_module.py'),
                (TestMethod, 'test_stuff'),
            ]
        )

    def test_split_unittest(self):
        suite = PyTestTestSuite()
        parts = suite.split_test_id('tests/test_module.py::TestClass::test_stuff')

        self.assertEqual(
            parts,
            [
                (TestModule, 'tests'),
                (TestModule, 'test_module.py'),
                (TestCase, 'TestClass'),
                (TestMethod, 'test_stuff'),
            ]
        )

    def test_split_long(self):
        suite = PyTestTestSuite()
        parts = suite.split_test_id('tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff')

        self.assertEqual(
            parts,
            [
                (TestModule, 'tests'),
                (TestModule, 'submodule'),
                (TestModule, 'subsubmodule'),
                (TestModule, 'test_deep_nesting.py'),
                (TestMethod, 'test_stuff'),
            ]
        )


class SuiteJoinTests(unittest.TestCase):
    def test_join_method_unittest(self):
        suite = PyTestTestSuite()
        parent = TestCase(None, 'tests/module.py::TestClass', 'TestClass')
        self.assertEqual(
            suite.join_path(parent, TestMethod, 'test_stuff'),
            'tests/module.py::TestClass::test_stuff'
        )

    def test_join_method(self):
        suite = PyTestTestSuite()
        parent = TestCase(None, 'tests/module.py', 'module.py')
        self.assertEqual(
            suite.join_path(parent, TestMethod, 'test_stuff'),
            'tests/module.py::test_stuff'
        )

    def test_join_case(self):
        suite = PyTestTestSuite()
        parent = TestModule(None, 'tests/module.py', 'module.py')
        self.assertEqual(
            suite.join_path(parent, TestCase, 'TestClass'),
            'tests/module.py::TestClass'
        )

    def test_join_module(self):
        suite = PyTestTestSuite()
        parent = TestModule(None, 'tests', 'tests')
        self.assertEqual(
            suite.join_path(parent, TestModule, 'module.py'),
            'tests/module.py'
        )

    def test_join_submodule(self):
        suite = PyTestTestSuite()
        self.assertEqual(
            suite.join_path(suite, TestModule, 'tests'),
            'tests'
        )
