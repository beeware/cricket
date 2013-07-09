from __future__ import absolute_import

import json
from StringIO import StringIO
import sys
import time
import traceback
import unittest


def trim_docstring(docstring):
    """Trim leading spaces in docstring indentation.

    Algorithm taken from PEP 257:
        http://www.python.org/dev/peps/pep-0257/#id20
    """
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


class PipedTestResult(unittest.result.TestResult):
    """A test result class that can print test results in a machine-parseable format.

    Used by PipedTestRunner.
    """
    RESULT_SEPARATOR = '\x1f'  # ASCII US (Unit Separator)

    def __init__(self, stream, use_old_discovery=True):
        super(PipedTestResult, self).__init__()
        self.stream = stream
        self.use_old_discovery = use_old_discovery
        self._first = True

    def description(self, test):
        if test._testMethodDoc:
            return trim_docstring(test._testMethodDoc)
        else:
            return 'No description'

    def startTest(self, test):
        super(PipedTestResult, self).startTest(test)

        # # Create a clean buffer for stdout content.
        self._stdout = StringIO()
        sys.stdout = self._stdout

        if self.use_old_discovery:
            parts = test.id().split('.')
            tests_index = parts.index('tests')
            path = '%s.%s.%s' % (parts[tests_index - 1], parts[-2], parts[-1])
        else:
            path = test.id()

        body = {
            'path': path,
            'start_time': time.time()
        }
        if self._first:
            self.stream.write(PipedTestRunner.START_TEST_RESULTS + '\n')
            self._first = False
        else:
            self.stream.write(self.RESULT_SEPARATOR + '\n')
        self.stream.write('%s\n' % json.dumps(body))
        self.stream.flush()

    def addSuccess(self, test):
        super(PipedTestResult, self).addSuccess(test)
        body = {
            'status': 'OK',
            'end_time': time.time(),
            'description': self.description(test),
            'output': self._stdout.getvalue(),
        }
        self.stream.write('%s\n' % json.dumps(body))
        self.stream.flush()

    def addError(self, test, err):
        super(PipedTestResult, self).addError(test, err)
        body = {
            'status': 'E',
            'end_time': time.time(),
            'description': self.description(test),
            'error': '\n'.join(traceback.format_exception(*err)),
            'output': self._stdout.getvalue(),
        }
        self.stream.write('%s\n' % json.dumps(body))
        self.stream.flush()

    def addFailure(self, test, err):
        super(PipedTestResult, self).addFailure(test, err)
        body = {
            'status': 'F',
            'end_time': time.time(),
            'description': self.description(test),
            'error': '\n'.join(traceback.format_exception(*err)),
            'output': self._stdout.getvalue(),
        }
        self.stream.write('%s\n' % json.dumps(body))
        self.stream.flush()

    def addSkip(self, test, reason):
        super(PipedTestResult, self).addSkip(test, reason)
        body = {
            'status': 's',
            'end_time': time.time(),
            'description': self.description(test),
            'error': reason,
            'output': self._stdout.getvalue(),
        }
        self.stream.write('%s\n' % json.dumps(body))
        self.stream.flush()

    def addExpectedFailure(self, test, err):
        super(PipedTestResult, self).addExpectedFailure(test, err)
        body = {
            'status': 'x',
            'end_time': time.time(),
            'description': self.description(test),
            'error': '\n'.join(traceback.format_exception(*err)),
            'output': self._stdout.getvalue(),
        }
        self.stream.write('%s\n' % json.dumps(body))
        self.stream.flush()

    def addUnexpectedSuccess(self, test):
        super(PipedTestResult, self).addUnexpectedSuccess(test)
        body = {
            'status': 'u',
            'end_time': time.time(),
            'description': self.description(test),
            'output': self._stdout.getvalue(),
        }
        self.stream.write('%s\n' % json.dumps(body))
        self.stream.flush()


class PipedTestRunner(unittest.TextTestRunner):
    """A test runner class that displays results in machine-parseable format.

    It prints out the names of tests as they are run, errors as they
    occur, and a summary of the results at the end of the test run.
    """
    START_TEST_RESULTS = '\x02'  # ASCII STX (Start of Text)
    END_TEST_RESULTS = '\x03'    # ASCII ETX (End of Text)

    def __init__(self, stream=sys.stdout, use_old_discovery=False):
        self.stream = stream
        self.use_old_discovery = use_old_discovery

    def run(self, test):
        "Run the given test case or test suite."
        # Remeber stdout reference so it can be restored later
        old_stdout = sys.stdout

        # Create the result pipe, and run the tests with it.
        result = PipedTestResult(self.stream, self.use_old_discovery)
        test(result)

        # Report end of test run
        self.stream.write(self.END_TEST_RESULTS + '\n')
        self.stream.flush()

        # Restore the stdout reference
        sys.stdout = old_stdout

        return result
