import sys

import pytest

from cricket.model import (
    TestCase as CTCase,
)
from cricket.model import (
    TestMethod as CTMethod,
)
from cricket.model import (
    TestModule as CTModule,
)
from cricket.pytest.model import PyTestTestSuite as PTSuite


def _full_tree(node):
    "Internal method generating a simple tree version of a test_suite node"
    if isinstance(node, CTCase):
        return (
            type(node),
            node._name,
            [_full_tree(sub_tree) for _, sub_tree in node._child_nodes.items()],
        )
    elif isinstance(node, CTMethod):
        return node._name
    elif isinstance(node, CTModule):
        return (
            type(node),
            node._name,
            [_full_tree(sub_tree) for _, sub_tree in node._child_nodes.items()],
        )
    elif isinstance(node, PTSuite):
        return [_full_tree(sub_tree) for _, sub_tree in node._child_nodes.items()]
    else:
        raise TypeError(f"Don't know how to handle node of type {type(node)}")


@pytest.mark.parametrize(
    "test_list, expected_errors, expected_tree",
    [
        pytest.param([], [], [], id="0"),
    ],
)
def test_no_tests(test_list, expected_errors, expected_tree):
    "If there are no tests, an empty tree is generated"
    test_suite = PTSuite()
    test_suite.refresh(test_list)
    assert (test_suite.errors, _full_tree(test_suite)) == (
        expected_errors,
        expected_tree,
    )


@pytest.mark.parametrize(
    "test_list, expected_errors, expected_tree",
    [
        pytest.param(
            [
                "tests.py::test_method",
                "tests.py::FunkyTestCase::test_something_unnecessary",
                "more_tests.py::test_other_method",
                "more_tests.py::test_more",
                "more_tests.py::FunkyTestCase::test_this_does_make_sense",
                "more_tests.py::FunkyTestCase::test_this_doesnt_make_sense",
                "more_tests.py::JankyTestCase::test_things",
                "deep_tests/package.py::test_deep_widget",
                "deep_tests/package.py::DeepTestCase::test_doo_hickey",
            ],
            [],
            [
                (
                    CTModule,
                    "tests.py",
                    [
                        "test_method",
                        (CTCase, "FunkyTestCase", ["test_something_unnecessary"]),
                    ],
                ),
                (
                    CTModule,
                    "more_tests.py",
                    [
                        "test_other_method",
                        "test_more",
                        (
                            CTCase,
                            "FunkyTestCase",
                            [
                                "test_this_does_make_sense",
                                "test_this_doesnt_make_sense",
                            ],
                        ),
                        (CTCase, "JankyTestCase", ["test_things"]),
                    ],
                ),
                (
                    CTModule,
                    "deep_tests",
                    [
                        (
                            CTModule,
                            "package.py",
                            [
                                "test_deep_widget",
                                (CTCase, "DeepTestCase", ["test_doo_hickey"]),
                            ],
                        ),
                    ],
                ),
            ],
            id="0",
        ),
    ],
)
def test_with_tests(test_list, expected_errors, expected_tree):
    "If tests are found, the right tree is created"
    test_suite = PTSuite()
    test_suite.refresh(test_list)
    assert (test_suite.errors, _full_tree(test_suite)) == (
        expected_errors,
        expected_tree,
    )


@pytest.mark.parametrize(
    "test_list, errors, expected_errors, expected_tree",
    [
        pytest.param(
            [
                "tests.py::FunkyTestCase::test_something_unnecessary",
            ],
            [
                "ERROR: you broke it, fool!",
            ],
            [
                "ERROR: you broke it, fool!",
            ],
            [
                (
                    CTModule,
                    "tests.py",
                    [(CTCase, "FunkyTestCase", ["test_something_unnecessary"])],
                )
            ],
            id="0",
        ),
    ],
)
def test_with_tests_and_errors(test_list, errors, expected_errors, expected_tree):
    "If tests *and* errors are found, the tree is still created."
    test_suite = PTSuite()
    test_suite.refresh(test_list, errors=errors)
    assert (test_suite.errors, _full_tree(test_suite)) == (
        expected_errors,
        expected_tree,
    )


@pytest.fixture
def test_suite():
    suite = PTSuite()
    suite.refresh(
        [
            "test_module.py::test_method",
            "app1.py::TestCase::test_method",
            "app2.py::TestCase1::test_method",
            "app2.py::TestCase2::test_method1",
            "app2.py::TestCase2::test_method2",
            "app3/tests.py::TestCase::test_method",
            "app4/tests1.py::TestCase::test_method",
            "app4/tests2.py::TestCase1::test_method",
            "app4/tests2.py::TestCase2::test_method1",
            "app4/tests2.py::TestCase2::test_method2",
            "app5/package/tests.py::TestCase::test_method",
            "app6/package1/tests.py::TestCase::test_method",
            "app6/package2/tests1.py::TestCase::test_method",
            "app6/package2/tests2.py::TestCase1::test_method",
            "app6/package2/tests2.py::TestCase2::test_method1",
            "app6/package2/tests2.py::TestCase2::test_method2",
            "app7/package/subpackage/tests.py::TestCase::test_method",
            "app8/package1/subpackage/tests.py::TestCase::test_method",
            "app8/package2/subpackage1/tests.py::TestCase::test_method",
            "app8/package2/subpackage2/tests1.py::TestCase::test_method",
            "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
            "app8/package2/subpackage2/tests2.py::TestCase2::test_method1",
            "app8/package2/subpackage2/tests2.py::TestCase2::test_method2",
        ]
    )
    return suite


@pytest.mark.parametrize(
    "label, expected",
    [
        pytest.param("app/package/tests.py::TestCase::test_method", (1, None), id="0"),
        pytest.param("app/package/tests.py::TestCase", (1, None), id="1"),
        pytest.param("app/package/tests.py", (1, None), id="2"),
        pytest.param("app/package", (1, None), id="3"),
        pytest.param("app", (1, None), id="4"),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_single_test_test_suite(label, expected):
    """If the test_suite only contains a single test, the reduction is
    always the full suite"""
    test_suite = PTSuite()
    test_suite.refresh(
        [
            "app/package/tests.py::TestCase::test_method",
        ]
    )
    assert test_suite.find_tests(labels=[label]) == expected


def test_all_tests(test_suite):
    "Without any qualifiers, all tests are run"
    assert test_suite.find_tests() == (23, None)


@pytest.mark.parametrize(
    "label, expected",
    [
        pytest.param("app1.py::TestCase::test_method", (1, ["app1.py"]), id="0"),
        pytest.param(
            "app2.py::TestCase1::test_method",
            (1, ["app2.py::TestCase1"]),
            id="1",
        ),
        pytest.param(
            "app2.py::TestCase2::test_method1",
            (1, ["app2.py::TestCase2::test_method1"]),
            id="2",
        ),
        pytest.param("app3/tests.py::TestCase::test_method", (1, ["app3"]), id="3"),
        pytest.param(
            "app4/tests1.py::TestCase::test_method",
            (1, ["app4/tests1.py"]),
            id="4",
        ),
        pytest.param(
            "app4/tests2.py::TestCase1::test_method",
            (1, ["app4/tests2.py::TestCase1"]),
            id="5",
        ),
        pytest.param(
            "app4/tests2.py::TestCase2::test_method1",
            (1, ["app4/tests2.py::TestCase2::test_method1"]),
            id="6",
        ),
        pytest.param(
            "app5/package/tests.py::TestCase::test_method",
            (1, ["app5"]),
            id="7",
        ),
        pytest.param(
            "app6/package1/tests.py::TestCase::test_method",
            (1, ["app6/package1"]),
            id="8",
        ),
        pytest.param(
            "app6/package2/tests1.py::TestCase::test_method",
            (1, ["app6/package2/tests1.py"]),
            id="9",
        ),
        pytest.param(
            "app6/package2/tests2.py::TestCase1::test_method",
            (1, ["app6/package2/tests2.py::TestCase1"]),
            id="10",
        ),
        pytest.param(
            "app6/package2/tests2.py::TestCase2::test_method1",
            (1, ["app6/package2/tests2.py::TestCase2::test_method1"]),
            id="11",
        ),
        pytest.param(
            "app7/package/subpackage/tests.py::TestCase::test_method",
            (1, ["app7"]),
            id="12",
        ),
        pytest.param(
            "app8/package1/subpackage/tests.py::TestCase::test_method",
            (1, ["app8/package1"]),
            id="13",
        ),
        pytest.param(
            "app8/package2/subpackage1/tests.py::TestCase::test_method",
            (1, ["app8/package2/subpackage1"]),
            id="14",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests1.py::TestCase::test_method",
            (1, ["app8/package2/subpackage2/tests1.py"]),
            id="15",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
            (1, ["app8/package2/subpackage2/tests2.py::TestCase1"]),
            id="16",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests2.py::TestCase2::test_method1",
            (1, ["app8/package2/subpackage2/tests2.py::TestCase2::test_method1"]),
            id="17",
        ),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_method_selection(test_suite, label, expected):
    "Explicitly named test method paths may be trimmed if they are unique"
    assert test_suite.find_tests(labels=[label]) == expected


@pytest.mark.parametrize(
    "label, expected",
    [
        pytest.param("app1.py::TestCase", (1, ["app1.py"]), id="0"),
        pytest.param("app2.py::TestCase1", (1, ["app2.py::TestCase1"]), id="1"),
        pytest.param("app2.py::TestCase2", (2, ["app2.py::TestCase2"]), id="2"),
        pytest.param("app3/tests.py::TestCase", (1, ["app3"]), id="3"),
        pytest.param("app4/tests1.py::TestCase", (1, ["app4/tests1.py"]), id="4"),
        pytest.param(
            "app4/tests2.py::TestCase1",
            (1, ["app4/tests2.py::TestCase1"]),
            id="5",
        ),
        pytest.param(
            "app4/tests2.py::TestCase2",
            (2, ["app4/tests2.py::TestCase2"]),
            id="6",
        ),
        pytest.param("app5/package/tests.py::TestCase", (1, ["app5"]), id="7"),
        pytest.param(
            "app6/package1/tests.py::TestCase",
            (1, ["app6/package1"]),
            id="8",
        ),
        pytest.param(
            "app6/package2/tests1.py::TestCase",
            (1, ["app6/package2/tests1.py"]),
            id="9",
        ),
        pytest.param(
            "app6/package2/tests2.py::TestCase1",
            (1, ["app6/package2/tests2.py::TestCase1"]),
            id="10",
        ),
        pytest.param(
            "app6/package2/tests2.py::TestCase2",
            (2, ["app6/package2/tests2.py::TestCase2"]),
            id="11",
        ),
        pytest.param(
            "app7/package/subpackage/tests.py::TestCase",
            (1, ["app7"]),
            id="12",
        ),
        pytest.param(
            "app8/package1/subpackage/tests.py::TestCase",
            (1, ["app8/package1"]),
            id="13",
        ),
        pytest.param(
            "app8/package2/subpackage1/tests.py::TestCase",
            (1, ["app8/package2/subpackage1"]),
            id="14",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests1.py::TestCase",
            (1, ["app8/package2/subpackage2/tests1.py"]),
            id="15",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests2.py::TestCase1",
            (1, ["app8/package2/subpackage2/tests2.py::TestCase1"]),
            id="16",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests2.py::TestCase2",
            (2, ["app8/package2/subpackage2/tests2.py::TestCase2"]),
            id="17",
        ),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_testcase_selection(test_suite, label, expected):
    "Explicitly named test case paths may be trimmed if they are unique"
    assert test_suite.find_tests(labels=[label]) == expected


@pytest.mark.parametrize(
    "label, expected",
    [
        pytest.param("app3/tests.py", (1, ["app3"]), id="0"),
        pytest.param("app4/tests1.py", (1, ["app4/tests1.py"]), id="1"),
        pytest.param("app4/tests2.py", (3, ["app4/tests2.py"]), id="2"),
        pytest.param("app5/package/tests.py", (1, ["app5"]), id="3"),
        pytest.param("app6/package1/tests.py", (1, ["app6/package1"]), id="4"),
        pytest.param(
            "app6/package2/tests1.py",
            (1, ["app6/package2/tests1.py"]),
            id="5",
        ),
        pytest.param(
            "app6/package2/tests2.py",
            (3, ["app6/package2/tests2.py"]),
            id="6",
        ),
        pytest.param(
            "app7/package/subpackage/tests.py",
            (1, ["app7"]),
            id="7",
        ),
        pytest.param(
            "app8/package1/subpackage/tests.py",
            (1, ["app8/package1"]),
            id="8",
        ),
        pytest.param(
            "app8/package2/subpackage1/tests.py",
            (1, ["app8/package2/subpackage1"]),
            id="9",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests1.py",
            (1, ["app8/package2/subpackage2/tests1.py"]),
            id="10",
        ),
        pytest.param(
            "app8/package2/subpackage2/tests2.py",
            (3, ["app8/package2/subpackage2/tests2.py"]),
            id="11",
        ),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_testmodule_selection(test_suite, label, expected):
    "Explicitly named test module paths may be trimmed if they are unique"
    assert test_suite.find_tests(labels=[label]) == expected


@pytest.mark.parametrize(
    "label, expected",
    [
        pytest.param("app5/package", (1, ["app5"]), id="0"),
        pytest.param("app6/package1", (1, ["app6/package1"]), id="1"),
        pytest.param("app6/package2", (4, ["app6/package2"]), id="2"),
        pytest.param("app7/package", (1, ["app7"]), id="3"),
        pytest.param("app8/package1", (1, ["app8/package1"]), id="4"),
        pytest.param("app8/package2", (5, ["app8/package2"]), id="5"),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_package_selection(test_suite, label, expected):
    "Explicitly named test package paths may be trimmed if they are unique"
    assert test_suite.find_tests(labels=[label]) == expected


@pytest.mark.parametrize(
    "label, expected",
    [
        pytest.param("app7/package/subpackage", (1, ["app7"]), id="0"),
        pytest.param("app8/package1/subpackage", (1, ["app8/package1"]), id="1"),
        pytest.param(
            "app8/package2/subpackage1",
            (1, ["app8/package2/subpackage1"]),
            id="2",
        ),
        pytest.param(
            "app8/package2/subpackage2",
            (4, ["app8/package2/subpackage2"]),
            id="3",
        ),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_subpackage_selection(test_suite, label, expected):
    "Explicitly named test subpackage paths may be trimmed if they are unique"
    assert test_suite.find_tests(labels=[label]) == expected


@pytest.mark.parametrize(
    "label, expected",
    [
        pytest.param("app1.py", (1, ["app1.py"]), id="app1"),
        pytest.param("app2.py", (3, ["app2.py"]), id="app2"),
        pytest.param("app3", (1, ["app3"]), id="app3"),
        pytest.param("app4", (4, ["app4"]), id="app4"),
        pytest.param("app5", (1, ["app5"]), id="app5"),
        pytest.param("app6", (5, ["app6"]), id="app6"),
        pytest.param("app7", (1, ["app7"]), id="app7"),
        pytest.param("app8", (6, ["app8"]), id="app8"),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_app_selection(test_suite, label, expected):
    "Explicitly named app paths return a count of all tests in the app"
    assert test_suite.find_tests(labels=[label]) == expected


@pytest.mark.parametrize(
    "labels, expected",
    [
        pytest.param(
            [
                "app2.py::TestCase2::test_method1",
                "app2.py::TestCase2::test_method2",
            ],
            (2, ["app2.py::TestCase2"]),
            id="0",
        ),
        pytest.param(
            [
                "app4/tests2.py::TestCase2::test_method1",
                "app4/tests2.py::TestCase2::test_method2",
            ],
            (2, ["app4/tests2.py::TestCase2"]),
            id="1",
        ),
        pytest.param(
            [
                "app6/package2/tests2.py::TestCase2::test_method1",
                "app6/package2/tests2.py::TestCase2::test_method2",
            ],
            (2, ["app6/package2/tests2.py::TestCase2"]),
            id="2",
        ),
        pytest.param(
            [
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method1",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method2",
            ],
            (2, ["app8/package2/subpackage2/tests2.py::TestCase2"]),
            id="3",
        ),
    ],
)
def test_testcase_collapse(test_suite, labels, expected):
    "If all methods in a test are selected, path is trimmed to the case"
    assert test_suite.find_tests(labels=labels) == expected


@pytest.mark.parametrize(
    "labels, expected",
    [
        pytest.param(
            [
                "app2.py::TestCase1::test_method",
                "app2.py::TestCase2::test_method1",
                "app2.py::TestCase2::test_method2",
            ],
            (3, ["app2.py"]),
            id="0",
        ),
        pytest.param(
            [
                "app2.py::TestCase1::test_method",
                "app2.py::TestCase2",
            ],
            (3, ["app2.py"]),
            id="1",
        ),
        pytest.param(
            [
                "app2.py::TestCase1",
                "app2.py::TestCase2",
            ],
            (3, ["app2.py"]),
            id="2",
        ),
        pytest.param(
            [
                "app4/tests2.py::TestCase1::test_method",
                "app4/tests2.py::TestCase2::test_method1",
                "app4/tests2.py::TestCase2::test_method2",
            ],
            (3, ["app4/tests2.py"]),
            id="3",
        ),
        pytest.param(
            [
                "app4/tests2.py::TestCase1::test_method",
                "app4/tests2.py::TestCase2",
            ],
            (3, ["app4/tests2.py"]),
            id="4",
        ),
        pytest.param(
            [
                "app4/tests2.py::TestCase1",
                "app4/tests2.py::TestCase2",
            ],
            (3, ["app4/tests2.py"]),
            id="5",
        ),
        pytest.param(
            [
                "app6/package2/tests2.py::TestCase1::test_method",
                "app6/package2/tests2.py::TestCase2::test_method1",
                "app6/package2/tests2.py::TestCase2::test_method2",
            ],
            (3, ["app6/package2/tests2.py"]),
            id="6",
        ),
        pytest.param(
            [
                "app6/package2/tests2.py::TestCase1::test_method",
                "app6/package2/tests2.py::TestCase2",
                "app6/package2/tests2.py",
            ],
            (3, ["app6/package2/tests2.py"]),
            id="7",
        ),
        pytest.param(
            [
                "app6/package2/tests2.py::TestCase1",
                "app6/package2/tests2.py::TestCase2",
            ],
            (3, ["app6/package2/tests2.py"]),
            id="8",
        ),
        pytest.param(
            [
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method1",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method2",
            ],
            (3, ["app8/package2/subpackage2/tests2.py"]),
            id="9",
        ),
        pytest.param(
            [
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (3, ["app8/package2/subpackage2/tests2.py"]),
            id="10",
        ),
        pytest.param(
            [
                "app8/package2/subpackage2/tests2.py::TestCase1",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (3, ["app8/package2/subpackage2/tests2.py"]),
            id="11",
        ),
    ],
)
def test_testmethod_collapse(test_suite, labels, expected):
    "If all test cases in a test are selected, path is trimmed to the testmethod"
    assert test_suite.find_tests(labels=labels) == expected


@pytest.mark.parametrize(
    "labels, expected",
    [
        pytest.param(
            [
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py::TestCase1::test_method",
                "app6/package2/tests2.py::TestCase2::test_method1",
                "app6/package2/tests2.py::TestCase2::test_method2",
            ],
            (4, ["app6/package2"]),
            id="0",
        ),
        pytest.param(
            [
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py::TestCase1::test_method",
                "app6/package2/tests2.py::TestCase2",
            ],
            (4, ["app6/package2"]),
            id="1",
        ),
        pytest.param(
            [
                "app6/package2/tests1.py::TestCase",
                "app6/package2/tests2.py::TestCase1",
                "app6/package2/tests2.py::TestCase2",
            ],
            (4, ["app6/package2"]),
            id="2",
        ),
        pytest.param(
            [
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method1",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method2",
            ],
            (5, ["app8/package2"]),
            id="3",
        ),
        pytest.param(
            [
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (5, ["app8/package2"]),
            id="4",
        ),
        pytest.param(
            [
                "app8/package2/subpackage1/tests.py::TestCase",
                "app8/package2/subpackage2/tests1.py::TestCase",
                "app8/package2/subpackage2/tests2.py::TestCase1",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (5, ["app8/package2"]),
            id="5",
        ),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_package_collapse(test_suite, labels, expected):
    """If all test cases in a test package are selected, "
    path is trimmed to the test method"""
    assert test_suite.find_tests(labels=labels) == expected


@pytest.mark.parametrize(
    "labels, expected",
    [
        pytest.param(
            [
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method1",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method2",
            ],
            (4, ["app8/package2/subpackage2"]),
            id="0",
        ),
        pytest.param(
            [
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (4, ["app8/package2/subpackage2"]),
            id="1",
        ),
        pytest.param(
            [
                "app8/package2/subpackage2/tests1.py::TestCase",
                "app8/package2/subpackage2/tests2.py::TestCase1",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (4, ["app8/package2/subpackage2"]),
            id="2",
        ),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_subpackage_collapse(test_suite, labels, expected):
    assert test_suite.find_tests(labels=labels) == expected


@pytest.mark.parametrize(
    "labels, expected",
    [
        pytest.param(
            [
                "app2.py::TestCase1::test_method",
                "app2.py::TestCase2::test_method1",
                "app2.py::TestCase2::test_method2",
            ],
            (3, ["app2.py"]),
            id="0",
        ),
        pytest.param(
            [
                "app2.py::TestCase1::test_method",
                "app2.py::TestCase2",
            ],
            (3, ["app2.py"]),
            id="1",
        ),
        pytest.param(
            [
                "app2.py::TestCase1",
                "app2.py::TestCase2",
            ],
            (3, ["app2.py"]),
            id="2",
        ),
        pytest.param(
            [
                "app4/tests1.py::TestCase::test_method",
                "app4/tests2.py::TestCase1::test_method",
                "app4/tests2.py::TestCase2::test_method1",
                "app4/tests2.py::TestCase2::test_method2",
            ],
            (4, ["app4"]),
            id="3",
        ),
        pytest.param(
            [
                "app4/tests1.py::TestCase::test_method",
                "app4/tests2.py::TestCase1::test_method",
                "app4/tests2.py::TestCase2",
            ],
            (4, ["app4"]),
            id="4",
        ),
        pytest.param(
            [
                "app4/tests1.py::TestCase::test_method",
                "app4/tests2.py::TestCase1",
                "app4/tests2.py::TestCase2",
            ],
            (4, ["app4"]),
            id="5",
        ),
        pytest.param(
            [
                "app4/tests1.py::TestCase::test_method",
                "app4/tests2.py",
            ],
            (4, ["app4"]),
            id="6",
        ),
        pytest.param(
            [
                "app4/tests1.py::TestCase",
                "app4/tests2.py",
            ],
            (4, ["app4"]),
            id="7",
        ),
        pytest.param(
            [
                "app4/tests1.py",
                "app4/tests2.py",
            ],
            (4, ["app4"]),
            id="8",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py::TestCase1::test_method",
                "app6/package2/tests2.py::TestCase2::test_method1",
                "app6/package2/tests2.py::TestCase2::test_method2",
            ],
            (5, ["app6"]),
            id="9",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py::TestCase1::test_method",
                "app6/package2/tests2.py::TestCase2",
            ],
            (5, ["app6"]),
            id="10",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py::TestCase1",
                "app6/package2/tests2.py::TestCase2",
            ],
            (5, ["app6"]),
            id="11",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py",
            ],
            (5, ["app6"]),
            id="12",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py::TestCase1",
                "app6/package2/tests2.py::TestCase2",
            ],
            (5, ["app6"]),
            id="13",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py::TestCase::test_method",
                "app6/package2/tests2.py",
            ],
            (5, ["app6"]),
            id="14",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py::TestCase",
                "app6/package2/tests2.py",
            ],
            (5, ["app6"]),
            id="15",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2/tests1.py",
                "app6/package2/tests2.py",
            ],
            (5, ["app6"]),
            id="16",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase::test_method",
                "app6/package2",
            ],
            (5, ["app6"]),
            id="17",
        ),
        pytest.param(
            [
                "app6/package1/tests.py::TestCase",
                "app6/package2",
            ],
            (5, ["app6"]),
            id="18",
        ),
        pytest.param(
            [
                "app6/package1/tests.py",
                "app6/package2",
            ],
            (5, ["app6"]),
            id="19",
        ),
        pytest.param(
            [
                "app6/package1",
                "app6/package2",
            ],
            (5, ["app6"]),
            id="20",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method1",
                "app8/package2/subpackage2/tests2.py::TestCase2::test_method2",
            ],
            (6, ["app8"]),
            id="21",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase1::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (6, ["app8"]),
            id="22",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py::TestCase1",
                "app8/package2/subpackage2/tests2.py::TestCase2",
            ],
            (6, ["app8"]),
            id="23",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py::TestCase::test_method",
                "app8/package2/subpackage2/tests2.py",
            ],
            (6, ["app8"]),
            id="24",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py::TestCase",
                "app8/package2/subpackage2/tests2.py",
            ],
            (6, ["app8"]),
            id="25",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2/tests1.py",
                "app8/package2/subpackage2/tests2.py",
            ],
            (6, ["app8"]),
            id="26",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase::test_method",
                "app8/package2/subpackage2",
            ],
            (6, ["app8"]),
            id="27",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py::TestCase",
                "app8/package2/subpackage2",
            ],
            (6, ["app8"]),
            id="28",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1/tests.py",
                "app8/package2/subpackage2",
            ],
            (6, ["app8"]),
            id="29",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2/subpackage1",
                "app8/package2/subpackage2",
            ],
            (6, ["app8"]),
            id="30",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase::test_method",
                "app8/package2",
            ],
            (6, ["app8"]),
            id="31",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py::TestCase",
                "app8/package2",
            ],
            (6, ["app8"]),
            id="32",
        ),
        pytest.param(
            [
                "app8/package1/subpackage/tests.py",
                "app8/package2",
            ],
            (6, ["app8"]),
            id="33",
        ),
        pytest.param(
            [
                "app8/package1/subpackage",
                "app8/package2",
            ],
            (6, ["app8"]),
            id="34",
        ),
        pytest.param(
            [
                "app8/package1",
                "app8/package2",
            ],
            (6, ["app8"]),
            id="35",
        ),
    ],
)
@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_app_collapse(test_suite, labels, expected):
    assert test_suite.find_tests(labels=labels) == expected
