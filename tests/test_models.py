import unittest
from cricket.model import TestSuite, TestModule, TestCase


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
        super(FindLabelTests, self).setUp()
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

    def test_all_tests(self):
        "Without any qualifiers, all tests are run"
        self.assertEquals(self.test_suite.find_tests()[0], 22)
