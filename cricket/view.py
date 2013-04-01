"""A module containing a visual representation of the testApp.

This is the "View" of the MVC world.

There is a single object - the View
"""

from Tkinter import *
from tkFont import *
from ttk import *
import tkMessageBox

from cricket.widgets import ReadOnlyText
from cricket.model import TestMethod, TestCase, TestApp
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


class View(object):
    def __init__(self, project):
        self.project = project
        self.executor = None

        # Root window
        self.root = Tk()
        self.root.title('Cricket')
        self.root.geometry('1024x768')

        # Prevent the menus from having the empty tearoff entry
        self.root.option_add('*tearOff', FALSE)
        # Catch the close button
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)
        # Catch the "quit" event.
        self.root.createcommand('exit', self.on_quit)
        # Menubar
        self.menubar = Menu(self.root)

        # self.menu_testApple = Menu(self.menubar, name='testApple')
        # self.menubar.add_cascade(menu=self.menu_testApple)

        self.menu_file = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_file, label='File')

        self.menu_edit = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_edit, label='Edit')

        # self.menu_help = Menu(self.menubar, name='help')
        # self.menubar.add_cascade(menu=self.menu_help)

        # self.menu_testApple.add_command(label='Test', command=self.cmd_dummy)

        # self.menu_file.add_command(label='New', command=self.cmd_dummy, accelerator="Command-N")
        # self.menu_file.add_command(label='Open...', command=self.cmd_dummy)
        # self.menu_file.add_command(label='Close', command=self.cmd_dummy)

        # self.menu_edit.add_command(label='New', command=self.cmd_dummy)
        # self.menu_edit.add_command(label='Open...', command=self.cmd_dummy)
        # self.menu_edit.add_command(label='Close', command=self.cmd_dummy)

        # self.menu_help.add_command(label='Test', command=self.cmd_dummy)

        # last step - configure the menubar
        self.root['menu'] = self.menubar

        # Main toolbar
        self.toolbar = Frame(self.root)
        self.toolbar.grid(column=0, row=0, sticky=(W, E))

        # Buttons on the toolbar
        self.stop_button = Button(self.toolbar, text='Stop', command=self.on_stop, state=DISABLED)
        self.stop_button.grid(column=0, row=0)

        self.run_all_button = Button(self.toolbar, text='Run all', command=self.on_run_all)
        self.run_all_button.grid(column=1, row=0)

        self.run_selected_button = Button(self.toolbar, text='Run selected', command=self.on_run_selected)
        self.run_selected_button.grid(column=2, row=0)

        self.rerun_button = Button(self.toolbar, text='Re-run', command=self.on_rerun, state=DISABLED)
        self.rerun_button.grid(column=3, row=0)

        # Main content area
        self.content = PanedWindow(self.root, orient=HORIZONTAL)
        self.content.grid(column=0, row=1, sticky=(N, S, E, W))

        # The left-hand side frame on the main content area
        self.tree_frame = Frame(self.content)
        self.tree_frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.content.add(self.tree_frame)

        self.tree = Treeview(self.tree_frame)
        self.tree.grid(column=0, row=0, sticky=(N, S, E, W))

        # Populate the initial tree nodes.
        for testApp_name, testApp in sorted(self.project.items()):
            testApp_node = self.tree.insert(
                '', 'end', testApp.path,
                text=testApp.name,
                tags=['TestApp', 'active'],
                open=True)

            for testCase_name, testCase in sorted(testApp.items()):
                testCase_node = self.tree.insert(
                    testApp_node, 'end', testCase.path,
                    text=testCase.name,
                    tags=['TestCase', 'active'],
                    open=True
                )

                for testMethod_name, testMethod in sorted(testCase.items()):
                    self.tree.insert(
                        testCase_node, 'end', testMethod.path,
                        text=testMethod.name,
                        tags=['TestMethod', 'active'],
                        open=True
                    )

        # Set up the tag colors for tree nodes.
        for status, config in STATUS.items():
            self.tree.tag_configure(config['tag'], foreground=config['color'])
        self.tree.tag_configure('inactive', foreground='lightgray')

        # Listen for button clicks on tree nodes
        self.tree.tag_bind('TestApp', '<Double-Button-1>', self.on_testAppClicked)
        self.tree.tag_bind('TestCase', '<Double-Button-1>', self.on_testCaseClicked)
        self.tree.tag_bind('TestMethod', '<Double-Button-1>', self.on_testMethodClicked)

        self.tree.tag_bind('TestApp', '<<TreeviewSelect>>', self.on_testMethodSelected)
        self.tree.tag_bind('TestCase', '<<TreeviewSelect>>', self.on_testMethodSelected)
        self.tree.tag_bind('TestMethod', '<<TreeviewSelect>>', self.on_testMethodSelected)

        # Listen for any state changes on nodes in the tree
        TestApp.bind('active', self.on_nodeActive)
        TestCase.bind('active', self.on_nodeActive)
        TestMethod.bind('active', self.on_nodeActive)

        TestApp.bind('inactive', self.on_nodeInactive)
        TestCase.bind('inactive', self.on_nodeInactive)
        TestMethod.bind('inactive', self.on_nodeInactive)

        # Listen for new nodes added to the tree
        TestApp.bind('new', self.on_nodeAdded)
        TestCase.bind('new', self.on_nodeAdded)
        TestMethod.bind('new', self.on_nodeAdded)

        # Listen for any status updates on nodes in the tree.
        TestMethod.bind('status_update', self.on_nodeStatusUpdate)

        # The tree's vertical scrollbar
        self.treeScrollbar = Scrollbar(self.tree_frame, orient=VERTICAL)
        self.treeScrollbar.grid(column=1, row=0, sticky=(N, S))

        # Tie the scrollbar to the text views, and the text views
        # to each other.
        self.tree.config(yscrollcommand=self.treeScrollbar.set)
        self.treeScrollbar.config(command=self.tree.yview)

        # The right-hand side frame on the main content area
        self.details_frame = Frame(self.content)
        self.details_frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.content.add(self.details_frame)

        # Set up the content in the details panel
        # Test Name
        self.name_label = Label(self.details_frame, text='Name:')
        self.name_label.grid(column=0, row=0, pady=5, sticky=(E,))

        self.name = StringVar()
        self.name_widget = Entry(self.details_frame, textvariable=self.name)
        self.name_widget.configure(state='readonly')
        self.name_widget.grid(column=1, row=0, pady=5, sticky=(W, E))

        # Test status
        self.test_status = StringVar()
        self.test_status_widget = Label(self.details_frame, textvariable=self.test_status, width=1, anchor=CENTER)
        f = Font(font=self.test_status_widget['font'])
        f['weight'] = 'bold'
        f['size'] = 50
        self.test_status_widget.config(font=f)
        self.test_status_widget.grid(column=2, row=0, padx=15, pady=5, rowspan=2, sticky=(N, W, E, S))

        # Test duration
        self.duration_label = Label(self.details_frame, text='Duration:')
        self.duration_label.grid(column=0, row=1, pady=5, sticky=(E,))

        self.duration = StringVar()
        self.duration_widget = Entry(self.details_frame, textvariable=self.duration)
        self.duration_widget.grid(column=1, row=1, pady=5, sticky=(E, W,))

        # Test description
        self.description_label = Label(self.details_frame, text='Description:')
        self.description_label.grid(column=0, row=2, pady=5, sticky=(N, E,))

        self.description = ReadOnlyText(self.details_frame, width=80, height=4)
        self.description.grid(column=1, row=2, pady=5, columnspan=2, sticky=(N, S, E, W,))

        self.descriptionScrollbar = Scrollbar(self.details_frame, orient=VERTICAL)
        self.descriptionScrollbar.grid(column=3, row=2, pady=5, sticky=(N, S))
        self.description.config(yscrollcommand=self.descriptionScrollbar.set)
        self.descriptionScrollbar.config(command=self.description.yview)

        # Test output
        self.output_label = Label(self.details_frame, text='Output:')
        self.output_label.grid(column=0, row=3, pady=5, sticky=(N, E,))

        self.output = ReadOnlyText(self.details_frame, width=80, height=4)
        self.output.grid(column=1, row=3, pady=5, columnspan=2, sticky=(N, S, E, W,))

        self.outputScrollbar = Scrollbar(self.details_frame, orient=VERTICAL)
        self.outputScrollbar.grid(column=3, row=3, pady=5, sticky=(N, S))
        self.output.config(yscrollcommand=self.outputScrollbar.set)
        self.outputScrollbar.config(command=self.description.yview)

        # Error message
        self.error_label = Label(self.details_frame, text='Error:')
        self.error_label.grid(column=0, row=4, pady=5, sticky=(N, E,))

        self.error = ReadOnlyText(self.details_frame, width=80)
        self.error.grid(column=1, row=4, pady=5, columnspan=2, sticky=(N, S, E, W))

        self.errorScrollbar = Scrollbar(self.details_frame, orient=VERTICAL)
        self.errorScrollbar.grid(column=3, row=4, pady=5, sticky=(N, S))
        self.error.config(yscrollcommand=self.errorScrollbar.set)
        self.errorScrollbar.config(command=self.error.yview)

        # Status bar
        self.statusbar = Frame(self.root)
        self.statusbar.grid(column=0, row=2, sticky=(W, E))

        # Current status
        self.run_status = StringVar()
        self.run_status_label = Label(self.statusbar, textvariable=self.run_status)
        self.run_status_label.grid(column=0, row=0, sticky=(W, E))
        self.run_status.set('Not running')

        # Test result summary
        self.run_summary = StringVar()
        self.run_summary_label = Label(self.statusbar, textvariable=self.run_summary)
        self.run_summary_label.grid(column=1, row=0, sticky=(W, E))
        self.run_summary.set('P:0 F:0 E:0 X:0 U:0 S:0')

        # Test progress
        self.progress_value = IntVar()
        self.progress = Progressbar(self.statusbar, orient=HORIZONTAL, length=200, mode='determinate', maximum=100, variable=self.progress_value)
        self.progress.grid(column=2, row=0, sticky=(W, E))

        # Set up listeners for runner events.
        Executor.bind('test_status_update', self.on_executorStatusUpdate)
        Executor.bind('test_start', self.on_executorTestStart)
        Executor.bind('test_end', self.on_executorTestEnd)
        Executor.bind('suite_end', self.on_executorSuiteEnd)
        Executor.bind('suite_error', self.on_executorSuiteError)

        # Main window resize handle
        self.grip = Sizegrip(self.statusbar)
        self.grip.grid(column=3, row=0, sticky=(S, E))

        # Now configure the weights for the frame grids
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        self.toolbar.columnconfigure(0, weight=0)
        self.toolbar.rowconfigure(0, weight=1)

        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.content.pane(0, weight=1)
        self.content.pane(1, weight=2)

        self.statusbar.columnconfigure(0, weight=1)
        self.statusbar.columnconfigure(1, weight=0)
        self.statusbar.columnconfigure(2, weight=0)
        self.statusbar.columnconfigure(3, weight=0)
        self.statusbar.rowconfigure(0, weight=1)

        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.columnconfigure(1, weight=0)
        self.tree_frame.rowconfigure(0, weight=1)

        self.details_frame.columnconfigure(0, weight=0)
        self.details_frame.columnconfigure(1, weight=1)
        self.details_frame.columnconfigure(2, weight=0)
        self.details_frame.columnconfigure(3, weight=0)
        self.details_frame.columnconfigure(4, weight=0)
        self.details_frame.rowconfigure(0, weight=0)
        self.details_frame.rowconfigure(1, weight=0)
        self.details_frame.rowconfigure(2, weight=1)
        self.details_frame.rowconfigure(3, weight=5)
        self.details_frame.rowconfigure(4, weight=10)

        # Now that we've laid out the grid, hide the error and output text
        # until we actually have an error/output to display
        self._hide_test_output()
        self._hide_test_errors()

    def _hide_test_output(self):
        self.output_label.grid_remove()
        self.output.grid_remove()
        self.outputScrollbar.grid_remove()
        self.details_frame.rowconfigure(3, weight=0)

    def _show_test_output(self, content):
        self.output.delete('1.0', END)
        self.output.insert('1.0', content)

        self.output_label.grid()
        self.output.grid()
        self.outputScrollbar.grid()
        self.details_frame.rowconfigure(3, weight=5)

    def _hide_test_errors(self):
        self.error_label.grid_remove()
        self.error.grid_remove()
        self.errorScrollbar.grid_remove()

    def _show_test_errors(self, content):
        self.error.delete('1.0', END)
        self.error.insert('1.0', content)

        self.error_label.grid()
        self.error.grid()
        self.errorScrollbar.grid()

    def mainloop(self):
        self.root.mainloop()

    def on_quit(self):
        "Event handler: Quit"
        # If the runner is currently running, kill it.
        self.stop()

        self.root.quit()

    def on_testAppClicked(self, event):
        "Event handler: an app has been clicked in the tree"
        testApp = self.project[self.tree.focus()]

        if testApp.active:
            for testCase_name, testCase in testApp.items():
                for testMethod_name, testMethod in testCase.items():
                    testMethod.active = False
        else:
            for testCase_name, testCase in testApp.items():
                for testMethod_name, testMethod in testCase.items():
                    testMethod.active = True

    def on_testCaseClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        testApp_name, testCase_name = self.tree.focus().split('.')
        testCase = self.project[testApp_name][testCase_name]

        if testCase.active:
            for testMethod_name, testMethod in testCase.items():
                testMethod.active = False
        else:
            for testMethod_name, testMethod in testCase.items():
                testMethod.active = True

    def on_testMethodClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        testApp_name, testCase_name, testMethod_name = self.tree.focus().split('.')
        testMethod = self.project[testApp_name][testCase_name][testMethod_name]

        testMethod.toggle_active()

    def on_testMethodSelected(self, event):
        "Event handler: a test case has been selected in the tree"
        if len(self.tree.selection()) == 1:
            parts = self.tree.selection()[0].split('.')
            if len(parts) == 3:
                # Individual test selected.
                testApp_name, testCase_name, testMethod_name = parts
                testMethod = self.project[testApp_name][testCase_name][testMethod_name]

                self.name.set(testMethod.path)

                self.description.delete('1.0', END)
                self.description.insert('1.0', testMethod.description)

                config = STATUS.get(testMethod.status, STATUS_DEFAULT)
                self.test_status_widget.config(foreground=config['color'])
                self.test_status.set(config['symbol'])

                if testMethod._result:
                    # Test has been executed
                    self.duration.set('%0.2fs' % testMethod._result['duration'])

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
                    self.duration.set('Not executed')

                    self._hide_test_output()
                    self._hide_test_errors()
            else:
                # Test class/app selected
                self.name.set('')
                self.test_status.set('')

                self.duration.set('')
                self.description.delete('1.0', END)

                self._hide_test_output()
                self._hide_test_errors()

        else:
            # Multiple tests selected
            self.name.set('')
            self.test_status.set('')

            self.duration.set('')
            self.description.delete('1.0', END)

            self._hide_test_output()
            self._hide_test_errors()

    def on_nodeAdded(self, node):
        "Event handler: a new node has been added to the tree"
        self.tree.insert(
            node.parent.path, 'end', node.path,
            text=node.name,
            tags=[node.__class__.__name__, 'active'],
            open=True
        )

    def on_nodeActive(self, node):
        "Event handler: a node on the tree has been made active"
        self.tree.item(node.path, tags=[node.__class__.__name__, 'active'])
        self.tree.item(node.path, open=True)

    def on_nodeInactive(self, node):
        "Event handler: a node on the tree has been made inactive"
        self.tree.item(node.path, tags=[node.__class__.__name__, 'inactive'])
        self.tree.item(node.path, open=False)

    def on_nodeStatusUpdate(self, node):
        "Event handler: a node on the tree has received a status update"
        self.tree.item(node.path, tags=['TestMethod', STATUS[node.status]['tag']])

    def on_stop(self, event=None):
        "Event handler: The stop button has been pressed"
        self.stop()

    def _run(self, active=True, status=None, labels=None):
        count, labels = self.project.find_tests(active, status, labels)

        self.run_status.set('Running...')
        self.run_summary.set('P:0 F:0 E:0 X:0 U:0 S:0')

        self.stop_button.configure(state=NORMAL)
        self.run_all_button.configure(state=DISABLED)
        self.run_selected_button.configure(state=DISABLED)
        self.rerun_button.configure(state=DISABLED)

        self.progress['maximum'] = count
        self.progress_value.set(0)

        # Create the runner
        self.executor = Executor(self.project, count, labels)

        # Queue the first progress handling event
        self.root.after(100, self.on_testProgress)

    def stop(self):
        "Stop the test suite."
        if self.executor and self.executor.is_running:
            self.run_status.set('Stopping...')

            self.executor.terminate()
            self.executor = None

            self.run_status.set('Stopped.')

            self.stop_button.configure(state=DISABLED)
            self.run_all_button.configure(state=NORMAL)
            self.run_selected_button.configure(state=NORMAL)
            self.rerun_button.configure(state=NORMAL)

    def on_run_all(self, event=None):
        "Event handler: The Run all button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self._run(active=True)

    def on_run_selected(self, event=None):
        "Event handler: The 'run selected' button has been pressed"

        # If a node is selected, it needs to be made active
        for path in self.tree.selection():
            parts = path.split('.')
            if len(parts) == 1:
                self.project[parts[0]].active = True
            elif len(parts) == 2:
                self.project[parts[0]][parts[1]].active = True
            elif len(parts) == 3:
                self.project[parts[0]][parts[1]][parts[2]].active = True

        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self._run(labels=set(self.tree.selection()))

    def on_rerun(self, event=None):
        "Event handler: The run/stop button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self._run(status=set(TestMethod.FAILING_STATES))

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
        self.tree.item(test_path, tags=['TestMethod', 'active'])

    def on_executorTestEnd(self, event, test_path, remaining_time):
        "The executor has finished running a test."
        # Update the progress meter
        self.progress_value.set(self.progress_value.get() + 1)

        # Update the run summary
        self.run_summary.set('P:%(pass)s F:%(fail)s E:%(error)s X:%(expected)s U:%(unexpected)s S:%(skip)s, ~%(remaining)s remaining' % {
                'pass': self.executor.result_count.get(TestMethod.STATUS_PASS, 0),
                'fail': self.executor.result_count.get(TestMethod.STATUS_FAIL, 0),
                'error': self.executor.result_count.get(TestMethod.STATUS_ERROR, 0),
                'expected': self.executor.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0),
                'unexpected': self.executor.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0),
                'skip': self.executor.result_count.get(TestMethod.STATUS_SKIP, 0),
                'remaining': remaining_time
            })

        # If the test that just fininshed is the one (and only one)
        # selected on the tree, update the display.
        if len(self.tree.selection()) == 1 and self.tree.selection()[0] == test_path:
            self.on_testMethodSelected(None)

    def on_executorSuiteEnd(self, event):
        "The test suite finished running."
        # Display the final results
        self.run_status.set('Finished.')
        if sum(self.executor.result_count.get(state, 0) for state in TestMethod.FAILING_STATES):
            dialog = tkMessageBox.showerror
        else:
            dialog = tkMessageBox.showinfo

        dialog(message=', '.join(
            '%d %s' % (count, TestMethod.STATUS_LABELS[state])
            for state, count in sorted(self.executor.result_count.items()))
        )

        # Reset the running summary.
        self.run_summary.set('P:%(pass)s F:%(fail)s E:%(error)s X:%(expected)s U:%(unexpected)s S:%(skip)s' % {
                'pass': self.executor.result_count.get(TestMethod.STATUS_PASS, 0),
                'fail': self.executor.result_count.get(TestMethod.STATUS_FAIL, 0),
                'error': self.executor.result_count.get(TestMethod.STATUS_ERROR, 0),
                'expected': self.executor.result_count.get(TestMethod.STATUS_EXPECTED_FAIL, 0),
                'unexpected': self.executor.result_count.get(TestMethod.STATUS_UNEXPECTED_SUCCESS, 0),
                'skip': self.executor.result_count.get(TestMethod.STATUS_SKIP, 0),
            })

        # Reset the buttons
        self.stop_button.configure(state=DISABLED)
        self.run_all_button.configure(state=NORMAL)
        self.run_selected_button.configure(state=NORMAL)
        self.rerun_button.configure(state=NORMAL)

        # Drop the reference to the executor
        self.executor = None

    def on_executorSuiteError(self, event, error):
        "An error occurred running the test suite."
        # Display the error
        self.run_status.set('Error running test suite.')
        tkMessageBox.showerror(message='Error running test suite:\n' + error)

        # Reset the buttons
        self.stop_button.configure(state=DISABLED)
        self.run_all_button.configure(state=NORMAL)
        self.run_selected_button.configure(state=NORMAL)
        self.rerun_button.configure(state=NORMAL)

        # Drop the reference to the executor
        self.executor = None
