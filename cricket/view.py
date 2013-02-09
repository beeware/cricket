"""A module containing a visual representation of the testApp.

This is the "View" of the MVC world.

There is a single object - the View
"""

import fcntl
import os
import subprocess


from Tkinter import *
from ttk import *

from cricket.widgets import ReadOnlyText
from cricket.model import TestMethod, TestCase, TestApp
from cricket.pipes import PipedTestResult, PipedTestRunner


class View(object):
    def __init__(self, model):
        self.model = model
        self.test_runner = None

        # The last progress command issued by the user.
        # When we start, set this to run_stop so that the
        # default action is to start running.
        self.last_command = self.on_run_stop

        # Root window
        self.root = Tk()
        self.root.title('Cricket')
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
        self.run_stop_button = Button(self.toolbar, text='Run', command=self.on_run_stop)
        self.run_stop_button.grid(column=0, row=0)

        # Main content area
        self.content = PanedWindow(self.root, orient=HORIZONTAL)
        self.content.grid(column=0, row=1, sticky=(N, S, E, W))

        # The left-hand side frame on the main content area
        self.tree_frame = Frame(self.content)
        self.tree_frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.content.add(self.tree_frame)

        self.tree = Treeview(self.tree_frame)
        self.tree.grid(column=0, row=0, sticky=(N, S, E, W))

        for testApp_name, testApp in sorted(self.model.items()):
            testApp_node = self.tree.insert('', 'end', testApp.path,
                text=testApp.name,
                tags=['TestApp', 'active'],
                open=True)

            for testCase_name, testCase in sorted(testApp.items()):
                testCase_node = self.tree.insert(testApp_node, 'end', testCase.path,
                    text=testCase.name,
                    tags=['TestCase', 'active'],
                    open=True
                )

                for testMethod_name, testMethod in sorted(testCase.items()):
                    self.tree.insert(testCase_node, 'end', testMethod.path,
                        text=testMethod.name,
                        tags=['TestMethod', 'active'],
                        open=True
                    )

        self.tree.tag_configure('fail', foreground='red')
        self.tree.tag_configure('pass', foreground='green')
        self.tree.tag_configure('inactive', foreground='lightgray')

        self.tree.tag_bind('TestApp', '<Double-Button-1>', self.on_testAppClicked)
        self.tree.tag_bind('TestCase', '<Double-Button-1>', self.on_testCaseClicked)
        self.tree.tag_bind('TestMethod', '<Double-Button-1>', self.on_testMethodClicked)

        TestApp.bind('active', self.on_nodeActive)
        TestCase.bind('active', self.on_nodeActive)
        TestMethod.bind('active', self.on_nodeActive)

        TestApp.bind('inactive', self.on_nodeInactive)
        TestCase.bind('inactive', self.on_nodeInactive)
        TestMethod.bind('inactive', self.on_nodeInactive)

        TestApp.bind('new', self.on_nodeAdded)
        TestCase.bind('new', self.on_nodeAdded)
        TestMethod.bind('new', self.on_nodeAdded)

        TestMethod.bind('status_update', self.on_nodeStatusUpdate)

        # The tree's vertical scrollbar
        self.vScrollbar = Scrollbar(self.tree_frame, orient=VERTICAL)
        self.vScrollbar.grid(column=1, row=0, sticky=(N, S))

        # Tie the scrollbar to the text views, and the text views
        # to each other.
        self.tree.config(yscrollcommand=self.vScrollbar.set)
        self.vScrollbar.config(command=self.tree.yview)

        # The right-hand side frame on the main content area
        self.details_frame = Frame(self.content)
        self.details_frame.grid(column=0, row=0, sticky=(N, S, E, W))
        self.content.add(self.details_frame)

        self.details = ReadOnlyText(self.details_frame)
        self.details.grid(column=0, row=0, sticky=(N, S, E, W))

        # Status bar
        self.statusbar = Frame(self.root)
        self.statusbar.grid(column=0, row=2, sticky=(W, E))

        # Current status
        self.status = StringVar()
        self.status_label = Label(self.statusbar, textvariable=self.status)
        self.status_label.grid(column=0, row=0, sticky=(W, E))
        self.status.set('Not running')

        # Test progress
        self.progress_value = IntVar()
        self.progress = Progressbar(self.statusbar, orient=HORIZONTAL, length=200, mode='determinate', maximum=100, variable=self.progress_value)
        self.progress.grid(column=1, row=0, sticky=(W, E))

        # TODO - hook up the progress bar.
        # self.progress_value.set(42)
        # self.progress['value'] = 42
        # self.progress['maximum'] = 142

        # Main window resize handle
        self.grip = Sizegrip(self.statusbar)
        self.grip.grid(column=2, row=0, sticky=(S, E))

        # Now configure the weights for the frame grids
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        self.toolbar.columnconfigure(0, weight=0)
        self.toolbar.rowconfigure(0, weight=1)

        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.statusbar.columnconfigure(0, weight=1)
        self.statusbar.columnconfigure(1, weight=0)
        self.statusbar.columnconfigure(2, weight=0)
        self.statusbar.rowconfigure(0, weight=1)

        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.columnconfigure(1, weight=0)
        self.tree_frame.rowconfigure(0, weight=1)

        self.details_frame.columnconfigure(0, weight=1)
        self.details_frame.rowconfigure(0, weight=1)

    def mainloop(self):
        self.root.mainloop()

    def on_quit(self):
        "Event handler: Quit"
        if self.test_runner:
            self.status.set('Stopping...')

            self.test_runner.terminate()
            self.test_runner = None

        self.root.quit()

    def on_testAppClicked(self, event):
        "Event handler: an app has been clicked in the tree"
        testApp = self.model[self.tree.focus()]

        if testApp.active:
            self.tree.item(self.tree.focus(), open=True)
            for testCase_name, testCase in testApp.items():
                for testMethod_name, testMethod in testCase.items():
                    testMethod.active = False
        else:
            self.tree.item(self.tree.focus(), open=False)
            for testCase_name, testCase in testApp.items():
                for testMethod_name, testMethod in testCase.items():
                    testMethod.active = True

    def on_testCaseClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        testApp_name, testCase_name = self.tree.focus().split('.')
        testCase = self.model[testApp_name][testCase_name]

        if testCase.active:
            self.tree.item(self.tree.focus(), open=True)
            for testMethod_name, testMethod in testCase.items():
                testMethod.active = False
        else:
            for testMethod_name, testMethod in testCase.items():
                testMethod.active = True
            self.tree.item(self.tree.focus(), open=False)

    def on_testMethodClicked(self, event):
        "Event handler: a test case has been clicked in the tree"
        testApp_name, testCase_name, testMethod_name = self.tree.focus().split('.')
        testMethod = self.model[testApp_name][testCase_name][testMethod_name]

        testMethod.toggle_active()

    def on_nodeAdded(self, node):
        "Event handler: a new node has been added to the tree"
        self.tree.insert(node.parent.path, 'end', node.path,
                                text=testMethod.name,
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
        self.tree.item(node.path, tags=['TestMethod', node.status_tag])

    def on_run_stop(self, event=None):
        "Event handler: The run/stop button has been pressed"

        # Check to see if the test runner exists, and if it does,
        # poll to check if it is still running.
        if self.test_runner is not None:
            self.test_runner.poll()

        if self.test_runner is None or self.test_runner.returncode is not None:
            self.status.set('Running...')
            self.run_stop_button.configure(text='Stop')

            self.test_runner = subprocess.Popen(
                ['python', 'manage.py', 'test', '--testrunner=cricket.runners.TestExecutor'] + self.model.test_labels,
                stdin=None,
                stdout=subprocess.PIPE,
                stderr=None,
                shell=False,
                bufsize=1,
            )
            # Probably only works on UNIX-alikes.
            # Windows users should feel free to suggest an alternative.
            fcntl.fcntl(self.test_runner.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

            # Data storage for test results.
            #  - buffer holds the character buffer being read from stdout
            #  - test is the test currently under execution
            #  - lines is an accumulator of extra test output.
            #    If lines is None, there's no test currently under execution
            self.result = {
                'buffer': [],
                'test': None,
                'lines': None,
            }

            # Queue the first progress handling event
            self.root.after(100, self.on_testProgress)

        else:
            self.status.set('Stopping...')

            self.test_runner.terminate()
            self.test_runner = None

            self.status.set('Stopped.')
            self.run_stop_button.configure(text='Run')

    def on_testProgress(self):
        "Event handler: a periodic update to read stdout, and turn that into GUI updates"
        finished = False
        stopped = False

        # Read from stdout, building a buffer.
        lines = []
        try:
            while True:
                ch = self.test_runner.stdout.read(1)
                if ch == '\n':
                    lines.append(''.join(self.result['buffer']))
                    self.result['buffer'] = []
                elif ch == '':
                    # An indicator that stdout is no longer
                    # available.
                    raise IOError()
                else:
                    self.result['buffer'].append(ch)
        except IOError:
            # No data available on stdout
            pass
        except AttributeError:
            # stdout has gone away; probably due to process being killed.
            stopped = True

        # Process all the full lines that are available
        for line in lines:
            if line in (PipedTestResult.separator, PipedTestRunner.separator):
                if self.result['lines'] is None:
                    # Preamble is finished. Set up the line buffer.
                    self.result['lines'] = []
                else:
                    # Start of new test result; record the last result
                    if self.result['lines'][1] == 'result: OK':
                        status = TestMethod.STATUS_PASS
                        error = None
                    elif self.result['lines'][1] == 'result: s':
                        status = TestMethod.STATUS_SKIP
                        error = None
                    elif self.result['lines'][1] == 'result: F':
                        status = TestMethod.STATUS_FAIL
                        error = '\n'.join(self.result['lines'][2:-1])
                    elif self.result['lines'][1] == 'result: x':
                        status = TestMethod.STATUS_EXPECTED_FAIL
                        error = None
                    elif self.result['lines'][1] == 'result: u':
                        status = TestMethod.STATUS_UNEXPECTED_SUCCESS
                        error = None
                    elif self.result['lines'][1] == 'result: E':
                        status = TestMethod.STATUS_ERROR
                        error = '\n'.join(self.result['lines'][2:-1])

                    start_time = self.result['lines'][0][7:]
                    end_time = self.result['lines'][-1][5:]

                    self.result['test'].set_result(
                        status=status,
                        error=error,
                        duration=float(end_time) - float(start_time),
                    )

                    # Clear the decks for the next test.
                    self.result['test'] = None
                    self.result['lines'] = []

                    if line == PipedTestRunner.separator:
                        # End of test execution.
                        # Mark the runner as finished, and move back
                        # to a pre-test state in the results.
                        finished = True
                        self.result['lines'] = None

                        self.status.set('Finished.')
                        self.run_stop_button.configure(text='Run')

            else:
                if self.result['lines'] is None:
                    self.status.set(line)
                else:
                    if self.result['test'] is None:
                        self.status.set('Running %s...' % line)
                        self.tree.see(line)
                        self.tree.item(line, tags=['TestMethod', 'active'])

                        self.result['test'] = self.model.confirm_exists(line)
                    else:
                        self.result['lines'].append(line)

        # If we're not finished, requeue the event.
        if finished:
            self.status.set('Finished.')
            self.run_stop_button.configure(text='Run')
        elif not stopped:
            self.root.after(100, self.on_testProgress)
