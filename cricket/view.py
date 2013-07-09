"""A module containing a visual representation of the testModule.

This is the "View" of the MVC world.
"""

from Tkinter import *
from tkFont import *
from ttk import *
import tkMessageBox

from cricket.widgets import ReadOnlyText
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


class MainWindow(object):
    def __init__(self, root):
        self._project = None
        self.executor = None

        # Root window
        self.root = root
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

        # self.menu_Apple = Menu(self.menubar, name='Apple')
        # self.menubar.add_cascade(menu=self.menu_Apple)

        self.menu_file = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_file, label='File')

        self.menu_edit = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.menu_edit, label='Edit')

        # self.menu_help = Menu(self.menubar, name='help')
        # self.menubar.add_cascade(menu=self.menu_help)

        # self.menu_Apple.add_command(label='Test', command=self.cmd_dummy)

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
        # The tabs for the two trees
        self.tree_notebook = Notebook(self.content, padding=(0, 5, 0, 5))
        self.content.add(self.tree_notebook)

        # The tree for all tests
        self.all_tests_tree_frame = Frame(self.content)
        self.all_tests_tree_frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.tree_notebook.add(self.all_tests_tree_frame, text='All tests')

        self.all_tests_tree = Treeview(self.all_tests_tree_frame)
        self.all_tests_tree.grid(column=0, row=0, sticky=(N, S, E, W))

        # Set up the tag colors for tree nodes.
        for status, config in STATUS.items():
            self.all_tests_tree.tag_configure(config['tag'], foreground=config['color'])
        self.all_tests_tree.tag_configure('inactive', foreground='lightgray')

        # Listen for button clicks on tree nodes
        self.all_tests_tree.tag_bind('TestModule', '<Double-Button-1>', self.on_testModuleClicked)
        self.all_tests_tree.tag_bind('TestCase', '<Double-Button-1>', self.on_testCaseClicked)
        self.all_tests_tree.tag_bind('TestMethod', '<Double-Button-1>', self.on_testMethodClicked)

        self.all_tests_tree.tag_bind('TestModule', '<<TreeviewSelect>>', self.on_testModuleSelected)
        self.all_tests_tree.tag_bind('TestCase', '<<TreeviewSelect>>', self.on_testCaseSelected)
        self.all_tests_tree.tag_bind('TestMethod', '<<TreeviewSelect>>', self.on_testMethodSelected)

        # The tree's vertical scrollbar
        self.all_tests_tree_scrollbar = Scrollbar(self.all_tests_tree_frame, orient=VERTICAL)
        self.all_tests_tree_scrollbar.grid(column=1, row=0, sticky=(N, S))

        # Tie the scrollbar to the text views, and the text views
        # to each other.
        self.all_tests_tree.config(yscrollcommand=self.all_tests_tree_scrollbar.set)
        self.all_tests_tree_scrollbar.config(command=self.all_tests_tree.yview)

        # The tree for problem tests
        self.problems_tree_frame = Frame(self.content)
        self.problems_tree_frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.tree_notebook.add(self.problems_tree_frame, text='Problems')

        self.problems_tree = Treeview(self.problems_tree_frame)
        self.problems_tree.grid(column=0, row=0, sticky=(N, S, E, W))

        # Set up the tag colors for tree nodes.
        for status, config in STATUS.items():
            self.problems_tree.tag_configure(config['tag'], foreground=config['color'])
        self.problems_tree.tag_configure('inactive', foreground='lightgray')

        # Problem tree only deals with selection, not clicks.
        self.problems_tree.tag_bind('TestModule', '<<TreeviewSelect>>', self.on_testModuleSelected)
        self.problems_tree.tag_bind('TestCase', '<<TreeviewSelect>>', self.on_testCaseSelected)
        self.problems_tree.tag_bind('TestMethod', '<<TreeviewSelect>>', self.on_testMethodSelected)

        # The tree's vertical scrollbar
        self.problems_tree_scrollbar = Scrollbar(self.problems_tree_frame, orient=VERTICAL)
        self.problems_tree_scrollbar.grid(column=1, row=0, sticky=(N, S))

        # Tie the scrollbar to the text views, and the text views
        # to each other.
        self.problems_tree.config(yscrollcommand=self.problems_tree_scrollbar.set)
        self.problems_tree_scrollbar.config(command=self.all_tests_tree.yview)

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

        self.description_scrollbar = Scrollbar(self.details_frame, orient=VERTICAL)
        self.description_scrollbar.grid(column=3, row=2, pady=5, sticky=(N, S))
        self.description.config(yscrollcommand=self.description_scrollbar.set)
        self.description_scrollbar.config(command=self.description.yview)

        # Test output
        self.output_label = Label(self.details_frame, text='Output:')
        self.output_label.grid(column=0, row=3, pady=5, sticky=(N, E,))

        self.output = ReadOnlyText(self.details_frame, width=80, height=4)
        self.output.grid(column=1, row=3, pady=5, columnspan=2, sticky=(N, S, E, W,))

        self.output_scrollbar = Scrollbar(self.details_frame, orient=VERTICAL)
        self.output_scrollbar.grid(column=3, row=3, pady=5, sticky=(N, S))
        self.output.config(yscrollcommand=self.output_scrollbar.set)
        self.output_scrollbar.config(command=self.description.yview)

        # Error message
        self.error_label = Label(self.details_frame, text='Error:')
        self.error_label.grid(column=0, row=4, pady=5, sticky=(N, E,))

        self.error = ReadOnlyText(self.details_frame, width=80)
        self.error.grid(column=1, row=4, pady=5, columnspan=2, sticky=(N, S, E, W))

        self.error_scrollbar = Scrollbar(self.details_frame, orient=VERTICAL)
        self.error_scrollbar.grid(column=3, row=4, pady=5, sticky=(N, S))
        self.error.config(yscrollcommand=self.error_scrollbar.set)
        self.error_scrollbar.config(command=self.error.yview)

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

        self.all_tests_tree_frame.columnconfigure(0, weight=1)
        self.all_tests_tree_frame.columnconfigure(1, weight=0)
        self.all_tests_tree_frame.rowconfigure(0, weight=1)

        self.problems_tree_frame.columnconfigure(0, weight=1)
        self.problems_tree_frame.columnconfigure(1, weight=0)
        self.problems_tree_frame.rowconfigure(0, weight=1)

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

    ######################################################
    # Handlers for setting a new project
    ######################################################

    @property
    def project(self):
        return self._project

    def _add_test_module(self, parentNode, testModule):
        testModule_node = self.all_tests_tree.insert(
            parentNode, 'end', testModule.path,
            text=testModule.name,
            tags=['TestModule', 'active'],
            open=True)

        for subModuleName, subModule in sorted(testModule.items()):
            if isinstance(subModule, TestModule):
                self._add_test_module(testModule_node, subModule)
            else:
                testCase = subModule
                testCase_node = self.all_tests_tree.insert(
                    testModule_node, 'end', testCase.path,
                    text=testCase.name,
                    tags=['TestCase', 'active'],
                    open=True
                )

                for testMethod_name, testMethod in sorted(testCase.items()):
                    self.all_tests_tree.insert(
                        testCase_node, 'end', testMethod.path,
                        text=testMethod.name,
                        tags=['TestMethod', 'active'],
                        open=True
                    )

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
    # TK Main loop
    ######################################################

    def mainloop(self):
        self.root.mainloop()

    ######################################################
    # GUI Callbacks
    ######################################################

    def on_quit(self):
        "Event handler: Quit"
        # If the runner is currently running, kill it.
        self.stop()

        self.root.quit()

    def on_testModuleClicked(self, event):
        "Event handler: a module has been clicked in the tree"
        parts = event.widget.focus().split('.')
        testModule = self.project
        for part in parts:
            testModule = testModule[part]

        testModule.toggle_active()

    def on_testCaseClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        parts = event.widget.focus().split('.')
        testCase = self.project
        for part in parts:
            testCase = testCase[part]

        testCase.toggle_active()

    def on_testMethodClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        parts = event.widget.focus().split('.')
        testMethod = self.project
        for part in parts:
            testMethod = testMethod[part]

        testMethod.toggle_active()

    def on_testModuleSelected(self, event):
        "Event handler: a test module has been selected in the tree"
        self.name.set('')
        self.test_status.set('')

        self.duration.set('')
        self.description.delete('1.0', END)

        self._hide_test_output()
        self._hide_test_errors()

    def on_testCaseSelected(self, event):
        "Event handler: a test case has been selected in the tree"
        self.name.set('')
        self.test_status.set('')

        self.duration.set('')
        self.description.delete('1.0', END)

        self._hide_test_output()
        self._hide_test_errors()

    def on_testMethodSelected(self, event):
        "Event handler: a test case has been selected in the tree"
        if len(event.widget.selection()) == 1:
            parts = event.widget.selection()[0].split('.')

            # Find the definition for the actual test method
            # out of the project.
            testMethod = self.project
            for part in parts:
                testMethod = testMethod[part]

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
            # Multiple tests selected
            self.name.set('')
            self.test_status.set('')

            self.duration.set('')
            self.description.delete('1.0', END)

            self._hide_test_output()
            self._hide_test_errors()

    def on_nodeAdded(self, node):
        "Event handler: a new node has been added to the tree"
        self.all_tests_tree.insert(
            node.parent.path, 'end', node.path,
            text=node.name,
            tags=[node.__class__.__name__, 'active'],
            open=True
        )

    def on_nodeActive(self, node):
        "Event handler: a node on the tree has been made active"
        self.all_tests_tree.item(node.path, tags=[node.__class__.__name__, 'active'])
        self.all_tests_tree.item(node.path, open=True)

    def on_nodeInactive(self, node):
        "Event handler: a node on the tree has been made inactive"
        self.all_tests_tree.item(node.path, tags=[node.__class__.__name__, 'inactive'])
        self.all_tests_tree.item(node.path, open=False)

    def on_nodeStatusUpdate(self, node):
        "Event handler: a node on the tree has received a status update"
        self.all_tests_tree.item(node.path, tags=['TestMethod', STATUS[node.status]['tag']])

        if node.status in TestMethod.FAILING_STATES:
            # Test is in a failing state. Make sure it is on the problem tree,
            # with the correct current status.

            parts = node.path.split('.')
            parentModule = self.project
            for pos, part in enumerate(parts):
                path = '.'.join(parts[:pos+1])
                testModule = parentModule[part]

                if not self.problems_tree.exists(path):
                    self.problems_tree.insert(
                        parentModule.path, 'end', testModule.path,
                        text=testModule.name,
                        tags=[testModule.__class__.__name__, 'active'],
                        open=True
                    )

                parentModule = testModule

            self.problems_tree.item(node.path, tags=['TestMethod', STATUS[node.status]['tag']])
        else:
            # Test passed; if it's on the problem tree, remove it.
            if self.problems_tree.exists(node.path):
                self.problems_tree.delete(node.path)

                # Check all parents of this node. Recursively remove
                # any parent has no children as a result of this deletion.
                has_children = False
                node = node.parent
                while node.path and not has_children:
                    if not self.problems_tree.get_children(node.path):
                        self.problems_tree.delete(node.path)
                    else:
                        has_children = True
                    node = node.parent

    def on_stop(self, event=None):
        "Event handler: The stop button has been pressed"
        self.stop()

    def on_run_all(self, event=None):
        "Event handler: The Run all button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self.run(active=True)

    def on_run_selected(self, event=None):
        "Event handler: The 'run selected' button has been pressed"
        # Check the tree notebook to see which tree
        # is currently selected.
        current_tree_id = self.tree_notebook.select()
        if current_tree_id == self.problems_tree_frame._w:
            current_tree = self.problems_tree
        else:
            current_tree = self.all_tests_tree

        # If a node is selected, it needs to be made active
        for path in current_tree.selection():
            parts = path.split('.')
            testModule = self.project
            for part in parts:
                testModule = testModule[part]

            testModule.set_active(True)

        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self.run(labels=set(current_tree.selection()))

    def on_rerun(self, event=None):
        "Event handler: The run/stop button has been pressed"
        # If the executor isn't currently running, we can
        # start a test run.
        if not self.executor or not self.executor.is_running:
            self.run(status=set(TestMethod.FAILING_STATES))

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
        self.all_tests_tree.item(test_path, tags=['TestMethod', 'active'])

    def on_executorTestEnd(self, event, test_path, result, remaining_time):
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
        current_tree_id = self.tree_notebook.select()
        if current_tree_id == self.problems_tree_frame._w:
            current_tree = self.problems_tree
        else:
            current_tree = self.all_tests_tree

        if len(current_tree.selection()) == 1:
            # One test selected.
            if current_tree.selection()[0] == test_path:
                # If the test that just finished running is the selected
                # test, force reset the selection, which will generate a
                # selection event, forcing a refresh of the result page.
                current_tree.selection_set(current_tree.selection())
        else:
            # No or Multiple tests selected
            self.name.set('')
            self.test_status.set('')

            self.duration.set('')
            self.description.delete('1.0', END)

            self._hide_test_output()
            self._hide_test_errors()

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
        # Display the error in a dialog
        self.run_status.set('Error running test suite.')
        FailedTestDialog(self.root, error)

        # Reset the buttons
        self.stop_button.configure(state=DISABLED)
        self.run_all_button.configure(state=NORMAL)
        self.run_selected_button.configure(state=NORMAL)
        self.rerun_button.configure(state=NORMAL)

        # Drop the reference to the executor
        self.executor = None

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

    def _hide_test_output(self):
        "Hide the test output panel on the test results page"
        self.output_label.grid_remove()
        self.output.grid_remove()
        self.output_scrollbar.grid_remove()
        self.details_frame.rowconfigure(3, weight=0)

    def _show_test_output(self, content):
        "Show the test output panel on the test results page"
        self.output.delete('1.0', END)
        self.output.insert('1.0', content)

        self.output_label.grid()
        self.output.grid()
        self.output_scrollbar.grid()
        self.details_frame.rowconfigure(3, weight=5)

    def _hide_test_errors(self):
        "Hide the test error panel on the test results page"
        self.error_label.grid_remove()
        self.error.grid_remove()
        self.error_scrollbar.grid_remove()

    def _show_test_errors(self, content):
        "Show the test error panel on the test results page"
        self.error.delete('1.0', END)
        self.error.insert('1.0', content)

        self.error_label.grid()
        self.error.grid()
        self.error_scrollbar.grid()


class StackTraceDialog(Toplevel):
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
        Toplevel.__init__(self, parent)

        self.withdraw()  # remain invisible for now

        # If the master is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        if parent.winfo_viewable():
            self.transient(parent)

        self.title(title)

        self.parent = parent

        self.frame = Frame(self)
        self.frame.grid(column=0, row=0, sticky=(N, S, E, W))

        self.label = Label(self.frame, text=label)
        self.label.grid(column=0, row=0, padx=5, pady=5, sticky=(W, E))

        self.description = ReadOnlyText(self.frame, width=80, height=20)
        self.description.grid(column=0, columnspan=2, row=1, pady=5, sticky=(N, S, E, W,))

        self.description_scrollbar = Scrollbar(self.frame, orient=VERTICAL)
        self.description_scrollbar.grid(column=1, row=1, pady=5, sticky=(N, S, E))
        self.description.config(yscrollcommand=self.description_scrollbar.set)
        self.description_scrollbar.config(command=self.description.yview)

        self.description.insert('1.0', trace)

        self.cancel_button = Button(self.frame, text=cancel_text, command=self.cancel)
        self.cancel_button.grid(column=0, row=2, padx=5, pady=5, sticky=(E,))

        self.ok_button = Button(self.frame, text=button_text, command=self.ok, default=ACTIVE)
        self.ok_button.grid(column=1, row=2, padx=5, pady=5, sticky=(E,))


        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=0)

        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=0)

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind('<Return>', self.ok)

        if self.parent is not None:
            self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                      parent.winfo_rooty()+50))

        self.deiconify()  # become visible now

        self.ok_button.focus_set()

        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def ok(self, event=None):
        self.withdraw()
        self.update_idletasks()

        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()
        self.status = self.OK

    def cancel(self, event=None):
        self.withdraw()
        self.update_idletasks()

        if self.parent is not None:
            self.parent.focus_set()

        self.destroy()
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
        self.parent.quit()


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
        self.parent.quit()


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
