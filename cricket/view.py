"""A module containing a visual representation of the testModule.

This is the "View" of the MVC world.
"""

import os
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

ICONS_DIR = os.path.dirname(__file__)+'/icons/'

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

        self.executor = None
        self.content = None

        # Main window of the application with title and size
        self.main_window = toga.MainWindow(self.name, size=(1024,768))
        self.main_window.app = self

        # Setup the menu
        self._setup_menubar()

        # Set up the main content for the window.
        self._setup_button_toolbar()
        self._setup_status_bar()
        self._setup_main_content()

        self._setup_init_values()

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

        # Add details about the project on default menu items
        for default_menu in self.commands:
            if hasattr(default_menu, 'label'):
                if 'About' in default_menu.label:
                    default_menu.enabled = True
                    default_menu.action = self.cmd_about_cricket
                elif 'Preferences' in default_menu.label:
                    # TODO implement cricket preferences
                    pass
                elif 'Visit homepage' in default_menu.label:
                    default_menu.enabled = True
                    default_menu.action = self.cmd_cricket_page
                    default_menu.label = 'Open Cricket project page'
                    default_menu.group = toga.Group.HELP

        # Custom menus
        self.control_tests_group = toga.Group('Test')
        self.beeware_group = toga.Group('BeeWare')

        self.open_duvet_command = toga.Command(self.cmd_open_duvet,
                                                'Open Duvet...',
                                                group=self.beeware_group)
        self.open_duvet_command.enabled = False if duvet is None else True

        # Cricket's menu items
        self.commands.add(
            # Beeware items
            self.open_duvet_command,

            # Help items
            toga.Command(self.cmd_cricket_docs, 'Open Documentation',
                        group=toga.Group.HELP),
            toga.Command(self.cmd_cricket_github, 'Open Cricket on GitHub',
                        group=toga.Group.HELP),
            toga.Command(self.cmd_beeware_page, 'Open BeeWare project page',
                        group=toga.Group.HELP),
        )

    def _setup_button_toolbar(self):
        '''
        The button toolbar runs as a horizontal area at the top of the GUI.
        It is a persistent GUI component
        '''

        # Button to stop run the tests
        self.stop_button = toga.Command(self.cmd_stop, 'Stop',
                                         tooltip='Stop running the tests.',
                                         icon=ICONS_DIR+'stop.png',
                                         shortcut='s',
                                         group=self.control_tests_group)
        self.stop_button.enabled = False

        # Button to run all the tests
        self.run_all_button = toga.Command(self.cmd_run_all, 'Run all',
                                         tooltip='Run all the tests.',
                                         icon=ICONS_DIR+'play.png',
                                         shortcut='r',
                                         group=self.control_tests_group)

        # Button to run only the tests selected by the user
        self.run_selected_button = toga.Command(self.cmd_run_selected,
                                        'Run selected',
                                         tooltip='Run the tests selected.',
                                         icon=ICONS_DIR+'run_select.png',
                                         shortcut='e',
                                         group=self.control_tests_group)
        self.run_selected_button.enabled = False

        # Re-run all the tests
        self.rerun_button = toga.Command(self.cmd_rerun, 'Re-run',
                                         tooltip='Re-run the tests.',
                                         icon=ICONS_DIR+'re_run.png',
                                         shortcut='a',
                                         group=self.control_tests_group)
        self.rerun_button.enabled = False

        self.main_window.toolbar.add(self.stop_button,
                                    self.run_all_button,
                                    self.run_selected_button,
                                    self.rerun_button)

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
        self.outer_split = toga.SplitContainer(direction =
                                            toga.SplitContainer.HORIZONTAL)
        self.outer_split.content = [self.split_main_container, self.statusbar]

        self.content = self.outer_split

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

        # Initial status for coverage
        self.coverage = False
        # Checkbutton to change the status for coverage
        self.coverage_checkbox = toga.Switch('Generate coverage',
                                on_toggle=self.on_coverageChange)

        # If coverage is available, enable it by default.
        # Otherwise, disable the widget
        if not coverage:
            self.coverage = False
            self.coverage_checkbox.enabled = False

        label_sample = lambda text: toga.Label(text,
                                    alignment=toga.RIGHT_ALIGNED,
                                    style=CSS(width=80, margin_right=10))
        text_input_sample = lambda text: toga.TextInput(readonly=True,
                                                        style=CSS(flex=1),
                                                        initial=text)
        text_input_scroll_sample = lambda text: \
                                toga.MultilineTextInput(style=CSS(flex=1),
                                                        initial=text)

        # Box to put the name of the test
        self.name_box = toga.Box(style=CSS(flex_direction='row', margin=5))
        # Label to indicate that the next input text it will be the name
        self.name_label = label_sample('Name:')
        # Text input to show the name of the test
        self.name_input = text_input_sample('')
        # Insert the name box objects
        self.name_box.add(self.name_label)
        self.name_box.add(self.name_input)

        # TODO wait fix issue 175
        # self.test_status = toga.Label('.', alignment=toga.LEFT_ALIGNED,
        #                                 style=CSS(width=100, height=50,
        #                                 margin_left=10))
        # add font to test_status when the weight of the font and color for
        #   labels become available
        # self.test_status_font = toga.Font(family='Helvetica', size=50)
        # self.test_status.set_font(self.test_status_font)
        # self.test_status.rehint()
        # self.name_box.add(self.test_status)

        # Box to put the test duration
        self.duration_box = toga.Box(style=CSS(flex_direction='row', margin=5))
        # Label to indicate the test duration
        self.duration_label = label_sample('Duration:')
        # Text input to show the test duration
        self.duration_input = text_input_sample('')
        self.duration_box.add(self.duration_label)
        self.duration_box.add(self.duration_input)

        # Box to put the test description
        self.description_box = toga.Box(style=CSS(flex_direction='row',
                                                margin=5))
        # Label to indicate the test description
        self.description_label = label_sample('Description:')
        # Text input to show the test description
        self.description_input = text_input_scroll_sample('')
        # Insert the test description box objects
        self.description_box.add(self.description_label)
        self.description_box.add(self.description_input)

        # Box to put the test output
        self.output_box = toga.Box(style=CSS(flex_direction='row', margin=5))
        # Label to indicate the test output
        self.output_label = label_sample('Output:')
        # Text input to show the test output
        self.output_input = text_input_scroll_sample('')
        # Insert the test output box objects
        self.output_box.add(self.output_label)
        self.output_box.add(self.output_input)

        # Box to put the test error
        self.error_box = toga.Box(style=CSS(flex_direction='row', margin=5))
        # Label to indicate the test error
        self.error_label = label_sample('Error:')
        # Text input to show the test error
        self.error_input = text_input_scroll_sample('')
        # Insert the test error box objects
        self.error_box.add(self.error_label)
        self.error_box.add(self.error_input)

        # Insert the right box contents
        self.right_box.add(self.coverage_checkbox)
        self.right_box.add(self.name_box)
        self.right_box.add(self.duration_box)
        self.right_box.add(self.description_box)
        self.right_box.add(self.output_box)
        self.right_box.add(self.error_box)

    def _setup_status_bar(self):
        '''
        The bottom frame to inform the user about the status of the tests that are running. It is a persistent GUI component
        '''

        self.run_status = toga.Label('Not running')

        self.run_summary = toga.Label('T:0 P:0 F:0 E:0 X:0 U:0 S:0',
                                        alignment=toga.RIGHT_ALIGNED,
                                        style=CSS(width=200))

        self.statusbar = toga.Box(style=CSS(flex_direction='row'))
        self.statusbar.add(self.run_status)
        self.statusbar.add(self.run_summary)

        # TODO add run status, summary input text readonly and progress values

    def _setup_init_values(self):
        "Update the layout with the initial values."
        # Get a count of active tests to display in the status bar.
        count, labels = self.project.find_tests(True)
        self.run_summary.text = 'T:%s P:0 F:0 E:0 X:0 U:0 S:0' % count

        # Update the project to make sure coverage status matches the GUI
        self.on_coverageChange()

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
        # TODO tree widget
        # testModule_node = self.all_tests_tree.insert(
        #     parentNode, 'end', testModule.path,
        #     text=testModule.name,
        #     tags=['TestModule', 'active'],
        #     open=True)
        #
        # for subModuleName, subModule in sorted(testModule.items()):
        #     if isinstance(subModule, TestModule):
        #         self._add_test_module(testModule_node, subModule)
        #     else:
        #         testCase = subModule
        #         testCase_node = self.all_tests_tree.insert(
        #             testModule_node, 'end', testCase.path,
        #             text=testCase.name,
        #             tags=['TestCase', 'active'],
        #             open=True
        #         )
        #
        #         for testMethod_name, testMethod in sorted(testCase.items()):
        #             self.all_tests_tree.insert(
        #                 testCase_node, 'end', testMethod.path,
        #                 text=testMethod.name,
        #                 tags=['TestMethod', 'active'],
        #                 open=True
        #             )
        pass

    @project.setter
    def project(self, project):
        self._project = project

        # Populate the initial tree nodes. This is recursive, because
        # the tree could be of arbitrary depth.
        for testModule_name, testModule in sorted(project.items()):
            self._add_test_module('', testModule)

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
        # TODO do this part after the port of the Tree widget

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
            self.main_window.error_dialog('Error on open duvet',
                                'Unable to start Duvet: %s' % e)

    def cmd_cricket_page(self, sender):
        "Show the Cricket project page"
        webbrowser.open_new('http://pybee.org/cricket/')

    def cmd_beeware_page(self, sender):
        "Show the Beeware project page"
        webbrowser.open_new('http://pybee.org/')

    def cmd_cricket_github(self, sender):
        "Show the Cricket GitHub repo"
        webbrowser.open_new('http://github.com/pybee/cricket')

    def cmd_cricket_docs(self, sender):
        "Show the Cricket documentation"
        webbrowser.open_new('https://cricket.readthedocs.io/')

    def cmd_about_cricket(self, sender):
        "Show a dialog with Cricket information"

        self.about_cricket = "Cricket is a graphical tool that helps you run your test suites. \n \nNormal unittest test runners dump all output to the console, and provide very little detail while the suite is running. As a result: \n \n- You can't start looking at failures until the test suite has completed running,\n- It isn't a very accessible format for identifying patterns in test failures, \n- It can be hard (or cumbersome) to re-run any tests that have failed. \n \nWhy the name cricket? Test Cricket is the most prestigious version of the game of cricket. Games last for up to 5 days... just like running some test suites. The usual approach for making cricket watchable is a generous dose of beer; in programming, Balmer Peak limits come into effect, so something else is required..."

        self.main_window.info_dialog('Cricket', self.about_cricket)


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
        self.name_input.clear()
        self.duration_input.clear()
        self.description_input.clear()

        # TODO wait fix issue 175
        # self.test_status.set('')

        self._hide_test_output()
        self._hide_test_errors()

        # update "run selected" button enabled state
        self.set_selected_button_state()

    def on_testCaseSelected(self, event):
        "Event handler: a test case has been selected in the tree"
        self.name_input.clear()
        self.duration_input.clear()
        self.description_input.clear()

        # TODO wait fix issue 175
        # self.test_status.set('')

        self._hide_test_output()
        self._hide_test_errors()

        # update "run selected" button enabled state
        self.set_selected_button_state()

    def on_testMethodSelected(self, event):
        "Event handler: a test case has been selected in the tree"
        "Event handler: a test case has been selected in the tree"
        if len(event.widget.selection()) == 1:
            parts = event.widget.selection()[0].split('.')

            # Find the definition for the actual test method
            # out of the project.
            testMethod = self.project
            for part in parts:
                testMethod = testMethod[part]

            self.name_input.value = testMethod.path

            self.description.clear()
            self.description.value += testMethod.description

            config = STATUS.get(testMethod.status, STATUS_DEFAULT)
            # TODO wait fix issue 175
            # self.test_status_widget.config(foreground=config['color'])
            # self.test_status.set(config['symbol'])

            if testMethod._result:
                # Test has been executed
                self.duration.value = '%0.2fs' % testMethod._result['duration']

                if testMethod.output:
                    self._show_test_output(testMethod.output)
                else:
                    self._hide_test_output()

                if testMethod.error:
                    self._show_test_errors(testMethod.error)
                else:
                    self._hide_test_errors()
            else:
                # Test hasn't been executed yet.
                self.duration.value = 'Not executed'

                self._hide_test_output()
                self._hide_test_errors()

        else:
            # Multiple tests selected
            self.name.clear()
            self.duration.clear()
            self.description.clear()

            # TODO wait fix issue 175
            # self.test_status.set('')

            self._hide_test_output()
            self._hide_test_errors()

        # update "run selected" button enabled state
        self.set_selected_button_state()

    def on_nodeAdded(self, node):
        "Event handler: a new node has been added to the tree"
        # TODO on tree widget part
        pass

    def on_nodeActive(self, node):
        "Event handler: a node on the tree has been made active"
        # TODO on tree widget part
        pass

    def on_nodeInactive(self, node):
        "Event handler: a node on the tree has been made inactive"
        # TODO on tree widget part
        pass

    def on_nodeStatusUpdate(self, node):
        "Event handler: a node on the tree has received a status update"
        # TODO on tree widget part
        pass

    def on_coverageChange(self, event=None):
        "Event handler: when the coverage checkbox has been toggled"
        self.coverage = not self.coverage
        self.project.coverage = self.coverage == True
        if self.coverage:
            self._hide_test_output()
            self._hide_test_errors()
        else:
            self._show_test_output('olar')
            self._show_test_errors('olar')

    def on_testProgress(self):
        "Event handler: a periodic update to poll the runner for output, generating GUI updates"
        if self.executor and self.executor.poll():
            # TODO update layout every 100 ms
            pass
            # self.root.after(100, self.on_testProgress)

    def on_executorStatusUpdate(self, event, update):
        "The executor has some progress to report"
        # Update the status line.
        self.run_status.text = update

    def on_executorTestStart(self, event, test_path):
        "The executor has started running a new test."
        # Update status line, and set the tree item to active.
        self.run_status.text = 'Running %s...' % test_path

    def on_executorTestEnd(self, event, test_path, result, remaining_time):
        "The executor has finished running a test."
        # TODO update progress bar
        # Update the progress meter
        # self.progress_value.set(self.progress_value.get() + 1)

        # Update the run summary
        self.run_summary.text = 'T:%(total)s P:%(pass)s F:%(fail)s E:%(error)s X:%(expected)s U:%(unexpected)s S:%(skip)s, ~%(remaining)s remaining' % {
            'total': self.executor.total_count,
            'pass': self.executor.result_count.get(TestMethod.STATUS_PASS, 0),
            'fail': self.executor.result_count.get(TestMethod.STATUS_FAIL, 0),
            'error': self.executor.result_count.get(TestMethod.STATUS_ERROR, 0),
            'expected': self.executor.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0),
            'unexpected': self.executor.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0),
            'skip': self.executor.result_count.get(TestMethod.STATUS_SKIP, 0),
            'remaining': remaining_time
        }

        # If the test that just fininshed is the one (and only one)
        # selected on the tree, update the display.
        # TODO on tree widget part
        # current_tree = self.current_test_tree
        # if len(current_tree.selection()) == 1:
        #     # One test selected.
        #     if current_tree.selection()[0] == test_path:
        #         # If the test that just finished running is the selected
        #         # test, force reset the selection, which will generate a
        #         # selection event, forcing a refresh of the result page.
        #         current_tree.selection_set(current_tree.selection())
        # else:
        # No or Multiple tests selected
        self.name.clear()
        self.duration.clear()
        self.description.clear()

        # TODO wait fix issue 175
        # self.test_status.set('')

        self._hide_test_output()
        self._hide_test_errors()

    def on_executorSuiteEnd(self, event, error=None):
        "The test suite finished running."
        # Display the final results
        self.run_status.text = 'Finished.'

        if error:
            # TODO update dialog error
            pass

        if self.executor.any_failed:
            # TODO update dialog error
            pass
        else:
            # TODO update dialog error
            pass

        message = ', '.join(
            '%d %s' % (count, TestMethod.STATUS_LABELS[state])
            for state, count in sorted(self.executor.result_count.items()))

        # TODO update dialog message error
        # dialog(message=message or 'No tests were ran')

        # Reset the running summary.
        self.run_summary.text = 'T:%(total)s P:%(pass)s F:%(fail)s E:%(error)s X:%(expected)s U:%(unexpected)s S:%(skip)s' % {
            'total': self.executor.total_count,
            'pass': self.executor.result_count.get(TestMethod.STATUS_PASS, 0),
            'fail': self.executor.result_count.get(TestMethod.STATUS_FAIL, 0),
            'error': self.executor.result_count.get(TestMethod.STATUS_ERROR, 0),
            'expected': self.executor.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0),
            'unexpected': self.executor.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0),
            'skip': self.executor.result_count.get(TestMethod.STATUS_SKIP, 0),
        }

        # Reset the buttons
        self.reset_button_states_on_end()

        # Drop the reference to the executor
        self.executor = None

    def on_executorSuiteError(self, event, error):
        "An error occurred running the test suite."
        # Display the error in a dialog
        self.run_status.text = 'Error running test suite.'

        # TODO update dialog error

        # Reset the buttons
        self.reset_button_states_on_end()

        # Drop the reference to the executor
        self.executor = None

    def reset_button_states_on_end(self):
        "A test run has ended and we should enable or disable buttons as appropriate."
        self.stop_button.enabled = False
        self.run_all_button.enabled = True
        self.set_selected_button_state()
        if self.executor and self.executor.any_failed:
            self.rerun_button.enabled = True
        else:
            self.rerun_button.enabled = False

    def set_selected_button_state(self):
        if self.executor and self.executor.is_running:
            self.run_selected_button.enabled = False
        elif self.current_test_tree.selection():
            self.run_selected_button.enabled = True
        else:
            self.run_selected_button.enabled = False

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
        self.run_status.text = 'Running...'
        self.run_summary.text = 'T:%s P:0 F:0 E:0 X:0 U:0 S:0' % count

        self.stop_button.enabled = True
        self.run_all_button.enabled = False
        self.run_selected_button.enabled = False
        self.rerun_button.enabled = False

        # TODO progress bar
        # self.progress['maximum'] = count

        # Create the runner
        self.executor = Executor(self.project, count, labels)

    def stop(self):
        "Stop the test suite."
        if self.executor and self.executor.is_running:
            self.run_status.text = 'Stopping...'

            self.executor.terminate()
            self.executor = None

            self.run_status.text = 'Stopped.'

            self.reset_button_states_on_end()

    def _hide_test_output(self):
        "Hide the test output panel on the test results page"
        self.output_box.hide()

    def _show_test_output(self, content):
        "Show the test output panel on the test results page"
        self.output_input.value = content
        self.output_box.show()

    def _hide_test_errors(self):
        "Hide the test error panel on the test results page"
        self.error_box.hide()

    def _show_test_errors(self, content):
        "Show the test error panel on the test results page"
        self.error_input.value = content
        self.error_box.show()

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

    def __init__(self, parent, title, label, trace, critical=False):
        '''Show a dialog with a scrollable stack trace.

        Arguments:

            parent -- a parent window (the application window)
            title -- the title for the stack trace window
            label -- the label describing the stack trace
            trace -- the stack trace content to display.
            critical -- indicates if the stack trace dialog will be critical
        '''
        self.parent = parent
        self.status = None

        self.button_result = self.parent.main_window.stack_trace_dialog(title,
                                                        label, trace,
                                                        retry=critical)

        if self.button_result:
            self.status = self.OK
        elif critical:
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
            False,
        )

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
            False,
        )


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
            True,
        )


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
            False,
        )
