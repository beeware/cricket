import unittest
from cricket.executor import parse_status_and_error
from cricket.model import TestMethod


class TestErrorAndStatus(unittest.TestCase):
    def test_status_returned(self):
        expected_error_definitions = {
            'OK': TestMethod.STATUS_PASS,
            's': TestMethod.STATUS_SKIP,
            'F': TestMethod.STATUS_FAIL,
            'x': TestMethod.STATUS_EXPECTED_FAIL,
            'u': TestMethod.STATUS_UNEXPECTED_SUCCESS,
            'E': TestMethod.STATUS_ERROR,
        }
        for error_code, expected_status in expected_error_definitions.items():
            with self.subTest('error code ' + error_code):
                status, error = parse_status_and_error({
                    'end_time': 1500000000,
                    'status': error_code,
                    'description': 'Some Test',
                    'error': '',
                    'output': '',
                })
                self.assertEqual(status, expected_status)

    def test_error_returned(self):
        sample_error = 'something broke'
        expect_error_text = ['s', 'F', 'x', 'E']
        for error_code in expect_error_text:
            with self.subTest('error text returned for code ' + error_code):
                status, error = parse_status_and_error({
                    'end_time': 1500000000,
                    'status': error_code,
                    'description': 'Some Test',
                    'error': sample_error,
                    'output': '',
                })
                self.assertIn(sample_error, error)

    def test_error_not_returned(self):
        sample_error = 'something broke'
        expect_no_error_text = ['OK', 'u']
        for error_code in expect_no_error_text:
            with self.subTest('error is none when error code is ' + error_code):
                status, error = parse_status_and_error({
                    'end_time': 1500000000,
                    'status': error_code,
                    'description': 'Some Test',
                    'error': sample_error,
                    'output': '',
                })
                self.assertIsNone(error)
