"""A module containing a visual representation of the testModule.

This is the "View" of the MVC world.
"""

import os
import sys
import subprocess
import webbrowser

import toga
from toga.style import Pack
from toga.style.pack import RIGHT, LEFT, CENTER, ROW, COLUMN, VISIBLE, HIDDEN
from toga.font import BOLD, SANS_SERIF

# Check for the existence of coverage and duvet
try:
    import coverage
    try:
        import duvet
    except ImportError:
        duvet = None
except ImportError:
    coverage = None
    duvet = None

from cricket.model import TestMethod, TestSuiteProblems
from cricket.executor import Executor
from cricket.dialogs import FailedTestDialog, TestLoadErrorDialog, IgnorableTestLoadErrorDialog


class Cricket(toga.App):
    def startup(self):
        '''
        -----------------------------------------------------
        | main button toolbar                               |
        -----------------------------------------------------
        |       < ma | in content area >                    |
        |            |                                      |
        |  left      |              right                   |
        |  control   |              details frame           |
        |  tree      |              / output viewer         |
        |  area      |                                      |
        -----------------------------------------------------
        |     status bar area                               |
        -----------------------------------------------------

        '''
        self.executor = None

        # Main window of the application with title and size
        self.main_window = toga.MainWindow(title=self.name, size=(1024, 768))

        # Setup the menu and toolbar
        self._setup_commands()

        # Set up the main content for the window.
        self._setup_status_bar()
        self._setup_main_content()

        self._setup_init_values()

        # Now that we've laid out the grid, hide the error text
        # until we actually have an error/output to display
        # self.error_box.style.visibility = HIDDEN

        # Sets the content defined above to show on the main window
        self.main_window.content = self.content
        # Show the main window
        self.main_window.show()

        self._check_errors_status()

    def open_document(self, doc):
        pass

    ######################################################
    # Error handlers from the model or test suite  FIXME
    ######################################################

    @property
    def test_load_error(self):
        return self._test_load_error

    @test_load_error.setter
    def test_load_error(self, trace=None):
        self._test_load_error = trace

    @property
    def ignorable_test_load_error(self):
        return self._ignorable_test_load_error

    @ignorable_test_load_error.setter
    def ignorable_test_load_error(self, trace=None):
        self._ignorable_test_load_error = trace

    ######################################################
    # Internal GUI layout methods.
    ######################################################

    def _setup_commands(self):
        # Custom command groups
        self.control_tests_group = toga.Group('Test')
        self.instruments_group = toga.Group('Instruments')

        self.show_coverage_command = toga.Command(
            self.cmd_show_coverage,
            'Show coverage...',
            group=self.instruments_group
        )
        self.show_coverage_command.enabled = False if duvet is None else True

        # Button to stop run the tests
        self.stop_command = toga.Command(
            self.cmd_stop, 'Stop',
            tooltip='Stop running the tests.',
            icon=toga.Icon('icons/stop.png'),
            shortcut='s',
            group=self.control_tests_group
        )
        self.stop_command.enabled = False

        # Button to run all the tests
        self.run_all_command = toga.Command(
            self.cmd_run_all, 'Run all',
            tooltip='Run all the tests.',
            icon=toga.Icon('icons/play.png'),
            shortcut='r',
            group=self.control_tests_group
        )

        # Button to run only the tests selected by the user
        self.run_selected_command = toga.Command(
            self.cmd_run_selected, 'Run selected',
            tooltip='Run the tests selected.',
            icon=toga.Icon('icons/run_select.png'),
            shortcut='e',
            group=self.control_tests_group
        )
        self.run_selected_command.enabled = False

        # Re-run all the tests
        self.rerun_command = toga.Command(
            self.cmd_rerun, 'Re-run',
            tooltip='Re-run the tests.',
            icon=toga.Icon('icons/re_run.png'),
            shortcut='a',
            group=self.control_tests_group
        )
        self.rerun_command.enabled = False

        # Cricket's menu items
        self.commands.add(
            # Instrument items
            self.show_coverage_command,
        )

        self.main_window.toolbar.add(
            self.stop_command,
            self.run_all_command,
            self.run_selected_command,
            self.rerun_command
        )

    def _setup_main_content(self):
        '''
        Sets up the main content area. It is a persistent GUI component
        '''

        # Create the output/viewer area on the right frame
        # Need to create this before the option container in the left
        # frame is created.
        self._setup_right_frame()

        # Create the tree/control area on the left frame
        self._setup_left_frame()

        # Weight the split container so 66% of the screen
        # is the details panel.
        self.split_main_container = toga.SplitContainer(
            content=[
                (self.tree_notebook, 33),
                (self.right_box, 66),
            ],
            style=Pack(flex=1)
        )
        # Main content area
        self.outer_box = toga.Box(
            children=[
                self.split_main_container,
                self.statusbar
            ],
            style=Pack(direction=COLUMN)
        )
        self.content = self.outer_box

    def _setup_left_frame(self):
        '''
        The left frame mostly consists of the tree widget
        '''
        self.all_tests_tree = toga.Tree(
            ['Test'], accessors=['label'],
            data=self.test_suite,
            multiple_select=True
        )

        self.all_tests_tree.on_select = self.on_test_selected

        self.problem_tests_tree = toga.Tree(
            ['Test'], accessors=['label'],
            data=TestSuiteProblems(self.test_suite),
            multiple_select=True
        )
        self.problem_tests_tree.on_select = self.on_test_selected

        self.tree_notebook = toga.OptionContainer(
            content=[
                ('All tests', self.all_tests_tree),
                ('Problems', self.problem_tests_tree)
            ],
            on_select=self.on_tab_selected
        )

    def _setup_right_frame(self):
        '''
        The right frame is basically the "output viewer" space
        '''
        # Box to show the detail of a test
        self.right_box = toga.Box(style=Pack(direction=COLUMN, padding=(10, 0)))

        # Initial status for coverage
        self.coverage = False
        # Checkbutton to change the status for coverage
        # self.coverage_checkbox = toga.Switch('Generate coverage', on_toggle=self.on_coverageChange)

        # If coverage is available, enable it by default.
        # Otherwise, disable the widget
        if not coverage:
            self.coverage = False
            # self.coverage_checkbox.enabled = False

        # Label for indicator status of test
        self.status_label = toga.Label(
            '',
            style=Pack(
                text_align=CENTER,
                width=60,
                padding_right=10,
                font_family=SANS_SERIF,
                font_weight=BOLD,
                font_size=40,
            )
        )

        # Box to put the name of the test
        self.name_box = toga.Box(style=Pack(direction=ROW, padding=(5, 10)))
        # Label to indicate that the next input text it will be the name
        self.name_label = toga.Label(
            'Name:', style=Pack(text_align=RIGHT, width=80, padding_right=10)
        )
        # Text input to show the name of the test
        self.name_view = toga.TextInput(readonly=True, style=Pack(flex=1))
        # Insert the name box objects
        self.name_box.add(self.name_label)
        self.name_box.add(self.name_view)

        # Box to put the test duration
        self.duration_box = toga.Box(style=Pack(direction=ROW, padding=(5, 10)))
        # Label to indicate the test duration
        self.duration_label = toga.Label(
            'Duration:', style=Pack(text_align=RIGHT, width=80, padding_right=10)
        )
        # Text input to show the test duration
        self.duration_view = toga.TextInput(readonly=True, style=Pack(flex=1))
        self.duration_box.add(self.duration_label)
        self.duration_box.add(self.duration_view)

        # Group the name and duration into a single "identifier" box
        self.identifier_box = toga.Box(style=Pack(direction=COLUMN, flex=1))
        self.identifier_box.add(self.name_box)
        self.identifier_box.add(self.duration_box)

        # Put the identifiers on the same row as the status label
        self.summary_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER))
        self.summary_box.add(self.identifier_box)
        self.summary_box.add(self.status_label)

        # Box to put the test description
        self.description_box = toga.Box(style=Pack(direction=ROW, padding=(5, 10), flex=1))
        # Label to indicate the test description
        self.description_label = toga.Label(
            'Description:', style=Pack(text_align=RIGHT, width=80, padding_right=10)
        )
        # Text input to show the test description
        self.description_view = toga.MultilineTextInput(style=Pack(flex=1))
        # Insert the test description box objects
        self.description_box.add(self.description_label)
        self.description_box.add(self.description_view)

        # Box to put the test output
        self.output_box = toga.Box(style=Pack(direction=ROW, padding=(5, 10), flex=3))
        # Label to indicate the test output
        self.output_label = toga.Label(
            'Output:', style=Pack(text_align=RIGHT, width=80, padding_right=10)
        )
        # Text input to show the test output
        self.output_view = toga.MultilineTextInput(style=Pack(flex=1))
        # Insert the test output box objects
        self.output_box.add(self.output_label)
        self.output_box.add(self.output_view)

        # Box to put the test error
        self.error_box = toga.Box(style=Pack(direction=ROW, padding=(5, 10), flex=3))
        # Label to indicate the test error
        self.error_label = toga.Label(
            'Error:', style=Pack(text_align=RIGHT, width=80, padding_right=10)
        )
        # Text input to show the test error
        self.error_view = toga.MultilineTextInput(style=Pack(flex=1))
        # Insert the test error box objects
        self.error_box.add(self.error_label)
        self.error_box.add(self.error_view)

        # Insert the right box contents
        # self.right_box.add(self.coverage_checkbox)
        self.right_box.add(self.summary_box)
        self.right_box.add(self.description_box)
        self.right_box.add(self.output_box)
        self.right_box.add(self.error_box)

    def _setup_status_bar(self):
        '''The bottom frame to inform the user about the status of the tests
        that are running.
        '''
        self.run_status = toga.Label('Not running', style=Pack(padding_left=10))

        self.run_summary = toga.Label(
            'T:0 P:0 F:0 E:0 X:0 U:0 S:0',
            style=Pack(flex=1, text_align=RIGHT)
        )

        # Test progress
        self.progress = toga.ProgressBar(
            max=100, value=0, style=Pack(padding_left=10, padding_right=10, width=200)
        )

        self.statusbar = toga.Box(
            style=Pack(direction=ROW)
        )

        self.statusbar.add(self.run_status)
        self.statusbar.add(self.run_summary)
        self.statusbar.add(self.progress)

    def _setup_init_values(self):
        "Update the layout with the initial values."
        # Get a count of active tests to display in the status bar.

        count, labels = self.test_suite.find_tests(active=True)
        self.run_summary.text = 'T:{count} P:0 F:0 E:0 X:0 U:0 S:0'.format(count=count)

        # Update the test suite to make sure coverage status matches the GUI
        self.on_coverageChange(None)

    ######################################################
    # Handlers for setting a new test_suite
    ######################################################

    @property
    def test_suite(self):
        return self._test_suite

    @test_suite.setter
    def test_suite(self, test_suite):
        self._test_suite = test_suite
        self._test_suite.add_listener(self)

    ######################################################
    # User commands
    ######################################################

    def cmd_quit(self):
        "Command: Quit"
        # If the runner is currently running, kill it.
        self.stop()

    async def cmd_stop(self, widget):
        "Command: The stop button has been pressed"
        await self.stop()

    async def cmd_run_all(self, widget):
        "Command: The Run all button has been pressed"
        # Update test status icon
        # self.tests_tree_data.update_visualization(toga.Icon('icons/wait.png'))
        # self.problem_tests_data.data = {}
        # self.all_tests_tree.update()
        # self.problem_tests_tree.update()
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor:
            await self.run(active=True)

    async def cmd_run_selected(self, widget):
        "Command: The 'run selected' button has been pressed"
        tests_to_run = set()
        if self.current_tree.selection:
            for node in self.current_tree.selection:
                tests_to_run.add(node.path)

        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor:
            await self.run(labels=tests_to_run)

    def cmd_rerun(self, widget):
        "Command: The run/stop button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor:
            self.run(status=set(TestMethod.FAILING_STATES))

    def cmd_show_coverage(self, widget):
        "Command: Open coverage tool"
        try:
            subprocess.Popen('duvet')
        except Exception as e:
            self.main_window.error_dialog('Error on open duvet', 'Unable to start Duvet: %s' % e)

    # def cmd_cricket_page(self, sender):
    #     "Show the Cricket test_suite page"
    #     webbrowser.open_new('http://pybee.org/cricket/')

    # def cmd_beeware_page(self, sender):
    #     "Show the Beeware test_suite page"
    #     webbrowser.open_new('http://pybee.org/')

    # def cmd_cricket_github(self, sender):
    #     "Show the Cricket GitHub repo"
    #     webbrowser.open_new('http://github.com/pybee/cricket')

    # def cmd_cricket_docs(self, sender):
    #     "Show the Cricket documentation"
    #     webbrowser.open_new('https://cricket.readthedocs.io/')

    # def cmd_about_cricket(self, sender):
    #     "Show a dialog with Cricket information"

    #     self.about_cricket = "Cricket is a graphical tool that helps you run your test suites. \n \nNormal unittest test runners dump all output to the console, and provide very little detail while the suite is running. As a result: \n \n- You can't start looking at failures until the test suite has completed running,\n- It isn't a very accessible format for identifying patterns in test failures, \n- It can be hard (or cumbersome) to re-run any tests that have failed. \n \nWhy the name cricket? Test Cricket is the most prestigious version of the game of cricket. Games last for up to 5 days... just like running some test suites. The usual approach for making cricket watchable is a generous dose of beer; in programming, Balmer Peak limits come into effect, so something else is required..."

    #     self.main_window.info_dialog('Cricket', self.about_cricket)

    ######################################################
    # GUI Callbacks
    ######################################################

    def on_tab_selected(self, tab, option):
        "Event handler: the tree selection has changed."
        self.current_tree = option
        self.on_test_selected(option, None)

    def on_test_selected(self, widget, node):
        "Event handler: a test case has been selected in the tree"
        nodes = widget.selection
        # Multiple tests selected
        if nodes and len(nodes) > 1:
            self.status_label.text = ''
            self.name_view.clear()
            self.duration_view.clear()
            self.description_view.clear()

            self.output_view.clear()
            self.error_view.clear()
            # self.error_box.style.visibility = HIDDEN
        elif nodes:
            # Find the definition for the actual test method out of the test_suite
            testMethod = nodes[0]
            self.name_view.value = testMethod.path
            try:
                self.description_view.value = testMethod.description

                # Display constants for test status
                self.status_label.text = {
                    TestMethod.STATUS_UNKNOWN: '?',
                    TestMethod.STATUS_PASS: '\u25cf',
                    TestMethod.STATUS_SKIP: 'S',
                    TestMethod.STATUS_FAIL: 'F',
                    TestMethod.STATUS_EXPECTED_FAIL: 'X',
                    TestMethod.STATUS_UNEXPECTED_SUCCESS: 'U',
                    TestMethod.STATUS_ERROR: 'E',
                }[testMethod.status]
                self.status_label.style.color = {
                    TestMethod.STATUS_UNKNOWN: '#BFBFBF',
                    TestMethod.STATUS_PASS: '#28C025',
                    TestMethod.STATUS_SKIP: '#259EBF',
                    TestMethod.STATUS_FAIL: '#E32C2E',
                    TestMethod.STATUS_EXPECTED_FAIL: '#3C25BF',
                    TestMethod.STATUS_UNEXPECTED_SUCCESS: '#C82788',
                    TestMethod.STATUS_ERROR: '#E4742C',
                }[testMethod.status]

                if testMethod.status:
                    # Test has been executed
                    self.duration_view.value = '%0.2fs' % testMethod.duration

                    self.output_view.value = testMethod.output

                    if testMethod.error:
                        self.error_view.value = testMethod.error
                    #     self.error_box.style.visibility = VISIBLE
                    # else:
                    #     self.error_box.style.visibility = HIDDEN
                else:
                    # Test hasn't been executed yet.
                    self.duration_view.value = 'Not executed'

                    self.output_view.clear()
                    self.error_view.clear()

                    # self.error_box.style.visibility = HIDDEN
            except AttributeError as e:
                # There's no description attribute; that means it's not a test method,
                # it's a module or test case.
                self.status_label.text = ''
                self.description_view.clear()
                self.duration_view.clear()

                self.output_view.clear()
                self.error_view.clear()

                # self.error_box.style.visibility = HIDDEN
        else:
            # No selection at all.
            self.status_label.text = ''
            self.name_view.clear()
            self.description_view.clear()
            self.duration_view.clear()
            self.output_view.clear()
            self.error_view.clear()

            # self.error_box.style.visibility = HIDDEN

        # update "run selected" button enabled state
        self.set_selected_button_state()

    def on_coverageChange(self, widget):
        "Event handler: when the coverage checkbox has been toggled"
        self.coverage = not self.coverage
        self.test_suite.coverage = self.coverage == True

    def on_executorStatusUpdate(self, event, update):
        "The executor has some progress to report"
        # Update the status line.
        self.run_status.text = update

    def executor_test_start(self, test_path):
        "The executor has started running a new test."
        # Update status line, and set the tree item to active.
        self.run_status.text = 'Running %s...' % test_path

    def executor_test_end(self, test_path, result, remaining_time):
        "The executor has finished running a test."
        # Update the progress meter
        self.progress.value += 1

        # Update the run summary
        self.run_summary.text = 'T{total} P:{passes} F:{failed} E:{errors} X:{expected} U:{unexpected} S:{skipped}, ~{remaining} remaining'.format(
            total=self.executor.total_count,
            passes=self.executor.result_count.get(TestMethod.STATUS_PASS, 0),
            failed=self.executor.result_count.get(TestMethod.STATUS_FAIL, 0),
            errors=self.executor.result_count.get(TestMethod.STATUS_ERROR, 0),
            expected=self.executor.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0),
            unexpected=self.executor.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0),
            skipped=self.executor.result_count.get(TestMethod.STATUS_SKIP, 0),
            remaining=remaining_time,
        )

    def executor_suite_end(self, error=None):
        "The test suite finished running."
        # Display the final results
        self.run_status.text = 'Finished.'

        if error:
            self.main_window.error_dialog('Result', error)

        message = ', '.join(
            '%d %s' % (
                count, {
                    TestMethod.STATUS_PASS: "passed",
                    TestMethod.STATUS_FAIL: "failed",
                    TestMethod.STATUS_ERROR: "errors",
                    TestMethod.STATUS_EXPECTED_FAIL: "expected",
                    TestMethod.STATUS_UNEXPECTED_SUCCESS: "unexpected",
                    TestMethod.STATUS_SKIP: "skipped",
                }[state]
            )
            for state, count in sorted(self.executor.result_count.items())
        )

        if self.executor.any_failed:
            self.main_window.error_dialog('Result', message)
        else:
            self.main_window.info_dialog('Result',
                                message=message or 'No tests were ran')

        # Reset the running summary.
        self.run_summary.text = 'T{total} P:{passes} F:{failed} E:{errors} X:{expected} U:{unexpected} S:{skipped}'.format(
            total=self.executor.total_count,
            passes=self.executor.result_count.get(TestMethod.STATUS_PASS, 0),
            failed=self.executor.result_count.get(TestMethod.STATUS_FAIL, 0),
            errors=self.executor.result_count.get(TestMethod.STATUS_ERROR, 0),
            expected=self.executor.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0),
            unexpected=self.executor.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0),
            skipped=self.executor.result_count.get(TestMethod.STATUS_SKIP, 0),
        )

    def on_executorSuiteError(self, event, error):
        "An error occurred running the test suite."
        # Display the error in a dialog
        self.run_status.text = 'Error running test suite.'

        FailedTestDialog(self, error)

        # Reset the buttons
        self.reset_button_states_on_end()

        # Drop the reference to the executor
        self.executor = None

    def reset_button_states_on_end(self):
        "A test run has ended and we should enable or disable buttons as appropriate."
        self.stop_command.enabled = False
        self.run_all_command.enabled = True
        self.set_selected_button_state()
        if self.executor and self.executor.any_failed:
            self.rerun_command.enabled = True
        else:
            self.rerun_command.enabled = False

    def set_selected_button_state(self):
        state = False if self.executor else True
        self.run_selected_command.enabled = state

    ######################################################
    # GUI utility methods
    ######################################################

    async def run(self, active=True, status=None, labels=None):
        """Run the test suite.

        If active=True, only active tests will be run.
        If status is provided, only tests whose most recent run
            status matches the set provided will be executed.
        If labels is provided, only tests with those labels will
            be executed
        """
        count, labels = self.test_suite.find_tests(active=active, status=status, labels=labels)

        self.run_status.text = 'Running...'
        self.run_summary.text = 'T:{count} P:0 F:0 E:0 X:0 U:0 S:0'.format(count=count)

        self.stop_command.enabled = True
        self.run_all_command.enabled = False
        self.run_selected_command.enabled = False
        self.rerun_command.enabled = False

        self.progress.max = count
        self.progress.value = 0

        # Create the executor...
        self.executor = Executor(self.test_suite, self)

        # ...and run it
        await self.executor.run(count, labels)

        # Once it's done, clean up.
        self.executor = None
        self.reset_button_states_on_end()

    async def stop(self):
        "Stop the test suite."
        if self.executor:
            self.run_status.text = 'Stopping...'

            # await self.executor.terminate()

        self.executor = None
        self.run_status.text = 'Stopped.'

        self.reset_button_states_on_end()

    def _check_errors_status(self):
        """Checks if the model or the test_suite have errors.

        If there are errors on the model show the dialog TestLoadErrorDialog
            with these errors.
        If there are error on the test_suite show the dialog
            IgnorableTestLoadErrorDialog with these errors.
        """

        if self._test_load_error:
            dialog = TestLoadErrorDialog(self, self._test_load_error)
            if dialog.status == dialog.CANCEL:
                sys.exit(1)
        elif self._ignorable_test_load_error:
            dialog = IgnorableTestLoadErrorDialog(self,
                        self._ignorable_test_load_error)
            if dialog.status == dialog.CANCEL:
                sys.exit(1)
