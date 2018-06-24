import unittest
from cricket.model import TestModule, TestCase

# Use Unittest as a template for TestSuite behavior.
from cricket.unittest.model import UnittestTestSuite as TestSuite

class TestTestSuite(unittest.TestCase):
    """Tests for the process of converting the output of the Discoverer
    into an internal tree.
    """
    def _full_tree(self, node):
        "Internal method generating a simple tree version of a test_suite node"
        if isinstance(node, TestCase):
            return (type(node), node._child_labels)
        else:
            return dict(
                ((type(sub_tree), sub_node), self._full_tree(sub_tree))
                for sub_node, sub_tree in node._child_nodes.items()
            )

    def test_no_tests(self):
        "If there are no tests, an empty tree is generated"
        test_suite = TestSuite()
        test_suite.refresh(test_list=[])
        self.assertEqual(test_suite.errors, [])
        self.assertEqual(sorted(self._full_tree(test_suite)), sorted({}))

    def test_with_tests(self):
        "If tests are found, the right tree is created"

        test_suite = TestSuite()
        test_suite.refresh([
                'tests.FunkyTestCase.test_something_unnecessary',
                'more_tests.FunkyTestCase.test_this_does_make_sense',
                'more_tests.FunkyTestCase.test_this_doesnt_make_sense',
                'more_tests.JankyTestCase.test_things',
                'deep_tests.package.DeepTestCase.test_doo_hickey',
            ])
        self.assertEqual(test_suite.errors, [])
        self.assertEqual(sorted(self._full_tree(test_suite)), sorted({
                (TestModule, 'tests'): {
                    (TestCase, 'FunkyTestCase'): [
                        'test_something_unnecessary'
                    ]
                },
                (TestModule, 'more_tests'): {
                    (TestCase, 'FunkyTestCase'): [
                        'test_this_doesnt_make_sense',
                        'test_this_doesnt_make_sense'
                    ],
                    (TestCase, 'JankyTestCase'): [
                        'test_things'
                    ]
                },
                (TestModule, 'deep_tests'): {
                    (TestModule, 'package'): {
                        (TestCase, 'DeepTestCase'): [
                            'test_doo_hickey'
                        ]
                    }
                }
            }))

    def test_with_tests_and_errors(self):
        "If tests *and* errors are found, the tree is still created."
        test_suite = TestSuite()
        test_suite.refresh([
                'tests.FunkyTestCase.test_something_unnecessary',
            ],
            errors=[
                'ERROR: you broke it, fool!',
            ]
        )

        self.assertEqual(test_suite.errors, [
            'ERROR: you broke it, fool!',
        ])
        self.assertEqual(sorted(self._full_tree(test_suite)), sorted({
                (TestModule, 'tests'): {
                    (TestCase, 'FunkyTestCase'): [
                        'test_something_unnecessary'
                    ]
                }
            }))


class FindLabelTests(unittest.TestCase):
    "Check that naming tests by labels reduces to the right runtime list."
    def setUp(self):
        self.maxDiff = None
        self.test_suite = TestSuite()
        self.test_suite.refresh([
                'app1.TestCase.test_method',

                'app2.TestCase1.test_method',
                'app2.TestCase2.test_method1',
                'app2.TestCase2.test_method2',

                'app3.tests.TestCase.test_method',

                'app4.tests1.TestCase.test_method',
                'app4.tests2.TestCase1.test_method',
                'app4.tests2.TestCase2.test_method1',
                'app4.tests2.TestCase2.test_method2',

                'app5.package.tests.TestCase.test_method',

                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2.TestCase1.test_method',
                'app6.package2.tests2.TestCase2.test_method1',
                'app6.package2.tests2.TestCase2.test_method2',

                'app7.package.subpackage.tests.TestCase.test_method',

                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2.test_method1',
                'app8.package2.subpackage2.tests2.TestCase2.test_method2',
            ])

    def test_single_test_test_suite(self):
        "If the test_suite only contains a single test, the reduction is always the full suite"
        self.test_suite = TestSuite()
        self.test_suite.refresh([
                'app.package.tests.TestCase.test_method',
            ])

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app.package.tests.TestCase.test_method'
            ]),
            (1, None))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app.package.tests.TestCase'
            ]),
            (1, None))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app.package.tests'
            ]),
            (1, None))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app.package'
            ]),
            (1, None))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app'
            ]),
            (1, None))

    def test_all_tests(self):
        "Without any qualifiers, all tests are run"
        self.assertEqual(self.test_suite.find_tests(), (22, None))

    def test_method_selection(self):
        "Explicitly named test method paths may be trimmed if they are unique"
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app1.TestCase.test_method'
            ]),
            (1, ['app1']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1.test_method'
            ]),
            (1, ['app2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase2.test_method1'
            ]),
            (1, ['app2.TestCase2.test_method1']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app3.tests.TestCase.test_method'
            ]),
            (1, ['app3']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1.TestCase.test_method'
            ]),
            (1, ['app4.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase1.test_method'
            ]),
            (1, ['app4.tests2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase2.test_method1'
            ]),
            (1, ['app4.tests2.TestCase2.test_method1']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app5.package.tests.TestCase.test_method'
            ]),
            (1, ['app5']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method'
            ]),
            (1, ['app6.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests1.TestCase.test_method'
            ]),
            (1, ['app6.package2.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase1.test_method'
            ]),
            (1, ['app6.package2.tests2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase2.test_method1'
            ]),
            (1, ['app6.package2.tests2.TestCase2.test_method1']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app7.package.subpackage.tests.TestCase.test_method'
            ]),
            (1, ['app7']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method'
            ]),
            (1, ['app8.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage1.tests.TestCase.test_method'
            ]),
            (1, ['app8.package2.subpackage1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests1.TestCase.test_method'
            ]),
            (1, ['app8.package2.subpackage2.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase1.test_method'
            ]),
            (1, ['app8.package2.subpackage2.tests2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase2.test_method1'
            ]),
            (1, ['app8.package2.subpackage2.tests2.TestCase2.test_method1']))

    def test_testcase_selection(self):
        "Explicitly named test case paths may be trimmed if they are unique"

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app1.TestCase'
            ]),
            (1, ['app1']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1'
            ]),
            (1, ['app2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase2'
            ]),
            (2, ['app2.TestCase2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app3.tests.TestCase'
            ]),
            (1, ['app3']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1.TestCase'
            ]),
            (1, ['app4.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase1'
            ]),
            (1, ['app4.tests2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase2'
            ]),
            (2, ['app4.tests2.TestCase2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app5.package.tests.TestCase'
            ]),
            (1, ['app5']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase'
            ]),
            (1, ['app6.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests1.TestCase'
            ]),
            (1, ['app6.package2.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase1'
            ]),
            (1, ['app6.package2.tests2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase2'
            ]),
            (2, ['app6.package2.tests2.TestCase2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app7.package.subpackage.tests.TestCase'
            ]),
            (1, ['app7']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase'
            ]),
            (1, ['app8.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage1.tests.TestCase'
            ]),
            (1, ['app8.package2.subpackage1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests1.TestCase'
            ]),
            (1, ['app8.package2.subpackage2.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase1'
            ]),
            (1, ['app8.package2.subpackage2.tests2.TestCase1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase2'
            ]),
            (2, ['app8.package2.subpackage2.tests2.TestCase2']))

    def test_testmodule_selection(self):
        "Explicitly named test module paths may be trimmed if they are unique"
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app3.tests'
            ]),
            (1, ['app3']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1'
            ]),
            (1, ['app4.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2'
            ]),
            (3, ['app4.tests2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app5.package.tests'
            ]),
            (1, ['app5']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests'
            ]),
            (1, ['app6.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests1'
            ]),
            (1, ['app6.package2.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2'
            ]),
            (3, ['app6.package2.tests2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app7.package.subpackage.tests'
            ]),
            (1, ['app7']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests'
            ]),
            (1, ['app8.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage1.tests'
            ]),
            (1, ['app8.package2.subpackage1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests1'
            ]),
            (1, ['app8.package2.subpackage2.tests1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2'
            ]),
            (3, ['app8.package2.subpackage2.tests2']))

    def test_package_selection(self):
        "Explicitly named test package paths may be trimmed if they are unique"
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app5.package'
            ]),
            (1, ['app5']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1'
            ]),
            (1, ['app6.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2'
            ]),
            (4, ['app6.package2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app7.package'
            ]),
            (1, ['app7']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1'
            ]),
            (1, ['app8.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2'
            ]),
            (5, ['app8.package2']))

    def test_subpackage_selection(self):
        "Explicitly named test subpackage paths may be trimmed if they are unique"
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app7.package.subpackage'
            ]),
            (1, ['app7']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage'
            ]),
            (1, ['app8.package1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage1'
            ]),
            (1, ['app8.package2.subpackage1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2'
            ]),
            (4, ['app8.package2.subpackage2']))

    def test_app_selection(self):
        "Explicitly named app paths return a count of all tests in the app"
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app1'
            ]),
            (1, ['app1']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2'
            ]),
            (3, ['app2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app3'
            ]),
            (1, ['app3']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4'
            ]),
            (4, ['app4']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app5'
            ]),
            (1, ['app5']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6'
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app7'
            ]),
            (1, ['app7']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8'
            ]),
            (6, ['app8']))

    def test_testcase_collapse(self):
        "If all methods in a test are selected, path is trimmed to the case"
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase2.test_method1',
                'app2.TestCase2.test_method2',
            ]),
            (2, ['app2.TestCase2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase2.test_method1',
                'app4.tests2.TestCase2.test_method2',
            ]),
            (2, ['app4.tests2.TestCase2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase2.test_method1',
                'app6.package2.tests2.TestCase2.test_method2',
            ]),
            (2, ['app6.package2.tests2.TestCase2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase2.test_method1',
                'app8.package2.subpackage2.tests2.TestCase2.test_method2',
            ]),
            (2, ['app8.package2.subpackage2.tests2.TestCase2']))

    def test_testmethod_collapse(self):
        "If all test cases in a test are selected, path is trimmed to the testmethod"

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1.test_method',
                'app2.TestCase2.test_method1',
                'app2.TestCase2.test_method2',
            ]),
            (3, ['app2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1.test_method',
                'app2.TestCase2',
            ]),
            (3, ['app2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1',
                'app2.TestCase2',
            ]),
            (3, ['app2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase1.test_method',
                'app4.tests2.TestCase2.test_method1',
                'app4.tests2.TestCase2.test_method2',
            ]),
            (3, ['app4.tests2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase1.test_method',
                'app4.tests2.TestCase2',
            ]),
            (3, ['app4.tests2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests2.TestCase1',
                'app4.tests2.TestCase2',
            ]),
            (3, ['app4.tests2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase1.test_method',
                'app6.package2.tests2.TestCase2.test_method1',
                'app6.package2.tests2.TestCase2.test_method2',
            ]),
            (3, ['app6.package2.tests2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase1.test_method',
                'app6.package2.tests2.TestCase2',
                'app6.package2.tests2',
            ]),
            (3, ['app6.package2.tests2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests2.TestCase1',
                'app6.package2.tests2.TestCase2',
            ]),
            (3, ['app6.package2.tests2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2.test_method1',
                'app8.package2.subpackage2.tests2.TestCase2.test_method2',
            ]),
            (3, ['app8.package2.subpackage2.tests2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (3, ['app8.package2.subpackage2.tests2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests2.TestCase1',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (3, ['app8.package2.subpackage2.tests2']))

    def test_package_collapse(self):
        "If all test cases in a test package are selected, path is trimmed to the testmethod"

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2.TestCase1.test_method',
                'app6.package2.tests2.TestCase2.test_method1',
                'app6.package2.tests2.TestCase2.test_method2',
            ]),
            (4, ['app6.package2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2.TestCase1.test_method',
                'app6.package2.tests2.TestCase2',
            ]),
            (4, ['app6.package2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package2.tests1.TestCase',
                'app6.package2.tests2.TestCase1',
                'app6.package2.tests2.TestCase2',
            ]),
            (4, ['app6.package2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2.test_method1',
                'app8.package2.subpackage2.tests2.TestCase2.test_method2',
            ]),
            (5, ['app8.package2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (5, ['app8.package2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage1.tests.TestCase',
                'app8.package2.subpackage2.tests1.TestCase',
                'app8.package2.subpackage2.tests2.TestCase1',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (5, ['app8.package2']))

    def test_subpackage_collapse(self):
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2.test_method1',
                'app8.package2.subpackage2.tests2.TestCase2.test_method2',
            ]),
            (4, ['app8.package2.subpackage2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (4, ['app8.package2.subpackage2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package2.subpackage2.tests1.TestCase',
                'app8.package2.subpackage2.tests2.TestCase1',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (4, ['app8.package2.subpackage2']))

    def test_app_collapse(self):
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1.test_method',
                'app2.TestCase2.test_method1',
                'app2.TestCase2.test_method2',
            ]),
            (3, ['app2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1.test_method',
                'app2.TestCase2',
            ]),
            (3, ['app2']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app2.TestCase1',
                'app2.TestCase2',
            ]),
            (3, ['app2']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1.TestCase.test_method',
                'app4.tests2.TestCase1.test_method',
                'app4.tests2.TestCase2.test_method1',
                'app4.tests2.TestCase2.test_method2',
            ]),
            (4, ['app4']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1.TestCase.test_method',
                'app4.tests2.TestCase1.test_method',
                'app4.tests2.TestCase2',
            ]),
            (4, ['app4']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1.TestCase.test_method',
                'app4.tests2.TestCase1',
                'app4.tests2.TestCase2',
            ]),
            (4, ['app4']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1.TestCase.test_method',
                'app4.tests2',
            ]),
            (4, ['app4']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1.TestCase',
                'app4.tests2',
            ]),
            (4, ['app4']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app4.tests1',
                'app4.tests2',
            ]),
            (4, ['app4']))

        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2.TestCase1.test_method',
                'app6.package2.tests2.TestCase2.test_method1',
                'app6.package2.tests2.TestCase2.test_method2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2.TestCase1.test_method',
                'app6.package2.tests2.TestCase2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2.TestCase1',
                'app6.package2.tests2.TestCase2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2.TestCase1',
                'app6.package2.tests2.TestCase2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase.test_method',
                'app6.package2.tests2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1.TestCase',
                'app6.package2.tests2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2.tests1',
                'app6.package2.tests2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase.test_method',
                'app6.package2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests.TestCase',
                'app6.package2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1.tests',
                'app6.package2',
            ]),
            (5, ['app6']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app6.package1',
                'app6.package2',
            ]),
            (5, ['app6']))


        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2.test_method1',
                'app8.package2.subpackage2.tests2.TestCase2.test_method2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1.test_method',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2.TestCase1',
                'app8.package2.subpackage2.tests2.TestCase2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase.test_method',
                'app8.package2.subpackage2.tests2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1.TestCase',
                'app8.package2.subpackage2.tests2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2.tests1',
                'app8.package2.subpackage2.tests2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase.test_method',
                'app8.package2.subpackage2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests.TestCase',
                'app8.package2.subpackage2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1.tests',
                'app8.package2.subpackage2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2.subpackage1',
                'app8.package2.subpackage2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase.test_method',
                'app8.package2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests.TestCase',
                'app8.package2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage.tests',
                'app8.package2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1.subpackage',
                'app8.package2',
            ]),
            (6, ['app8']))
        self.assertEqual(self.test_suite.find_tests(labels=[
                'app8.package1',
                'app8.package2',
            ]),
            (6, ['app8']))
