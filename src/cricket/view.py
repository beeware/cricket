"""A module containing a visual representation of the testModule.

This is the "View" of the MVC world.
"""

import subprocess
import webbrowser

import toga
from toga.fonts import BOLD, SANS_SERIF
from toga.sources import AccessorColumn
from toga.style.pack import CENTER, COLUMN, HIDDEN, MONOSPACE, RIGHT, ROW, VISIBLE

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

from cricket.executor import Executor
from cricket.model import TestMethod, TestSuiteProblems


class Cricket(toga.App):
    def startup(self):
        """
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

        """
        self.executor = None

        # Main window of the application with title and size
        self.main_window = toga.MainWindow(size=(1024, 768))

        # Setup the menu and toolbar
        self._setup_commands()

        # Set up the main content for the window.
        self._setup_status_bar()
        self._setup_main_content()

        # Emit a tab selection event; this primes the
        # initial display of the status bar and details.
        self.on_tab_selected(self.tree_notebook)

        # Now that we've laid out the grid, hide the output and error text
        # until we actually have an error/output to display
        self.error_box.style.visibility = HIDDEN
        self.output_box.style.visibility = HIDDEN

        # Sets the content defined above to show on the main window
        self.main_window.content = self.content
        # Show the main window
        self.main_window.show()

    async def on_running(self):
        if self.test_load_error:
            abort = await self.dialog(
                toga.StackTraceDialog(
                    "Errors during test suite",
                    "The following errors were generated while running the test suite:",
                    self.test_load_error,
                )
            )
            if abort:
                self.exit()
        elif self.ignorable_test_load_error:
            abort = await self.dialog(
                toga.StackTraceDialog(
                    "Errors during test suite",
                    "The following errors were generated while running the test suite:",
                    self.ignorable_test_load_error,
                )
            )
            if abort:
                self.exit()

    def open_document(self, doc):
        pass

    #############################################
    # Error handlers from the model or test suite
    #############################################

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
        self.control_tests_group = toga.Group("Test")
        self.instruments_group = toga.Group("Instruments")

        self.show_coverage_command = toga.Command(
            self.cmd_show_coverage,
            "Show coverage...",
            group=self.instruments_group,
            enabled=duvet is not None,
        )

        # Button to stop run the tests
        self.stop_command = toga.Command(
            self.cmd_stop,
            "Stop",
            tooltip="Stop running the tests.",
            icon=toga.Icon("resources/stop.png"),
            shortcut="s",
            group=self.control_tests_group,
            enabled=False,
        )

        # Button to run all the tests
        self.run_all_command = toga.Command(
            self.cmd_run_all,
            "Run all",
            tooltip="Run all the tests.",
            icon=toga.Icon("resources/play.png"),
            shortcut="r",
            group=self.control_tests_group,
        )

        # Button to run only the tests selected by the user
        self.run_selected_command = toga.Command(
            self.cmd_run_selected,
            "Run selected",
            tooltip="Run the tests selected.",
            icon=toga.Icon("resources/run_select.png"),
            shortcut="e",
            group=self.control_tests_group,
            enabled=False,
        )

        # Re-run all the tests
        self.rerun_command = toga.Command(
            self.cmd_rerun,
            "Re-run",
            tooltip="Re-run the tests.",
            icon=toga.Icon("resources/re_run.png"),
            shortcut="a",
            group=self.control_tests_group,
            enabled=False,
        )

        # Help
        cmd_cricket_docs = toga.Command(
            self.show_cricket_docs,
            "Open Cricket documentation",
            group=toga.Group.HELP,
            order=20,
        )
        cmd_beeware_homepage = toga.Command(
            self.show_beeware_homepage,
            "Open BeeWare homepage",
            group=toga.Group.HELP,
            order=21,
        )
        cmd_cricket_github = toga.Command(
            self.show_cricket_github,
            "Open Cricket on GitHub",
            group=toga.Group.HELP,
            order=22,
        )

        # Cricket's menu items
        self.commands.add(
            # Instrument items
            self.show_coverage_command,
            # Help items
            cmd_cricket_docs,
            cmd_beeware_homepage,
            cmd_cricket_github,
        )

        self.main_window.toolbar.add(
            self.stop_command,
            self.run_all_command,
            self.run_selected_command,
            self.rerun_command,
        )

    def _setup_main_content(self):
        """
        Sets up the main content area. It is a persistent GUI component
        """

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
            flex=1,
        )
        # Main content area
        self.outer_box = toga.Box(
            children=[self.split_main_container, self.statusbar],
            direction=COLUMN,
        )
        self.content = self.outer_box

    def _setup_left_frame(self):
        """
        The left frame mostly consists of the tree widget
        """
        self.all_tests_tree = toga.Tree(
            columns=[AccessorColumn("Test", "label")],
            data=self.test_suite,
            on_select=self.on_test_selected,
            multiple_select=True,
        )
        self.all_tests_tree.expand()

        self.problem_tests_tree = toga.Tree(
            columns=[AccessorColumn("Test", "label")],
            data=TestSuiteProblems(self.test_suite),
            on_select=self.on_test_selected,
            multiple_select=True,
        )
        self.problem_tests_tree.expand()

        self.tree_notebook = toga.OptionContainer(
            content=[
                ("All tests", self.all_tests_tree),
                ("Problems", self.problem_tests_tree),
            ],
            on_select=self.on_tab_selected,
            margin_top=5,
        )

    def _setup_right_frame(self):
        """
        The right frame is basically the "output viewer" space
        """
        # Box to show the detail of a test
        self.right_box = toga.Box(direction=COLUMN, margin=(10, 0))

        # Initial status for coverage
        self.coverage = False
        # Checkbutton to change the status for coverage
        # self.coverage_checkbox = toga.Switch(
        #   'Generate coverage', on_toggle=self.on_coverageChange
        # )

        # If coverage is available, enable it by default.
        # Otherwise, disable the widget
        if not coverage:
            self.coverage = False
            # self.coverage_checkbox.enabled = False

        # Label for indicator status of test
        self.status_label = toga.Label(
            "",
            text_align=CENTER,
            width=60,
            margin_left=10,
            font_family=SANS_SERIF,
            font_weight=BOLD,
            font_size=40,
        )

        # Box to put the name of the test
        self.name_box = toga.Box(direction=ROW, margin=(5, 10))
        # Label to indicate that the next input text it will be the name
        self.name_label = toga.Label(
            "Name:",
            text_align=RIGHT,
            width=80,
            margin_right=10,
        )
        # Text input to show the name of the test
        self.name_view = toga.TextInput(readonly=True, flex=1)
        # Insert the name box objects
        self.name_box.add(self.name_label)
        self.name_box.add(self.name_view)

        # Box to put the test duration
        self.duration_box = toga.Box(direction=ROW, margin=(5, 10))
        # Label to indicate the test duration
        self.duration_label = toga.Label(
            "Duration:",
            text_align=RIGHT,
            width=80,
            margin_right=10,
        )
        # Text input to show the test duration
        self.duration_view = toga.TextInput(readonly=True, flex=1)
        self.duration_box.add(self.duration_label)
        self.duration_box.add(self.duration_view)

        # Group the name and duration into a single "identifier" box
        self.identifier_box = toga.Box(direction=COLUMN, flex=1)
        self.identifier_box.add(self.name_box)
        self.identifier_box.add(self.duration_box)

        # Put the identifiers on the same row as the status label
        self.summary_box = toga.Box(direction=ROW, align_items=CENTER)
        self.summary_box.add(self.identifier_box)
        self.summary_box.add(self.status_label)

        # Box to put the test description
        self.description_box = toga.Box(
            direction=ROW,
            margin=(5, 10),
            flex=1,
        )
        # Label to indicate the test description
        self.description_label = toga.Label(
            "Description:",
            text_align=RIGHT,
            width=80,
            margin_right=10,
        )
        # Text input to show the test description
        self.description_view = toga.MultilineTextInput(flex=1)
        # Insert the test description box objects
        self.description_box.add(self.description_label)
        self.description_box.add(self.description_view)

        # Box to put the test error
        self.error_box = toga.Box(direction=ROW, margin=(5, 10), flex=3)
        # Label to indicate the test error
        self.error_label = toga.Label(
            "Error:",
            text_align=RIGHT,
            width=80,
            margin_right=10,
        )
        # Text input to show the test error
        self.error_view = toga.MultilineTextInput(flex=1, font_family=MONOSPACE)
        # Insert the test error box objects
        self.error_box.add(self.error_label)
        self.error_box.add(self.error_view)

        # Box to put the test output
        self.output_box = toga.Box(direction=ROW, margin=(5, 10), flex=3)
        # Label to indicate the test output
        self.output_label = toga.Label(
            "Output:",
            text_align=RIGHT,
            width=80,
            margin_right=10,
        )
        # Text input to show the test output
        self.output_view = toga.MultilineTextInput(flex=1, font_family=MONOSPACE)
        # Insert the test output box objects
        self.output_box.add(self.output_label)
        self.output_box.add(self.output_view)

        # Insert the right box contents
        # self.right_box.add(self.coverage_checkbox)
        self.right_box.add(self.summary_box)
        self.right_box.add(self.description_box)
        self.right_box.add(self.error_box)
        self.right_box.add(self.output_box)

    def _setup_status_bar(self):
        """The bottom frame to inform the user about the status of the tests
        that are running.
        """
        self.run_status = toga.Label("Not running", margin_left=10)

        self.run_summary = toga.Label(
            "T:0 P:0 F:0 E:0 X:0 U:0 S:0",
            flex=1,
            text_align=RIGHT,
        )

        # Test progress
        self.progress = toga.ProgressBar(
            max=100,
            value=0,
            margin_left=10,
            margin_right=10,
            width=200,
        )

        self.statusbar = toga.Box(direction=ROW)

        self.statusbar.add(self.run_status)
        self.statusbar.add(self.run_summary)
        self.statusbar.add(self.progress)

    def _setup_init_values(self):
        "Update the layout with the initial values."
        # Get a count of active tests to display in the status bar.

        count, _labels = self.test_suite.find_tests(active=True)
        self.run_summary.text = f"T:{count} P:0 F:0 E:0 X:0 U:0 S:0"

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
        # self.tests_tree_data.update_visualization(toga.Icon('resources/wait.png'))
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
            subprocess.Popen("duvet")
        except subprocess.CalledProcessError as e:
            self.main_window.error_dialog(
                "Error on open duvet", f"Unable to start Duvet: {e}"
            )

    def show_beeware_homepage(self, sender):
        "Show the Beeware test_suite page"
        webbrowser.open_new("https://beeware.org/")

    def show_cricket_github(self, sender):
        "Show the Cricket GitHub repo"
        webbrowser.open_new("https://github.com/beeware/cricket")

    def show_cricket_docs(self, sender):
        "Show the Cricket documentation"
        webbrowser.open_new("https://cricket.beeware.org/")

    ######################################################
    # GUI Callbacks
    ######################################################

    def on_tab_selected(self, widget, **kwargs):
        "Event handler: the tree selection has changed."
        self.current_tree = widget.current_tab.content
        self.on_test_selected(self.current_tree)

    def on_test_selected(self, widget, **kwargs):
        "Event handler: a test case has been selected in the tree"
        nodes = widget.selection
        # Multiple tests selected
        if nodes and len(nodes) > 1:
            self.status_label.text = ""
            self.name_view.text = ""
            self.duration_view.text = ""
            self.description_view.text = ""

            self.output_view.text = ""
            self.error_view.text = ""

            self.error_box.style.visibility = HIDDEN
            self.output_box.style.visibility = HIDDEN
        elif nodes:
            # Find the definition for the actual test method out of the test_suite
            testMethod = nodes[0]
            self.name_view.value = testMethod.path
            try:
                self.description_view.value = testMethod.description

                # Display constants for test status
                self.status_label.text = {
                    TestMethod.STATUS_UNKNOWN: "?",
                    TestMethod.STATUS_PASS: "\u25cf",
                    TestMethod.STATUS_SKIP: "S",
                    TestMethod.STATUS_FAIL: "F",
                    TestMethod.STATUS_EXPECTED_FAIL: "X",
                    TestMethod.STATUS_UNEXPECTED_SUCCESS: "U",
                    TestMethod.STATUS_ERROR: "E",
                }[testMethod.status]
                self.status_label.style.color = {
                    TestMethod.STATUS_UNKNOWN: "#BFBFBF",
                    TestMethod.STATUS_PASS: "#28C025",
                    TestMethod.STATUS_SKIP: "#259EBF",
                    TestMethod.STATUS_FAIL: "#E32C2E",
                    TestMethod.STATUS_EXPECTED_FAIL: "#3C25BF",
                    TestMethod.STATUS_UNEXPECTED_SUCCESS: "#C82788",
                    TestMethod.STATUS_ERROR: "#E4742C",
                }[testMethod.status]

                if testMethod.status:
                    # Test has been executed
                    self.duration_view.value = f"{testMethod.duration:0.2f}s"

                    if testMethod.error:
                        self.error_view.value = testMethod.error
                        self.error_box.style.visibility = VISIBLE
                    else:
                        self.error_box.style.visibility = HIDDEN

                    if testMethod.output:
                        self.output_view.value = testMethod.output
                        self.output_box.style.visibility = VISIBLE
                    else:
                        self.output_box.style.visibility = HIDDEN
                else:
                    # Test hasn't been executed yet.
                    self.duration_view.value = "Not executed"

                    self.error_view.text = ""
                    self.error_box.style.visibility = HIDDEN

                    self.output_view.text = ""
                    self.output_box.style.visibility = HIDDEN
            except AttributeError:
                # There's no description attribute; that means it's not a test method,
                # it's a module or test case.
                self.status_label.text = ""
                self.description_view.text = ""
                self.duration_view.text = ""

                self.error_view.text = ""
                self.error_box.style.visibility = HIDDEN

                self.output_view.text = ""
                self.output_box.style.visibility = HIDDEN
        else:
            # No selection at all.
            self.status_label.text = ""
            self.name_view.text = ""
            self.description_view.text = ""
            self.duration_view.text = ""

            self.error_view.text = ""
            self.error_box.style.visibility = HIDDEN

            self.output_view.text = ""
            self.output_box.style.visibility = HIDDEN

        # update "run selected" button enabled state
        self.run_selected_command.enabled = not self.executor

    def on_coverageChange(self, widget):
        "Event handler: when the coverage checkbox has been toggled"
        self.coverage = not self.coverage
        self.test_suite.coverage = self.coverage

    def on_executorStatusUpdate(self, event, update):
        "The executor has some progress to report"
        # Update the status line.
        self.run_status.text = update

    def executor_test_start(self, test_path):
        "The executor has started running a new test."
        # Update status line, and set the tree item to active.
        self.run_status.text = f"Running {test_path}..."

    def executor_test_end(self, test_path, result, remaining_time):
        "The executor has finished running a test."
        # Update the progress meter
        self.progress.value += 1

        # Update the run summary
        e = self.executor
        self.run_summary.text = (
            f"T:{e.total_count} "
            f"P:{e.result_count.get(TestMethod.STATUS_PASS, 0)} "
            f"F:{e.result_count.get(TestMethod.STATUS_FAIL, 0)} "
            f"E:{e.result_count.get(TestMethod.STATUS_ERROR, 0)} "
            f"X:{e.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0)} "
            f"U:{e.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0)} "
            f"S:{e.result_count.get(TestMethod.STATUS_SKIP, 0)}, "
            f"~{remaining_time} remaining"
        )

    async def executor_suite_end(self, error=None):
        "The test suite finished running."
        # Display the final results
        self.run_status.text = "Finished."

        if error:
            await self.dialog(toga.ErrorDialog("Result", error))

        def state_msg(state):
            return {
                TestMethod.STATUS_PASS: "passed",
                TestMethod.STATUS_FAIL: "failed",
                TestMethod.STATUS_ERROR: "errors",
                TestMethod.STATUS_EXPECTED_FAIL: "expected",
                TestMethod.STATUS_UNEXPECTED_SUCCESS: "unexpected",
                TestMethod.STATUS_SKIP: "skipped",
            }[state]

        message = ", ".join(
            f"{count} {state_msg(state)}"
            for state, count in sorted(self.executor.result_count.items())
        )

        if self.executor.any_failed:
            await self.dialog(toga.ErrorDialog("Result", message))
        else:
            await self.dialog(
                toga.InfoDialog(
                    "Result",
                    message=message or "No tests were run",
                ),
            )

        # Reset the running summary.
        e = self.executor
        self.run_summary.text = (
            f"T{e.total_count} "
            f"P:{e.result_count.get(TestMethod.STATUS_PASS, 0)} "
            f"F:{e.result_count.get(TestMethod.STATUS_FAIL, 0)} "
            f"E:{e.result_count.get(TestMethod.STATUS_ERROR, 0)} "
            f"X:{e.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0)} "
            f"U:{e.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0)} "
            f"S:{e.result_count.get(TestMethod.STATUS_SKIP, 0)}"
        )

    # def on_executorSuiteError(self, event, error):
    #     "An error occurred running the test suite."
    #     # Display the error in a dialog
    #     self.run_status.text = "Error running test suite."

    #     FailedTestDialog(self, error)

    #     # Reset the buttons
    #     self.reset_button_states()

    #     # Drop the reference to the executor
    #     self.executor = None

    def reset_button_states(self):
        "A test run has ended and we should enable or disable buttons as appropriate."
        self.stop_command.enabled = False
        self.run_all_command.enabled = True
        self.run_selected_command.enabled = not self.executor
        if self.executor and self.executor.any_failed:
            self.rerun_command.enabled = True
        else:
            self.rerun_command.enabled = False

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
        count, labels = self.test_suite.find_tests(
            active=active, status=status, labels=labels
        )

        self.run_status.text = "Running..."
        self.run_summary.text = f"T:{count} P:0 F:0 E:0 X:0 U:0 S:0"

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
        self.reset_button_states()

    async def stop(self):
        "Stop the test suite."
        if self.executor:
            self.run_status.text = "Stopping..."

            # await self.executor.terminate()

        self.executor = None
        self.run_status.text = "Stopped."

        self.reset_button_states()
