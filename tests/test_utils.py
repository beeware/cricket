import pytest

from cricket.executor import parse_status_and_error
from cricket.model import TestMethod as CTMethod


@pytest.mark.parametrize(
    ("error_code", "expected_status"),
    [
        ("OK", CTMethod.STATUS_PASS),
        ("s", CTMethod.STATUS_SKIP),
        ("F", CTMethod.STATUS_FAIL),
        ("x", CTMethod.STATUS_EXPECTED_FAIL),
        ("u", CTMethod.STATUS_UNEXPECTED_SUCCESS),
        ("E", CTMethod.STATUS_ERROR),
    ],
)
def test_status_returned(error_code, expected_status):
    status, _error = parse_status_and_error(
        {
            "end_time": 1500000000,
            "status": error_code,
            "description": "Some Test",
            "error": "",
            "output": "",
        }
    )
    assert status == expected_status


@pytest.mark.parametrize("error_code", ["s", "F", "x", "E"])
def test_error_returned(error_code):
    sample_error = "something broke"
    _status, error = parse_status_and_error(
        {
            "end_time": 1500000000,
            "status": error_code,
            "description": "Some Test",
            "error": sample_error,
            "output": "",
        }
    )
    assert sample_error in error


@pytest.mark.parametrize("error_code", ["OK", "u"])
def test_error_not_returned(error_code):
    sample_error = "something broke"
    _status, error = parse_status_and_error(
        {
            "end_time": 1500000000,
            "status": error_code,
            "description": "Some Test",
            "error": sample_error,
            "output": "",
        }
    )
    assert error is None
