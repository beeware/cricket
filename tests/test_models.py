import mock

from cricket.compat import unittest
from cricket.model import Project, ModelLoadError, TestModule, TestCase


class TestProject(unittest.TestCase):
    """Tests for the process of converting the output of the Discoverer
    into an internal tree.
    """
    def _full_tree(self, node):
        "Internal method generating a simple tree version of a project node"
        if isinstance(node, TestCase):
            return (type(node), node.keys())
        else:
            return dict(
                ((type(sub_tree), sub_node), self._full_tree(sub_tree))
                for sub_node, sub_tree in node.items()
            )

    def test_no_tests(self):
        "If there are no tests, an empty tree is generated"
        project = Project(test_list=[])
        self.assertEquals(project.errors, [])
        self.assertItemsEqual(self._full_tree(project), {})

    def test_with_tests(self):
        "If tests are found, the right tree is created"

        project = Project(test_list=[
            'tests.FunkyTestCase.test_something_unnecessary',
            'more_tests.FunkyTestCase.test_this_does_make_sense',
            'more_tests.FunkyTestCase.test_this_doesnt_make_sense',
            'more_tests.JankyTestCase.test_things',
            'deep_tests.package.DeepTestCase.test_doo_hickey',
        ])
        self.assertEquals(project.errors, [])
        self.assertItemsEqual(self._full_tree(project), {
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
            })

    def test_with_tests_and_errors(self):
        "If tests *and* errors are found, the tree is still created."
        project = Project(test_list=[
                'tests.FunkyTestCase.test_something_unnecessary',
            ], errors = [
                'ERROR: you broke it, fool!',
            ])

        self.assertEquals(project.errors, [
            'ERROR: you broke it, fool!',
        ])
        self.assertItemsEqual(self._full_tree(project), {
                (TestModule, 'tests'): {
                    (TestCase, 'FunkyTestCase'): [
                        'test_something_unnecessary'
                    ]
                }
            })


class FindLabelTests(unittest.TestCase):
    "Check that naming tests by labels reduces to the right runtime list."
    def setUp(self):
        super(FindLabelTests, self).setUp()
        self.project = Project(test_list=[
            'app1.TestCase.test_method',
            'app2.TestCase1.test_method',
            'app2.TestCase2.test_method1',
            'app2.TestCase2.test_method2',
            'app3.tests.TestCase.test_method',
            'app4.tests1.TestCase.test_method',
            'app4.tests2.TestCase2.test_method1',
            'app4.tests2.TestCase2.test_method2',
            'app5.pacakge.tests.TestCase.test_method',
            'app5.package.tests1.TestCase.test_method',
            'app5.package.tests2.TestCase2.test_method1',
            'app5.package.tests2.TestCase2.test_method2',
            'app6.package1.tests.TestCase.test_method',
            'app6.package2.tests1.TestCase.test_method',
            'app6.package2.tests2.TestCase2.test_method1',
            'app6.package2.tests2.TestCase2.test_method2',
        ])

    def test_all_tests(self):
        "Without any qualifiers, all tests are run"
        self.assertEquals(self.project.find_tests(), (16, []))
