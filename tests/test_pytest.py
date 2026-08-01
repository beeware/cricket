import json
import os
import subprocess
import sys
from pathlib import Path

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

SAMPLE_DIR = Path(__file__).parent.parent / "sample"


@pytest.fixture
def sample_suite():
    _cwd = os.getcwd()
    os.chdir(SAMPLE_DIR)
    yield
    os.chdir(_cwd)


@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_discovery():
    suite = PTSuite()
    runner = subprocess.run(
        suite.discover_commandline(),
        stdin=None,
        capture_output=True,
        shell=False,
        check=True,
        cwd=SAMPLE_DIR,
    )

    found = set()
    for line in runner.stdout.decode("utf-8").split("\n"):
        if line:
            found.add(line)

    assert found == {
        "test_root.py::test_at_root",
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff",
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_things",
        "tests/submodule/test_more_nesting.py::test_stuff",
        "tests/submodule/test_more_nesting.py::test_things",
        "tests/submodule/test_nesting.py::test_stuff",
        "tests/submodule/test_nesting.py::test_things",
        "tests/test_outcomes.py::test_assertion_item",
        "tests/test_outcomes.py::test_error_item",
        "tests/test_outcomes.py::test_failing_item",
        "tests/test_outcomes.py::test_upassed_item",
        "tests/test_outcomes.py::test_upassed_strict_item",
        "tests/test_outcomes.py::test_xfailing_item",
        "tests/test_outcomes.py::test_passing_item",
        "tests/test_outcomes.py::test_skipped_item",
        "tests/test_unusual.py::test_item_output",
        "tests/test_unusual.py::test_slow_0",
        "tests/test_unusual.py::test_slow_1",
        "tests/test_unusual.py::test_slow_2",
        "tests/test_unusual.py::test_slow_3",
        "tests/test_unusual.py::test_slow_4",
        "tests/test_unusual.py::test_slow_5",
        "tests/test_unusual.py::test_slow_6",
        "tests/test_unusual.py::test_slow_7",
        "tests/test_unusual.py::test_slow_8",
        "tests/test_unusual.py::test_slow_9",
        "tests/units/submodule/test_more_unit_tests.py::MoreNestedTests::test_stuff",
        "tests/units/submodule/test_more_unit_tests.py::MoreNestedTests::test_things",
        "tests/units/test_outcomes.py::BadTests::test_assertion_item",
        "tests/units/test_outcomes.py::BadTests::test_error_item",
        "tests/units/test_outcomes.py::BadTests::test_failing_item",
        "tests/units/test_outcomes.py::BadTests::test_subtests",
        "tests/units/test_outcomes.py::BadTests::test_upassed_item",
        "tests/units/test_outcomes.py::BadTests::test_xfailing_item",
        "tests/units/test_outcomes.py::GoodTests::test_passing_item",
        "tests/units/test_outcomes.py::GoodTests::test_skipped_item",
        "tests/units/test_unit_tests.py::NestedTests::test_stuff",
        "tests/units/test_unit_tests.py::NestedTests::test_things",
        "tests/units/test_unit_tests.py::OtherNestedTests::test_stuff",
        "tests/units/test_unit_tests.py::OtherNestedTests::test_things",
        "tests/units/test_unusual.py::UnusualTests::test_item_output",
        "tests/units/test_unusual.py::UnusualTests::test_slow_0",
        "tests/units/test_unusual.py::UnusualTests::test_slow_1",
        "tests/units/test_unusual.py::UnusualTests::test_slow_2",
        "tests/units/test_unusual.py::UnusualTests::test_slow_3",
        "tests/units/test_unusual.py::UnusualTests::test_slow_4",
        "tests/units/test_unusual.py::UnusualTests::test_slow_5",
        "tests/units/test_unusual.py::UnusualTests::test_slow_6",
        "tests/units/test_unusual.py::UnusualTests::test_slow_7",
        "tests/units/test_unusual.py::UnusualTests::test_slow_8",
        "tests/units/test_unusual.py::UnusualTests::test_slow_9",
    }


def execute(*args, success=True):
    suite = PTSuite()
    runner = subprocess.run(
        suite.execute_commandline(list(args)),
        stdin=None,
        capture_output=True,
        shell=False,
        check=False,
    )

    if success:
        assert runner.returncode == 0
    else:
        assert runner.returncode != 0

    found = set()
    results = {}
    for line in runner.stdout.decode("utf-8").split("\n"):
        try:
            payload = json.loads(line)
            if "path" in payload:
                found.add(payload["path"])
            elif "status" in payload:
                count = results.setdefault(payload["status"], 0)
                results[payload["status"]] = count + 1
            else:
                pytest.fail(f"Unknown payload line: '{payload}'")
        except json.JSONDecodeError:
            pass

    return found, results


def test_run_all(sample_suite):
    found, results = execute(success=False)

    assert found == {
        "test_root.py::test_at_root",
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff",
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_things",
        "tests/submodule/test_more_nesting.py::test_stuff",
        "tests/submodule/test_more_nesting.py::test_things",
        "tests/submodule/test_nesting.py::test_stuff",
        "tests/submodule/test_nesting.py::test_things",
        "tests/test_outcomes.py::test_assertion_item",
        "tests/test_outcomes.py::test_error_item",
        "tests/test_outcomes.py::test_failing_item",
        "tests/test_outcomes.py::test_upassed_item",
        "tests/test_outcomes.py::test_upassed_strict_item",
        "tests/test_outcomes.py::test_xfailing_item",
        "tests/test_outcomes.py::test_passing_item",
        "tests/test_outcomes.py::test_skipped_item",
        "tests/test_unusual.py::test_item_output",
        "tests/test_unusual.py::test_slow_0",
        "tests/test_unusual.py::test_slow_1",
        "tests/test_unusual.py::test_slow_2",
        "tests/test_unusual.py::test_slow_3",
        "tests/test_unusual.py::test_slow_4",
        "tests/test_unusual.py::test_slow_5",
        "tests/test_unusual.py::test_slow_6",
        "tests/test_unusual.py::test_slow_7",
        "tests/test_unusual.py::test_slow_8",
        "tests/test_unusual.py::test_slow_9",
        "tests/units/submodule/test_more_unit_tests.py::MoreNestedTests::test_stuff",
        "tests/units/submodule/test_more_unit_tests.py::MoreNestedTests::test_things",
        "tests/units/test_outcomes.py::BadTests::test_assertion_item",
        "tests/units/test_outcomes.py::BadTests::test_error_item",
        "tests/units/test_outcomes.py::BadTests::test_failing_item",
        "tests/units/test_outcomes.py::BadTests::test_subtests",
        "tests/units/test_outcomes.py::BadTests::test_upassed_item",
        "tests/units/test_outcomes.py::BadTests::test_xfailing_item",
        "tests/units/test_outcomes.py::GoodTests::test_passing_item",
        "tests/units/test_outcomes.py::GoodTests::test_skipped_item",
        "tests/units/test_unit_tests.py::NestedTests::test_stuff",
        "tests/units/test_unit_tests.py::NestedTests::test_things",
        "tests/units/test_unit_tests.py::OtherNestedTests::test_stuff",
        "tests/units/test_unit_tests.py::OtherNestedTests::test_things",
        "tests/units/test_unusual.py::UnusualTests::test_item_output",
        "tests/units/test_unusual.py::UnusualTests::test_slow_0",
        "tests/units/test_unusual.py::UnusualTests::test_slow_1",
        "tests/units/test_unusual.py::UnusualTests::test_slow_2",
        "tests/units/test_unusual.py::UnusualTests::test_slow_3",
        "tests/units/test_unusual.py::UnusualTests::test_slow_4",
        "tests/units/test_unusual.py::UnusualTests::test_slow_5",
        "tests/units/test_unusual.py::UnusualTests::test_slow_6",
        "tests/units/test_unusual.py::UnusualTests::test_slow_7",
        "tests/units/test_unusual.py::UnusualTests::test_slow_8",
        "tests/units/test_unusual.py::UnusualTests::test_slow_9",
    }

    assert results == {"OK": 39, "F": 4, "E": 3, "x": 2, "u": 1, "s": 2}


def test_single_test_method(sample_suite):
    found, results = execute(
        "tests/submodule/test_nesting.py::test_stuff",
    )

    assert found == {
        "tests/submodule/test_nesting.py::test_stuff",
    }

    assert results == {"OK": 1}


def test_multiple_test_methods(sample_suite):
    found, results = execute(
        "tests/submodule/test_nesting.py::test_stuff",
        "tests/submodule/test_nesting.py::test_things",
    )

    assert found == {
        "tests/submodule/test_nesting.py::test_stuff",
        "tests/submodule/test_nesting.py::test_things",
    }

    assert results == {"OK": 2}


def test_module(sample_suite):
    found, results = execute(
        "tests/submodule/test_nesting.py",
    )

    assert found == {
        "tests/submodule/test_nesting.py::test_stuff",
        "tests/submodule/test_nesting.py::test_things",
    }

    assert results == {"OK": 2}


def test_submodules(sample_suite):
    found, results = execute(
        "tests/submodule",
    )

    assert found == {
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff",
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_things",
        "tests/submodule/test_more_nesting.py::test_stuff",
        "tests/submodule/test_more_nesting.py::test_things",
        "tests/submodule/test_nesting.py::test_stuff",
        "tests/submodule/test_nesting.py::test_things",
    }

    assert results == {"OK": 6}


def test_single_root_test_method(sample_suite):
    found, results = execute(
        "test_root.py::test_at_root",
    )

    assert found == {
        "test_root.py::test_at_root",
    }

    assert results == {"OK": 1}


def test_single_root_test_file(sample_suite):
    found, results = execute("test_root.py")

    assert found == {
        "test_root.py::test_at_root",
    }

    assert results == {"OK": 1}


# PyTest doesn't filter test naming overlaps.
# This is (arguably) a bug in PyTest itself.
@pytest.mark.xfail
def test_overlap(sample_suite):
    found, results = execute(
        "tests/submodule/test_nesting.py",
        "tests/submodule/test_nesting.py::test_things",
    )

    assert found == {
        "tests/submodule/test_nesting.py::test_stuff",
        "tests/submodule/test_nesting.py::test_things",
    }

    assert results == {"OK": 2}


def test_mixed(sample_suite):
    found, results = execute(
        "tests/submodule/subsubmodule/test_deep_nesting.py",
        "tests/submodule/test_nesting.py::test_stuff",
    )

    assert found == {
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff",
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_things",
        "tests/submodule/test_nesting.py::test_stuff",
    }

    assert results == {"OK": 3}


def test_split_root(sample_suite):
    suite = PTSuite()
    parts = suite.split_test_id("tests.py::test_stuff")

    assert parts == [
        (CTModule, "tests.py"),
        (CTMethod, "test_stuff"),
    ]


def test_split_root_unittest(sample_suite):
    suite = PTSuite()
    parts = suite.split_test_id("tests.py::TestClass::test_stuff")

    assert parts == [
        (CTModule, "tests.py"),
        (CTCase, "TestClass"),
        (CTMethod, "test_stuff"),
    ]


@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_split_minimal(sample_suite):
    suite = PTSuite()
    parts = suite.split_test_id("tests/test_module.py::test_stuff")

    assert parts == [
        (CTModule, "tests"),
        (CTModule, "test_module.py"),
        (CTMethod, "test_stuff"),
    ]


@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_split_unittest(sample_suite):
    suite = PTSuite()
    parts = suite.split_test_id("tests/test_module.py::TestClass::test_stuff")

    assert parts == [
        (CTModule, "tests"),
        (CTModule, "test_module.py"),
        (CTCase, "TestClass"),
        (CTMethod, "test_stuff"),
    ]


@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_split_long(sample_suite):
    suite = PTSuite()
    parts = suite.split_test_id(
        "tests/submodule/subsubmodule/test_deep_nesting.py::test_stuff"
    )

    assert parts == [
        (CTModule, "tests"),
        (CTModule, "submodule"),
        (CTModule, "subsubmodule"),
        (CTModule, "test_deep_nesting.py"),
        (CTMethod, "test_stuff"),
    ]


def test_join_method_unittest(sample_suite):
    suite = PTSuite()
    parent = CTCase(None, "tests/module.py::TestClass", "TestClass")
    assert (
        suite.join_path(parent, CTMethod, "test_stuff")
        == "tests/module.py::TestClass::test_stuff"
    )


def test_join_method(sample_suite):
    suite = PTSuite()
    parent = CTCase(None, "tests/module.py", "module.py")
    assert (
        suite.join_path(parent, CTMethod, "test_stuff") == "tests/module.py::test_stuff"
    )


def test_join_case(sample_suite):
    suite = PTSuite()
    parent = CTModule(None, "tests/module.py", "module.py")
    assert suite.join_path(parent, CTCase, "TestClass") == "tests/module.py::TestClass"


@pytest.mark.skipif(sys.platform == "win32", "Test has problems on Windows")
def test_join_module(sample_suite):
    suite = PTSuite()
    parent = CTModule(None, "tests", "tests")
    assert suite.join_path(parent, CTModule, "module.py") == "tests/module.py"


def test_join_submodule(sample_suite):
    suite = PTSuite()
    assert suite.join_path(suite, CTModule, "tests") == "tests"
