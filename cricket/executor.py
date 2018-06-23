import asyncio
import json
import subprocess
import sys
from threading import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

from cricket.model import TestMethod
from cricket.pipes import PipedTestResult, PipedTestRunner


def enqueue_output(out, queue):
    """A utility method for consuming piped output from a subprocess.

    Reads content from `out` one line at a time, and puts it onto
    queue for consumption in a separate thread.
    """
    for line in iter(out.readline, b''):
        queue.put(line.strip().decode('utf-8'))
    out.close()


def parse_status_and_error(post):
    if post['status'] == 'OK':
        status = TestMethod.STATUS_PASS
        error = None
    elif post['status'] == 's':
        status = TestMethod.STATUS_SKIP
        error = 'Skipped: ' + post.get('error')
    elif post['status'] == 'F':
        status = TestMethod.STATUS_FAIL
        error = post.get('error')
    elif post['status'] == 'x':
        status = TestMethod.STATUS_EXPECTED_FAIL
        error = post.get('error')
    elif post['status'] == 'u':
        status = TestMethod.STATUS_UNEXPECTED_SUCCESS
        error = None
    elif post['status'] == 'E':
        status = TestMethod.STATUS_ERROR
        error = post.get('error')

    return status, error


class Executor:
    "A wrapper around the subprocess that executes tests."
    def __init__(self, test_suite, display=None):
        self.test_suite = test_suite
        self.display = display

        # The TestMethod object currently under execution.
        self.current_test = None

        # An accumulator of ouput from the tests. If buffer is None,
        # then the test suite isn't currently running - it's in suite
        # setup/teardown.
        self.buffer = None

        # An accumulator for error output from the tests.
        self.error_buffer = []

        # The timestamp when current_test started
        self.start_time = None

        # The count of tests that have been executed.
        self.completed_count = 0

        # The count of specific test results.
        self.result_count = {}

    async def run(self, count, labels):
        self.total_count = count

        self.proc = await asyncio.create_subprocess_shell(
            ' '.join(self.test_suite.execute_commandline(labels)),
            stdin=None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        line = await self.proc.stdout.readline()
        while line:
            line = line.strip().decode('utf-8')
            if line in {
                            PipedTestResult.RESULT_SEPARATOR,
                            PipedTestRunner.START_TEST_RESULTS,
                            PipedTestRunner.END_TEST_RESULTS,
                        }:
                if self.buffer is None:
                    # Preamble is finished. Set up the line buffer.
                    self.buffer = []
                else:
                    # Start of new test result; record the last result
                    # Then, work out what content goes where.
                    pre = json.loads(self.buffer[0])
                    if len(self.buffer) == 2:
                        # No subtests are present, or only one subtest
                        post = json.loads(self.buffer[1])
                        status, error = parse_status_and_error(post)
                    else:
                        # We have subtests; capture the most important status (until we can capture all the statuses)
                        status = TestMethod.STATUS_PASS  # Assume pass until told otherwise
                        error = ''
                        for line_num in range(1, len(self.buffer)):
                            post = json.loads(self.buffer[line_num])
                            subtest_status, subtest_error = parse_status_and_error(post)
                            if subtest_status > status:
                                status = subtest_status
                            if subtest_error:
                                error += subtest_error + '\n\n'

                    # Increase the count of executed tests
                    self.completed_count = self.completed_count + 1

                    # Get the start and end times for the test
                    start_time = float(pre['start_time'])
                    end_time = float(post['end_time'])

                    self.current_test.set_result(
                        description=post['description'],
                        status=status,
                        output=post.get('output'),
                        error=error,
                        duration=end_time - start_time,
                    )

                    # Work out how long the suite has left to run (approximately)
                    if self.start_time is None:
                        self.start_time = start_time
                    total_duration = end_time - self.start_time
                    time_per_test = total_duration / self.completed_count
                    remaining_time = (self.total_count - self.completed_count) * time_per_test
                    if remaining_time > 4800:
                        remaining = '%s hours' % int(remaining_time / 2400)
                    elif remaining_time > 2400:
                        remaining = '%s hour' % int(remaining_time / 2400)
                    elif remaining_time > 120:
                        remaining = '%s mins' % int(remaining_time / 60)
                    elif remaining_time > 60:
                        remaining = '%s min' % int(remaining_time / 60)
                    else:
                        remaining = '%ss' % int(remaining_time)

                    # Update test result counts
                    self.result_count.setdefault(status, 0)
                    self.result_count[status] = self.result_count[status] + 1

                    # Update the display
                    if self.display:
                        self.display.executor_test_end(
                            test_path=self.current_test.path,
                            result=status,
                            remaining_time=remaining
                        )

                    # Clear the decks for the next test.
                    self.current_test = None
                    self.buffer = []

                    if line == PipedTestRunner.END_TEST_RESULTS:
                        # End of test execution.
                        # Mark the runner as finished, and move back
                        # to a pre-test state in the results.
                        finished = True
                        self.buffer = None

            else:
                # Not a separator line, so it's actual content.
                if self.buffer is not None:
                    # Suite is running - have we got an active test?
                    # Doctest (and some other tools) output invisible escape sequences.
                    # Strip these if they exist.
                    if line.startswith('\x1b'):
                        line = line[line.find('{'):]

                    # Store the cleaned buffer
                    self.buffer.append(line)

                    # If we don't have an currently active test, this line will
                    # contain the path for the test.
                    if self.current_test is None:
                        try:
                            # No active test; first line tells us which test is running.
                            pre = json.loads(line)
                            self.current_test = self.test_suite.put_test(pre['path'])

                            # Update the display
                            if self.display:
                                self.display.executor_test_start(
                                    test_path=self.current_test.path,
                                )

                        except ValueError:
                            self.current_test = None
                # else:
                #     # We haven't started the suite yet; we're still collecting the preamble
            line = await self.proc.stdout.readline()

        # Update the display
        if self.display:
            self.display.executor_suite_end()

        # elif stopped:
        #     # Suite has stopped producing output.
        #     if self.error_buffer:
        #         self.emit('suite_error', error='\n'.join(self.error_buffer))
        #     else:
        #         self.emit('suite_error', error='Test output ended unexpectedly')

    async def terminate(self):
        "Stop the executor."
        self.proc.terminate()
        await self.proc.wait()

    @property
    def any_failed(self):
        return sum(self.result_count.get(state, 0) for state in TestMethod.FAILING_STATES)
