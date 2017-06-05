"""A module containing a visual representation of the testModule.

This is the "View" of the MVC world.
"""

import sys
import toga
import subprocess
import webbrowser
from colosseum import CSS

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

from cricket.model import TestMethod, TestCase, TestModule
from cricket.executor import Executor

# Display constants for test status
STATUS = {
    TestMethod.STATUS_PASS: {
        'description': u'Pass',
        'symbol': u'\u25cf',
        'tag': 'pass',
        'color': '#28C025',
    },
    TestMethod.STATUS_SKIP: {
        'description': u'Skipped',
        'symbol': u'S',
        'tag': 'skip',
        'color': '#259EBF'
    },
    TestMethod.STATUS_FAIL: {
        'description': u'Failure',
        'symbol': u'F',
        'tag': 'fail',
        'color': '#E32C2E'
    },
    TestMethod.STATUS_EXPECTED_FAIL: {
        'description': u'Expected\n  failure',
        'symbol': u'X',
        'tag': 'expected',
        'color': '#3C25BF'
    },
    TestMethod.STATUS_UNEXPECTED_SUCCESS: {
        'description': u'Unexpected\n   success',
        'symbol': u'U',
        'tag': 'unexpected',
        'color': '#C82788'
    },
    TestMethod.STATUS_ERROR: {
        'description': 'Error',
        'symbol': u'E',
        'tag': 'error',
        'color': '#E4742C'
    },
}

STATUS_DEFAULT = {
    'description': 'Not\nexecuted',
    'symbol': u'',
    'tag': None,
    'color': '#BFBFBF',
}



class MainWindow(toga.App):
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

        self._project = None
        self.executor = None
        self.content = None

        # Main window of the application with title and size
        self.main_window = toga.MainWindow(self.name, size=(1024,768))
        self.main_window.app = self

        # Setup the menu
        self._setup_menubar()

        # Set up the main content for the window.
        self._setup_button_toolbar()
        self._setup_main_content()
        self._setup_status_bar()

        # Set up listeners for runner events.
        Executor.bind('test_status_update', self.on_executorStatusUpdate)
        Executor.bind('test_start', self.on_executorTestStart)
        Executor.bind('test_end', self.on_executorTestEnd)
        Executor.bind('suite_end', self.on_executorSuiteEnd)
        Executor.bind('suite_error', self.on_executorSuiteError)

        # Now that we've laid out the grid, hide the error and output text
        # until we actually have an error/output to display
        self._hide_test_output()
        self._hide_test_errors()

        # Sets the content defined above to show on the main window
        self.main_window.content = self.content
        # Show the main window
        self.main_window.show()

        self._check_errors_status()

    ######################################################
    # Error handlers from the model or project
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

    def _setup_menubar(self):
        '''
        The menu bar is located at the top of the OS or application depending
        on which OS is being used. It contains drop down items menus to
        interact with the system. It is a persistent GUI component.
        '''
        # TODO Add menu items will be implement, issue #81
        pass

    def _setup_button_toolbar(self):
        '''
        The button toolbar runs as a horizontal area at the top of the GUI.
        It is a persistent GUI component
        '''

        # TODO decide which icon to put in the commands of the toolbar

        # Button to stop run the tests
        self.stop_button = toga.Command(self.cmd_stop, 'Stop',
                                         tooltip='Stop running the tests.',
                                         icon=toga.TIBERIUS_ICON)
        self.stop_button.enabled = False

        # Button to run all the tests
        self.run_all_button = toga.Command(self.cmd_run_all, 'Run all',
                                         tooltip='Run all the tests.',
                                         icon=toga.TIBERIUS_ICON)

        # Button to run only the tests selected by the user
        self.run_selected_button = toga.Command(self.cmd_run_selected,
                                        'Run selected',
                                         tooltip='Run the tests selected.',
                                         icon=toga.TIBERIUS_ICON)
        self.run_selected_button.enabled = False

        # Re-run all the tests
        self.rerun_button = toga.Command(self.cmd_rerun, 'Re-run',
                                         tooltip='Re-run the tests.',
                                         icon=toga.TIBERIUS_ICON)
        self.rerun_button.enabled = False

        # TODO add switch for generate coverage

        self.main_window.toolbar = [self.stop_button,
                                    self.run_all_button,
                                    self.run_selected_button,
                                    self.rerun_button]

    def _setup_main_content(self):
        '''
        Sets up the main content area. It is a persistent GUI component
        '''

        # Create the tree/control area on the left frame
        self._setup_left_frame()
        self._setup_all_tests_tree()
        self._setup_problem_tests_tree()

        # Create the output/viewer area on the right frame
        self._setup_right_frame()

        self.split_main_container = toga.SplitContainer()
        self.split_main_container.content = [self.left_box, self.right_box]

        # Main content area
        # TODO uncomment this after correct the issue #167
        # self.content = toga.Box()
        # self.content.add(self.split_main_container)

        # TODO comment this after correct the issue #167
        self.content = self.split_main_container

    def _setup_left_frame(self):
        '''
        The left frame mostly consists of the tree widget
        '''
        all_tests_box = toga.Tree(['Tests'])
        problems_box = toga.Tree(['Problems'])

        self.left_box = toga.OptionContainer(content=[
                                                ('All tests', all_tests_box),
                                                ('Problems', problems_box)])

    def _setup_all_tests_tree(self):
        # TODO add tree widget to set all the tests tree
        pass

    def _setup_problem_tests_tree(self):
        # TODO add tree widget to set all the problems tests tree
        pass

    def _setup_right_frame(self):
        '''
        The right frame is basically the "output viewer" space
        '''
        # Box to show the detail of a test
        self.right_box = toga.Box(style=CSS(flex_direction='column',
                                            padding_top=15))
        # Box to put the name of the test
        self.name_box = toga.Box(style=CSS(flex_direction='row', margin=5))

        # Label to indicate that the next input text it will be the name
        self.name_label = toga.Label('Name:', alignment=toga.RIGHT_ALIGNED,
                                    style=CSS(width=50, margin_right=10))

        # Text input to show the name of the test
        self.name_input = toga.TextInput(readonly=True, style=CSS(flex=1))

        self.test_status = toga.Label('.', alignment=toga.LEFT_ALIGNED,
                                        style=CSS(width=100, height=50, margin_left=10))

        # add font to test_status when the weight of the font and color for
        #   labels become available
        # self.test_status_font = toga.Font(family='Helvetica', size=50)
        # self.test_status.set_font(self.test_status_font)
        # self.test_status.rehint()

        self.name_box.add(self.name_label)
        self.name_box.add(self.name_input)
        # self.name_box.add(self.test_status)

        self.right_box.add(self.name_box)

        # TODO duration, description, output and error labels
        #   and readonly text input

    def _setup_status_bar(self):
        '''
        The bottom frame to inform the user about the status of the tests that are running. It is a persistent GUI component
        '''

        self.run_status = toga.Label('Not running')

        self.statusbar = toga.Box()
        self.statusbar.add(self.run_status)

        # TODO uncomment this after correct the issue #167
        # self.content.add(self.statusbar)

        # TODO add run status, summary and progress values

    ######################################################
    # Utility methods for inspecting current GUI state
    ######################################################

    @property
    def current_test_tree(self):
        "Check the tree notebook to return the currently selected tree."
        pass

    ######################################################
    # Handlers for setting a new project
    ######################################################

    @property
    def project(self):
        return self._project

    def _add_test_module(self, parentNode, testModule):
        pass

    @project.setter
    def project(self, project):
        self._project = project

        # Listen for any state changes on nodes in the tree
        TestModule.bind('active', self.on_nodeActive)
        TestCase.bind('active', self.on_nodeActive)
        TestMethod.bind('active', self.on_nodeActive)

        TestModule.bind('inactive', self.on_nodeInactive)
        TestCase.bind('inactive', self.on_nodeInactive)
        TestMethod.bind('inactive', self.on_nodeInactive)

        # Listen for new nodes added to the tree
        TestModule.bind('new', self.on_nodeAdded)
        TestCase.bind('new', self.on_nodeAdded)
        TestMethod.bind('new', self.on_nodeAdded)

        # Listen for any status updates on nodes in the tree.
        TestMethod.bind('status_update', self.on_nodeStatusUpdate)

        # Update the project to make sure coverage status matches the GUI
        self.on_coverageChange()

    ######################################################
    # User commands
    ######################################################

    def cmd_quit(self):
        "Command: Quit"
        # If the runner is currently running, kill it.
        self.stop()

    def cmd_stop(self, event=None):
        "Command: The stop button has been pressed"
        self.stop()

    def cmd_run_all(self, event=None):
        "Command: The Run all button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self.run(active=True)

    def cmd_run_selected(self, event=None):
        "Command: The 'run selected' button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            pass

    def cmd_rerun(self, event=None):
        "Command: The run/stop button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self.run(status=set(TestMethod.FAILING_STATES))

    def cmd_open_duvet(self, event=None):
        "Command: Open Duvet"
        try:
            subprocess.Popen('duvet')
        except Exception as e:
            pass

    def cmd_cricket_page(self):
        "Show the Cricket project page"
        webbrowser.open_new('http://pybee.org/cricket/')

    def cmd_beeware_page(self):
        "Show the Beeware project page"
        webbrowser.open_new('http://pybee.org/')

    def cmd_cricket_github(self):
        "Show the Cricket GitHub repo"
        webbrowser.open_new('http://github.com/pybee/cricket')

    def cmd_cricket_docs(self):
        "Show the Cricket documentation"
        webbrowser.open_new('https://cricket.readthedocs.io/')

    ######################################################
    # GUI Callbacks
    ######################################################

    def on_testModuleClicked(self, event):
        "Event handler: a module has been clicked in the tree"
        pass

    def on_testCaseClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        pass

    def on_testMethodClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        pass

    def on_testModuleSelected(self, event):
        "Event handler: a test module has been selected in the tree"
        self._hide_test_output()
        self._hide_test_errors()

        # update "run selected" button enabled state
        self.set_selected_button_state()

    def on_testCaseSelected(self, event):
        "Event handler: a test case has been selected in the tree"
        self._hide_test_output()
        self._hide_test_errors()

        # update "run selected" button enabled state
        self.set_selected_button_state()

    def on_testMethodSelected(self, event):
        "Event handler: a test case has been selected in the tree"
        # update "run selected" button enabled state
        self.set_selected_button_state()

    def on_nodeAdded(self, node):
        "Event handler: a new node has been added to the tree"
        pass

    def on_nodeActive(self, node):
        "Event handler: a node on the tree has been made active"
        pass

    def on_nodeInactive(self, node):
        "Event handler: a node on the tree has been made inactive"
        pass

    def on_nodeStatusUpdate(self, node):
        "Event handler: a node on the tree has received a status update"
        pass

    def on_coverageChange(self):
        "Event handler: when the coverage checkbox has been toggled"
        pass

    def on_testProgress(self):
        "Event handler: a periodic update to poll the runner for output, generating GUI updates"
        if self.executor and self.executor.poll():
            self.root.after(100, self.on_testProgress)

    def on_executorStatusUpdate(self, event, update):
        "The executor has some progress to report"
        # Update the status line.
        self.run_status.set(update)

    def on_executorTestStart(self, event, test_path):
        "The executor has started running a new test."
        # Update status line, and set the tree item to active.
        self.run_status.set('Running %s...' % test_path)

    def on_executorTestEnd(self, event, test_path, result, remaining_time):
        "The executor has finished running a test."
        # Update the progress meter
        pass

    def on_executorSuiteEnd(self, event, error=None):
        "The test suite finished running."
        # Reset the buttons
        self.reset_button_states_on_end()

        # Drop the reference to the executor
        self.executor = None

    def on_executorSuiteError(self, event, error):
        "An error occurred running the test suite."
        # Reset the buttons
        self.reset_button_states_on_end()

        # Drop the reference to the executor
        self.executor = None

    def reset_button_states_on_end(self):
        "A test run has ended and we should enable or disable buttons as appropriate."
        self.set_selected_button_state()
        if self.executor and self.executor.any_failed:
            pass
        else:
            pass

    def set_selected_button_state(self):
        if self.executor and self.executor.is_running:
            pass
        elif self.current_test_tree.selection():
            pass
        else:
            pass

    ######################################################
    # GUI utility methods
    ######################################################

    def run(self, active=True, status=None, labels=None):
        """Run the test suite.

        If active=True, only active tests will be run.
        If status is provided, only tests whose most recent run
            status matches the set provided will be executed.
        If labels is provided, only tests with those labels will
            be executed
        """
        count, labels = self.project.find_tests(active, status, labels)

        self.progress['maximum'] = count
        self.progress_value.set(0)

        # Create the runner
        self.executor = Executor(self.project, count, labels)

    def stop(self):
        "Stop the test suite."
        if self.executor and self.executor.is_running:

            self.executor.terminate()
            self.executor = None

            self.reset_button_states_on_end()

    def _hide_test_output(self):
        "Hide the test output panel on the test results page"
        pass

    def _show_test_output(self, content):
        "Show the test output panel on the test results page"
        pass

    def _hide_test_errors(self):
        "Hide the test error panel on the test results page"
        pass

    def _show_test_errors(self, content):
        "Show the test error panel on the test results page"
        pass

    def _check_errors_status(self):
        """Checks if the model or the project have errors.

        If there are errors on the model show the dialog TestLoadErrorDialog
            with these errors.
        If there are error on the project show the dialog
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


class StackTraceDialog:
    OK = 1
    CANCEL = 2

    def __init__(self, parent, title, label, trace, button_text='OK',
                 cancel_text='Cancel'):
        '''Show a dialog with a scrollable stack trace.

        Arguments:

            parent -- a parent window (the application window)
            title -- the title for the stack trace window
            label -- the label describing the stack trace
            trace -- the stack trace content to display.
            button_text -- the label for the button text ("OK" by default)
            cancel_text -- the label for the cancel button ("Cancel" by default)
        '''
        self.parent = parent
        self.status = None

        # TODO adjust label, readonly input text and a scrollcontainer

        if cancel_text is not None:
            # TODO adjust add button to cancel
            pass

        # TODO adjust button ok

        self.parent.main_window.stack_trace_dialog(title, label, trace)

    def ok(self, event=None):
        self.status = self.OK

    def cancel(self, event=None):
        self.status = self.CANCEL

class FailedTestDialog(StackTraceDialog):
    def __init__(self, parent, trace):
        '''Report an error when running a test suite.

        Arguments:

            parent -- a parent window (the application window)
            trace -- the stack trace content to display.
        '''
        StackTraceDialog.__init__(
            self,
            parent,
            'Error running test suite',
            'The following stack trace was generated when attempting to run the test suite:',
            trace,
            button_text='OK',
            cancel_text='Quit',
        )

    def cancel(self, event=None):
        StackTraceDialog.cancel(self, event=event)

class TestErrorsDialog(StackTraceDialog):
    def __init__(self, parent, trace):
        '''Show a dialog with a scrollable list of errors.

        Arguments:

            parent -- a parent window (the application window)
            error -- the error content to display.
        '''
        StackTraceDialog.__init__(
            self,
            parent,
            'Errors during test suite',
            ('The following errors were generated while running the test suite:'),
            trace,
            button_text='OK',
            cancel_text=None,
        )

    def cancel(self, event=None):
        StackTraceDialog.cancel(self, event=event)


class TestLoadErrorDialog(StackTraceDialog):
    def __init__(self, parent, trace):
        '''Show a dialog with a scrollable stack trace.

        Arguments:

            parent -- a parent window (the application window)
            trace -- the stack trace content to display.
        '''
        StackTraceDialog.__init__(
            self,
            parent,
            'Error discovering test suite',
            ('The following stack trace was generated when attempting to '
             'discover the test suite:'),
            trace,
            button_text='Retry',
            cancel_text='Quit',
        )

    def cancel(self, event=None):
        StackTraceDialog.cancel(self, event=event)


class IgnorableTestLoadErrorDialog(StackTraceDialog):
    def __init__(self, parent, trace):
        '''Show a dialog with a scrollable stack trace when loading
           tests turned up errors in stderr but they can safely be ignored.

        Arguments:

            parent -- a parent window (the application window)
            trace -- the stack trace content to display.
        '''
        StackTraceDialog.__init__(
            self,
            parent,
            'Error discovering test suite',
            ('The following error where captured during test discovery '
             'but running the tests might still work:'),
            trace,
            button_text='Continue',
            cancel_text='Quit',
        )
