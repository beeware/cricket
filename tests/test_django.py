import json
import os
import subprocess
import unittest

from cricket.django.model import DjangoTestSuite


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.join(__file__)))
SAMPLE_DIR = os.path.join(ROOT_DIR, 'sample', 'django')


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(SAMPLE_DIR)

    def tearDown(self):
        os.chdir(self._cwd)

    def test_discovery(self):
        suite = DjangoTestSuite()
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
                'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
                'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
                'firstapp.tests.submodule.test_more_nesting.MoreNestedTests.test_stuff',
                'firstapp.tests.submodule.test_more_nesting.MoreNestedTests.test_things',
                'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
                'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
                'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_stuff',
                'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_things',
                'firstapp.tests.test_outcomes.BadTests.test_assertion_item',
                'firstapp.tests.test_outcomes.BadTests.test_error_item',
                'firstapp.tests.test_outcomes.BadTests.test_failing_item',
                'firstapp.tests.test_outcomes.BadTests.test_subtests',
                'firstapp.tests.test_outcomes.BadTests.test_upassed_item',
                'firstapp.tests.test_outcomes.BadTests.test_xfailing_item',
                'firstapp.tests.test_outcomes.GoodTests.test_passing_item',
                'firstapp.tests.test_outcomes.GoodTests.test_skipped_item',
                'firstapp.tests.test_unusual.UnusualTests.test_item_output',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_0',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_1',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_2',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_3',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_4',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_5',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_6',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_7',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_8',
                'firstapp.tests.test_unusual.UnusualTests.test_slow_9',
                'secondapp.tests.ModuleTests.test_stuff',
                'secondapp.tests.ModuleTests.test_things',
            }
        )



class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(SAMPLE_DIR)

    def tearDown(self):
        os.chdir(self._cwd)

    def execute(self, *args):
        suite = DjangoTestSuite()
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
            'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
            'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
            'firstapp.tests.submodule.test_more_nesting.MoreNestedTests.test_stuff',
            'firstapp.tests.submodule.test_more_nesting.MoreNestedTests.test_things',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_things',
            'firstapp.tests.test_outcomes.BadTests.test_assertion_item',
            'firstapp.tests.test_outcomes.BadTests.test_error_item',
            'firstapp.tests.test_outcomes.BadTests.test_failing_item',
            'firstapp.tests.test_outcomes.BadTests.test_subtests',
            'firstapp.tests.test_outcomes.BadTests.test_upassed_item',
            'firstapp.tests.test_outcomes.BadTests.test_xfailing_item',
            'firstapp.tests.test_outcomes.GoodTests.test_passing_item',
            'firstapp.tests.test_outcomes.GoodTests.test_skipped_item',
            'firstapp.tests.test_unusual.UnusualTests.test_item_output',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_0',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_1',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_2',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_3',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_4',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_5',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_6',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_7',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_8',
            'firstapp.tests.test_unusual.UnusualTests.test_slow_9',
            'secondapp.tests.ModuleTests.test_stuff',
            'secondapp.tests.ModuleTests.test_things',
        })

        self.assertEqual(results, {'OK': 25, 'F': 5, 'E': 1, 'x': 1, 'u': 1, 's': 1})

    def test_single_test_method(self):
        found, results = self.execute(
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
        )

        self.assertEqual(found, {
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
        })

        self.assertEqual(results, {'OK': 1})


    def test_multiple_test_methods(self):
        found, results = self.execute(
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
        )

        self.assertEqual(found, {
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_test_case(self):
        found, results = self.execute(
            'firstapp.tests.submodule.test_nesting.NestedTests',
        )

        self.assertEqual(found, {
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_module(self):
        found, results = self.execute(
            'firstapp.tests.submodule.test_nesting',
        )

        self.assertEqual(found, {
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 4})

    def test_submodules(self):
        found, results = self.execute(
            'firstapp.tests.submodule',
        )

        self.assertEqual(found, {
            'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
            'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
            'firstapp.tests.submodule.test_more_nesting.MoreNestedTests.test_stuff',
            'firstapp.tests.submodule.test_more_nesting.MoreNestedTests.test_things',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_things',
        })

    def test_app(self):
        found, results = self.execute(
            'secondapp',
        )

        self.assertEqual(found, {
            'secondapp.tests.ModuleTests.test_stuff',
            'secondapp.tests.ModuleTests.test_things',
        })

        self.assertEqual(results, {'OK': 2})

    def test_overlap(self):
        found, results = self.execute(
            'firstapp.tests.submodule.test_nesting',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
        )

        self.assertEqual(found, {
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_things',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_stuff',
            'firstapp.tests.submodule.test_nesting.OtherNestedTests.test_things',
        })

        self.assertEqual(results, {'OK': 4})

    def test_mixed(self):
        found, results = self.execute(
            'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'secondapp',
        )

        self.assertEqual(found, {
            'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_stuff',
            'firstapp.tests.submodule.subsubmodule.test_deep_nesting.DeepNestedTests.test_things',
            'firstapp.tests.submodule.test_nesting.NestedTests.test_stuff',
            'secondapp.tests.ModuleTests.test_stuff',
            'secondapp.tests.ModuleTests.test_things',
        })

        self.assertEqual(results, {'OK': 5})
