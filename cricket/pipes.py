import sys
import time
import traceback
import unittest

from django.utils.unittest import result


class PipedTestResult(result.TestResult):
    """A test result class that can print test results in a machine-parseable format.

    Used by PipedTestRunner.
    """
    separator = '-' * 70

    def __init__(self, stream):
        super(PipedTestResult, self).__init__()
        self.stream = stream

    def startTest(self, test):
        super(PipedTestResult, self).startTest(test)
        parts = test.id().split('.')
        tests_index = parts.index('tests')
        self.stream.write(self.separator + '\n')
        self.stream.write('%s.%s.%s\nstart: %s\n' % (parts[tests_index - 1], parts[-2], parts[-1], time.time()))
        self.stream.flush()

    def addSuccess(self, test):
        super(PipedTestResult, self).addSuccess(test)
        self.stream.write("result: OK\nend: %s" % time.time())
        self.stream.write('\n')
        self.stream.flush()

    def addError(self, test, err):
        super(PipedTestResult, self).addError(test, err)
        self.stream.write('result: E\nend: %s\n' % time.time())
        self.stream.write('\n'.join(traceback.format_exception(*err)))
        self.stream.write('\n')
        self.stream.flush()

    def addFailure(self, test, err):
        super(PipedTestResult, self).addFailure(test, err)
        self.stream.write('result: F\nend: %s\n' % time.time())
        self.stream.write('\n'.join(traceback.format_exception(*err)))
        self.stream.write('\n')
        self.stream.flush()

    def addSkip(self, test, reason):
        super(PipedTestResult, self).addSkip(test, reason)
        self.stream.write("result: s\nend: %s\n" % time.time())
        self.stream.write(reason)
        self.stream.write('\n')
        self.stream.flush()

    def addExpectedFailure(self, test, err):
        super(PipedTestResult, self).addExpectedFailure(test, err)
        self.stream.write("result: x\nend: %s\n" % time.time())
        self.stream.write('\n'.join(traceback.format_exception(*err)))
        self.stream.write('\n')
        self.stream.flush()

    def addUnexpectedSuccess(self, test):
        super(PipedTestResult, self).addUnexpectedSuccess(test)
        self.stream.write("result: u\nend: %s" % time.time())
        self.stream.write('\n')
        self.stream.flush()


class PipedTestRunner(unittest.TextTestRunner):
    """A test runner class that displays results in machine-parseable format.

    It prints out the names of tests as they are run, errors as they
    occur, and a summary of the results at the end of the test run.
    """
    separator = '=' * 70

    def __init__(self, stream=sys.stdout):
        self.stream = stream

    def run(self, test):
        "Run the given test case or test suite."
        result = PipedTestResult(self.stream)

        test(result)

        self.stream.write(self.separator + '\n')
        self.stream.flush()

        return result
