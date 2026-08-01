import pytest


def test_passing_item():
    pass


@pytest.mark.skip(reason="tra-la-la")
def test_skipped_item():
    pass


def test_failing_item():
    raise AssertionError("Failed!")


def test_assertion_item():
    value1 = 1
    assert value1 == 2, "Who are you kidding?"


def test_error_item():
    raise ValueError("this is really bad")


@pytest.mark.xfail
def test_xfailing_item():
    raise AssertionError("This is a known bad")


@pytest.mark.xfail
def test_upassed_item():
    pass


@pytest.mark.xfail(strict=True)
def test_upassed_strict_item():
    pass
