import pytest


def test_passing_item():
    pass


@pytest.mark.skip(reason='tra-la-la')
def test_skipped_item():
    pass


def test_failing_item():
    assert False, 'Failed!'


def test_assertion_item():
    assert 1 == 2, 'Who are you kidding?'


def test_error_item():
    raise Exception("this is really bad")


@pytest.mark.xfail
def test_xfailing_item():
    assert False,  'This is a known bad'


@pytest.mark.xfail
def test_upassed_item():
    pass


@pytest.mark.xfail(strict=True)
def test_upassed_strict_item():
    pass
