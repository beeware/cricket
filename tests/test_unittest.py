import json
import os
import subprocess
import unittest

from cricket.unittest.model import UnittestTestSuite
from cricket.model import TestModule, TestCase, TestMethod


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.join(__file__)))
SAMPLE_DIR = os.path.join(ROOT_DIR, 'sample', 'unittest')


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(SAMPLE_DIR)

    def tearDown(self):
        os.chdir(self._cwd)

    def test_discovery(self):
        suite = UnittestTestSuite()
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
                'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
                'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
                'tests.submodule.test_more_nesting.MoreNestedTests.test_stuff',
                'tests.submodule.test_more_nesting.MoreNestedTests.test_things',
                'tests.submodule.test_nesting.NestedTests.test_stuff',
                'tests.submodule.test_nesting.NestedTests.test_things',
                'tests.submodule.test_nesting.OtherNestedTests.test_stuff',
                'tests.submodule.test_nesting.OtherNestedTests.test_things',
                'tests.test_outcomes.BadTests.test_assertion_item',
                'tests.test_outcomes.BadTests.test_error_item',
                'tests.test_outcomes.BadTests.test_failing_item',
                'tests.test_outcomes.BadTests.test_subtests',
                'tests.test_outcomes.BadTests.test_upassed_item',
                'tests.test_outcomes.BadTests.test_xfailing_item',
                'tests.test_outcomes.GoodTests.test_passing_item',
                'tests.test_outcomes.GoodTests.test_skipped_item',
                'tests.test_unusual.UnusualTests.test_item_output',
                'tests.test_unusual.UnusualTests.test_slow_0',
                'tests.test_unusual.UnusualTests.test_slow_1',
                'tests.test_unusual.UnusualTests.test_slow_2',
                'tests.test_unusual.UnusualTests.test_slow_3',
                'tests.test_unusual.UnusualTests.test_slow_4',
                'tests.test_unusual.UnusualTests.test_slow_5',
                'tests.test_unusual.UnusualTests.test_slow_6',
                'tests.test_unusual.UnusualTests.test_slow_7',
                'tests.test_unusual.UnusualTests.test_slow_8',
                'tests.test_unusual.UnusualTests.test_slow_9',
            }
        )


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(SAMPLE_DIR)

    def tearDown(self):
        os.chdir(self._cwd)

    def execute(self, *args):
        suite = UnittestTestSuite()
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
            'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
            'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
            'tests.submodule.test_more_nesting.MoreNestedTests.test_stuff',
            'tests.submodule.test_more_nesting.MoreNestedTests.test_things',
            'tests.submodule.test_nesting.NestedTests.test_stuff',
            'tests.submodule.test_nesting.NestedTests.test_things',
            'tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'tests.submodule.test_nesting.OtherNestedTests.test_things',
            'tests.test_outcomes.BadTests.test_assertion_item',
            'tests.test_outcomes.BadTests.test_error_item',
            'tests.test_outcomes.BadTests.test_failing_item',
            'tests.test_outcomes.BadTests.test_subtests',
            'tests.test_outcomes.BadTests.test_upassed_item',
            'tests.test_outcomes.BadTests.test_xfailing_item',
            'tests.test_outcomes.GoodTests.test_passing_item',
            'tests.test_outcomes.GoodTests.test_skipped_item',
            'tests.test_unusual.UnusualTests.test_item_output',
            'tests.test_unusual.UnusualTests.test_slow_0',
            'tests.test_unusual.UnusualTests.test_slow_1',
            'tests.test_unusual.UnusualTests.test_slow_2',
            'tests.test_unusual.UnusualTests.test_slow_3',
            'tests.test_unusual.UnusualTests.test_slow_4',
            'tests.test_unusual.UnusualTests.test_slow_5',
            'tests.test_unusual.UnusualTests.test_slow_6',
            'tests.test_unusual.UnusualTests.test_slow_7',
            'tests.test_unusual.UnusualTests.test_slow_8',
            'tests.test_unusual.UnusualTests.test_slow_9',
        })

        self.assertEqual(results, {'OK': 23, 'F': 5, 'E': 1, 'x': 1, 'u': 1, 's': 1})

    def test_single_test_method(self):
        found, results = self.execute(
            'tests.submodule.test_nesting.NestedTests.test_stuff',
        )

        self.assertEqual(found, {
            'tests.submodule.test_nesting.NestedTests.test_stuff',
        })

        self.assertEqual(results, {'OK': 1})


    def test_multiple_test_methods(self):
        found, results = self.execute(
            'tests.submodule.test_nesting.NestedTests.test_stuff',
            'tests.submodule.test_nesting.NestedTests.test_things',
        )

        self.assertEqual(found, {
            'tests.submodule.test_nesting.NestedTests.test_stuff',
            'tests.submodule.test_nesting.NestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_test_case(self):
        found, results = self.execute(
            'tests.submodule.test_nesting.NestedTests',
        )

        self.assertEqual(found, {
            'tests.submodule.test_nesting.NestedTests.test_stuff',
            'tests.submodule.test_nesting.NestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_module(self):
        found, results = self.execute(
            'tests.submodule.test_nesting',
        )

        self.assertEqual(found, {
            'tests.submodule.test_nesting.NestedTests.test_stuff',
            'tests.submodule.test_nesting.NestedTests.test_things',
            'tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'tests.submodule.test_nesting.OtherNestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 4})

    def test_submodules(self):
        found, results = self.execute(
            'tests.submodule',
        )

        self.assertEqual(found, {
            'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
            'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
            'tests.submodule.test_more_nesting.MoreNestedTests.test_stuff',
            'tests.submodule.test_more_nesting.MoreNestedTests.test_things',
            'tests.submodule.test_nesting.NestedTests.test_stuff',
            'tests.submodule.test_nesting.NestedTests.test_things',
            'tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'tests.submodule.test_nesting.OtherNestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 8})

    def test_overlap(self):
        found, results = self.execute(
            'tests.submodule.test_nesting',
            'tests.submodule.test_nesting.NestedTests.test_things',
        )

        self.assertEqual(found, {
            'tests.submodule.test_nesting.NestedTests.test_stuff',
            'tests.submodule.test_nesting.NestedTests.test_things',
            'tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'tests.submodule.test_nesting.OtherNestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 4})

    def test_mixed(self):
        found, results = self.execute(
            'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests',
            'tests.submodule.test_nesting.NestedTests.test_stuff',
        )

        self.assertEqual(found, {
            'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
            'tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
            'tests.submodule.test_nesting.NestedTests.test_stuff',
        })

        self.assertEqual(results, {'OK': 3})


class SuiteSplitTests(unittest.TestCase):
    def test_split_minimal(self):
        suite = UnittestTestSuite()
        parts = suite.split_test_id('tests.TestClass.test_stuff')

        self.assertEqual(
            parts,
            [
                (TestModule, 'tests'),
                (TestCase, 'TestClass'),
                (TestMethod, 'test_stuff'),
            ]
        )

    def test_split_long(self):
        suite = UnittestTestSuite()
        parts = suite.split_test_id('tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff')

        self.assertEqual(
            parts,
            [
                (TestModule, 'tests'),
                (TestModule, 'submodule'),
                (TestModule, 'subsubmodule'),
                (TestModule, 'test_deep_nesting'),
                (TestCase, 'DeepNestedTests'),
                (TestMethod, 'test_stuff'),
            ]
        )


class SuiteJoinTests(unittest.TestCase):
    def test_join_method(self):
        suite = UnittestTestSuite()
        parent = TestCase(None, 'tests.module.TestClass', 'TestClass')
        self.assertEqual(
            suite.join_path(parent, TestMethod, 'test_stuff'),
            'tests.module.TestClass.test_stuff'
        )

    def test_join_case(self):
        suite = UnittestTestSuite()
        parent = TestModule(None, 'tests.module', 'module')
        self.assertEqual(
            suite.join_path(parent, TestCase, 'TestClass'),
            'tests.module.TestClass'
        )

    def test_join_module(self):
        suite = UnittestTestSuite()
        parent = TestModule(None, 'tests', 'tests')
        self.assertEqual(
            suite.join_path(parent, TestModule, 'module'),
            'tests.module'
        )

    def test_join_submodule(self):
        suite = UnittestTestSuite()
        self.assertEqual(
            suite.join_path(suite, TestModule, 'tests'),
            'tests'
        )
