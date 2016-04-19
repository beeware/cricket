import json
import subprocess
import sys
from threading import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

from cricket.events import EventSource
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


class Executor(EventSource):
    "A wrapper around the subprocess that executes tests."
    def __init__(self, project, count, labels):
        self.project = project

        self.proc = subprocess.Popen(
            self.project.execute_commandline(labels),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            bufsize=1,
            close_fds='posix' in sys.builtin_module_names
        )

        # Piped stdout/stderr reads are blocking; therefore, we need to
        # do all our readline calls in a background thread, and use a
        # queue object to store lines that have been read.
        self.stdout = Queue()
        t = Thread(target=enqueue_output, args=(self.proc.stdout, self.stdout))
        t.daemon = True
        t.start()

        self.stderr = Queue()
        t = Thread(target=enqueue_output, args=(self.proc.stderr, self.stderr))
        t.daemon = True
        t.start()

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

        # The total count of tests under execution
        self.total_count = count

        # The count of tests that have been executed.
        self.completed_count = 0

        # The count of specific test results.
        self.result_count = {}

    @property
    def is_running(self):
        "Return True if this runner currently running."
        return self.proc.poll() is None

    @property
    def any_failed(self):
        return sum(self.result_count.get(state, 0) for state in TestMethod.FAILING_STATES)

    def terminate(self):
        "Stop the executor."
        self.proc.terminate()

    def poll(self):
        "Poll the runner looking for new test output"
        stopped = False
        finished = False

        # Read from stdout, building a buffer.
        lines = []
        try:
            while True:
                lines.append(self.stdout.get(block=False))
        except Empty:
            # queue.get() raises an exception when the queue is empty.
            # This means there is no more output to consume at this time.
            pass

        # Read from stderr, building a buffer.
        try:
            while True:
                self.error_buffer.append(self.stderr.get(block=False))
        except Empty:
            # queue.get() raises an exception when the queue is empty.
            # This means there is no more output to consume at this time.
            pass

        # Check to see if the subprocess is still running.
        # If it isn't, raise an error.
        if self.proc is None:
            stopped = True
        elif self.proc.poll() is not None:
            stopped = True

        # Process all the full lines that are available
        for line in lines:
            # Look for a separator.
            if line in (PipedTestResult.RESULT_SEPARATOR, PipedTestRunner.START_TEST_RESULTS, PipedTestRunner.END_TEST_RESULTS):
                if self.buffer is None:
                    # Preamble is finished. Set up the line buffer.
                    self.buffer = []
                else:
                    # Start of new test result; record the last result
                    # Then, work out what content goes where.
                    pre = json.loads(self.buffer[0])
                    post = json.loads(self.buffer[1])

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

                    # Increase the count of executed tests
                    self.completed_count = self.completed_count + 1

                    # Get the start and end times for the test
                    start_time = float(pre['start_time'])
                    end_time = float(post['end_time'])

                    self.current_test.description = post['description']

                    self.current_test.set_result(
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

                    # Notify the display to update.
                    self.emit('test_end', test_path=self.current_test.path, result=status, remaining_time=remaining)

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
                if self.buffer is None:
                    # Suite isn't running yet - just display the output
                    # as a status update line.
                    self.emit('test_status_update', update=line)
                else:
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
                        except ValueError:
                            self.emit('suit_end')
                            return True
                        self.current_test = self.project.confirm_exists(pre['path'])
                        self.emit('test_start', test_path=pre['path'])
        # If we're not finished, requeue the event.
        if finished:
            if self.error_buffer:
                self.emit('suite_end', error='\n'.join(self.error_buffer))
            else:
                self.emit('suite_end')
            return False

        elif stopped:
            # Suite has stopped producing output.
            if self.error_buffer:
                self.emit('suite_error', error=b'\n'.join(self.error_buffer))
            else:
                self.emit('suite_error', error='Test output ended unexpectedly')

            # Suite has finished; don't requeue
            return False

        else:
            # Still running - requeue event.
            return True
