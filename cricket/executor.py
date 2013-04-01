import fcntl
import os
import subprocess

from cricket.events import EventSource
from cricket.model import TestMethod
from cricket.pipes import PipedTestResult, PipedTestRunner


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
        )

        # Probably only works on UNIX-alikes.
        # Windows users should feel free to suggest an alternative.
        fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        # Data storage for test results.
        #  - lines is an accumulator of extra test output.
        #    If lines is None, there's no test currently under execution

        # The TestMethod object currently under execution.
        self.current_test = None

        # An accumulator of ouput from the tests. If buffer is None,
        # then the test suite isn't currently running - it's in suite
        # setup/teardown.
        self.buffer = None

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

    def terminate(self):
        "Stop the executor."
        self.proc.terminate()

    def _split_content(self):
        "Split separated content into it's parts"
        content = []
        all_content = []
        for line in self.buffer[3:]:
            if line == PipedTestResult.content_separator:
                all_content.append('\n'.join(content))
                content = []
            else:
                content.append(line)

        # Store everything in the last content block
        if content:
            all_content.append('\n'.join(content))

        return all_content

    def poll(self):
        "Poll the runner looking for new test output"
        stopped = False
        finished = False

        # Read from stdout, building a buffer.
        lines = []
        try:
            chunk = self.proc.stdout.read()
            if chunk != '':
                # If the last character in the chunk is a newline, drop it
                # because it will cause an empty line to be registered.
                if chunk[-1] == '\n':
                    chunk = chunk[:-1]
                lines = chunk.split('\n')
        except IOError:
            # If there's no data available, an IOError will be raised.
            pass
        except AttributeError:
            # If the process has been stopped, there won't be a pipe anymore.
            pass

        # Read from stderr, building a buffer.
        errors = []
        try:
            chunk = self.proc.stderr.read()
            if chunk != '':
                # If the last character in the chunk is a newline, drop it
                # because it will cause an empty line to be registered.
                if chunk[-1] == '\n':
                    chunk = chunk[:-1]
                errors = chunk.split('\n')
        except IOError:
            # If there's no data available, an IOError will be raised.
            pass
        except AttributeError:
            # If the process has been stopped, there won't be a pipe anymore.
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
            if line in (PipedTestResult.result_separator, PipedTestRunner.separator):
                if self.buffer is None:
                    # Preamble is finished. Set up the line buffer.
                    self.buffer = []
                else:
                    # Start of new test result; record the last result
                    content = self._split_content()
                    # Then, work out what content goes where.
                    if self.buffer[1] == 'result: OK':
                        status = TestMethod.STATUS_PASS
                        description = content[0]
                        error = None
                    elif self.buffer[1] == 'result: s':
                        status = TestMethod.STATUS_SKIP
                        description = content[0]
                        error = 'Skipped: ' + content[1]
                    elif self.buffer[1] == 'result: F':
                        status = TestMethod.STATUS_FAIL
                        description = content[0]
                        error = content[1]
                    elif self.buffer[1] == 'result: x':
                        status = TestMethod.STATUS_EXPECTED_FAIL
                        description = content[0]
                        error = content[1]
                    elif self.buffer[1] == 'result: u':
                        status = TestMethod.STATUS_UNEXPECTED_SUCCESS
                        description = content[0]
                        error = None
                    elif self.buffer[1] == 'result: E':
                        status = TestMethod.STATUS_ERROR
                        description = content[0]
                        error = content[1]

                    # Increase the count of executed tests
                    self.completed_count = self.completed_count + 1

                    # Get the start and end times for the test
                    start_time = self.buffer[0][7:]
                    end_time = self.buffer[2][5:]

                    self.current_test.description = description
                    self.current_test.set_result(
                        status=status,
                        output='' if self.completed_count % 2 == 0 else 'This is the output\nNo, this is the output',
                        error=error,
                        duration=float(end_time) - float(start_time),
                    )

                    # Work out how long the suite has left to run (approximately)
                    if self.start_time is None:
                        self.start_time = start_time
                    total_duration = float(end_time) - float(self.start_time)
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
                    self.emit('test_end', test_path=self.current_test.path, remaining_time=remaining)

                    # Clear the decks for the next test.
                    self.current_test = None
                    self.buffer = []

                    if line == PipedTestRunner.separator:
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
                    if self.current_test is None:
                        # No active test; first line tells us which test is running.
                        self.current_test = self.project.confirm_exists(line)
                        self.emit('test_start', test_path=line)
                    else:
                        # Active test; just accumulate the buffer.
                        self.buffer.append(line)

        # If we're not finished, requeue the event.
        if finished:
            self.emit('suite_end')
            return False

        elif stopped:
            # Suite has stopped producing output.
            if errors:
                self.emit('suite_error', error='\n'.join(errors))
            else:
                self.emit('suite_error', error='Test output ended unexpectedly')

            # Suite has finished; don't requeue
            return False

        else:
            # Still running - requeue event.
            return True
