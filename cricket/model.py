"""A module containing a data representation for the test suite.

This is the "Model" of the MVC world.

Each object in the model is an event source; views/controllers
can bind to events on the model to be notified of changes.
"""
import subprocess
import sys
from datetime import datetime

import toga
from toga.sources import Source


class ModelLoadError(Exception):
    def __init__(self, trace):
        super(ModelLoadError, self).__init__()
        self.trace = trace


class TestNode:
    def __init__(self, project, prefix, name):
        super().__init__()
        self._child_labels = []
        self._child_nodes = {}

        self._project = project
        self._prefix = prefix
        self.name = name
        self._active = True

    ######################################################################
    # Methods required by the TreeSource interface
    ######################################################################

    def __len__(self):
        return len(self._child_labels)

    def __getitem__(self, index):
        return self._child_nodes[self._child_labels[index]]

    def has_children(self):
        return True

    ######################################################################
    # Methods used by Cricket
    ######################################################################

    @property
    def path(self):
        "The dotted-path name that identifies this test method to the test runner"
        if self._prefix:
            return '{}.{}'.format(self._prefix, self.name)
        return self.name

    @property
    def label(self):
        "The display label for the node"
        return self.name

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

    def confirm_exists(self, test_label):
        """Confirm that the given test label exists in the current data model.

        If it doesn't, create a representation for it.
        """
        parts = test_label.split('.')

        if len(parts) == 1:
            TestClass = TestMethod
        elif len(parts) == 2:
            TestClass = TestCase
        else:
            TestClass = TestModule

        try:
            child = self._child_nodes[parts[0]]
        except KeyError:
            child = TestClass(self._project, self.path, parts[0])
            self._child_labels.append(parts[0])
            self._child_nodes[parts[0]] = child

        if len(parts) > 1:
            test = child.confirm_exists('.'.join(parts[1:]))
        else:
            test = child

        return test

    def find_tests(self, active=True, status=None):
        """Find the test labels matching the search criteria.

        Returns a count of tests found, plus the labels needed to
        execute those tests.
        """
        tests = []
        count = 0

        found_partial = False
        for child_label, child_node in self._child_nodes.items():
            include = True

            # If only active tests have been requested, the module
            # must be active.
            if active and not child_node.active:
                include = False

            subcount, subtests = child_node.find_tests(active, status)

            if include:
                count = count + subcount

                if isinstance(subtests, list):
                    found_partial = True
                    tests.extend(subtests)
                else:
                    tests.append(subtests)

        # No partials found; just reference the app.
        if not found_partial:
            return count, []

        return count, tests


class TestMethod:
    """A data representation of an individual test method.

    Emits:
        * 'new' when a new node is added
        * 'inactive' when the test method is made inactive in the suite.
        * 'active' when the test method is made active in the suite.
        * 'status_update' when the pass/fail status of the method is updated.
    """
    STATUS_UNKNOWN = None
    STATUS_PASS = 100
    STATUS_SKIP = 200
    STATUS_EXPECTED_FAIL = 300
    STATUS_UNEXPECTED_SUCCESS = 400
    STATUS_FAIL = 500
    STATUS_ERROR = 600

    FAILING_STATES = (STATUS_FAIL, STATUS_UNEXPECTED_SUCCESS, STATUS_ERROR)

    STATUS_LABELS = {
        STATUS_PASS: 'passed',
        STATUS_SKIP: 'skipped',
        STATUS_FAIL: 'failures',
        STATUS_EXPECTED_FAIL: 'expected failures',
        STATUS_UNEXPECTED_SUCCESS: 'unexpected successes',
        STATUS_ERROR: 'errors',
    }
    STATUS_ICONS = {
        STATUS_UNKNOWN: toga.Icon('icons/status/unknown.png'),
        STATUS_PASS: toga.Icon('icons/status/pass.png'),
        STATUS_SKIP: toga.Icon('icons/status/skip.png'),
        STATUS_EXPECTED_FAIL: toga.Icon('icons/status/expected_fail.png'),
        STATUS_UNEXPECTED_SUCCESS: toga.Icon('icons/status/unexpected_success.png'),
        STATUS_FAIL: toga.Icon('icons/status/fail.png'),
        STATUS_ERROR: toga.Icon('icons/status/error.png'),
    }


    def __init__(self, project, prefix, name):
        self._project = project
        self._prefix = prefix
        self._active = True

        self._name = name

        # Test status
        self._description = ''
        self._status = self.STATUS_UNKNOWN
        self._output = None
        self._error = None
        self._duration = None


    def __repr__(self):
        return u'TestMethod %s' % self.path

    ######################################################################
    # Methods required by the TreeSource interface
    ######################################################################

    def __len__(self):
        return 0

    def has_children(self):
        return False

    ######################################################################
    # Methods used by Cricket
    ######################################################################

    @property
    def path(self):
        "The dotted-path name that identifies this test method to the test runner"
        if self._prefix:
            return '{}.{}'.format(self._prefix, self.name)
        return self.name

    @property
    def label(self):
        "The display label for the node"
        return (self.STATUS_ICONS[self.status], self.name)

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def status(self):
        return self._status

    @property
    def output(self):
        return self._output

    @property
    def error(self):
        return self._error

    @property
    def duration(self):
        return self._duration

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

    def set_result(self, description, status, output, error, duration):
        self._description = description
        self._status = status
        self._output = output
        self._error = error
        self._duration = duration
        # self.emit()

    def set_active(self, is_active, cascade=True):
        """Explicitly set the active state of the test method

        If cascade is True, the parent testCase will be prompted
        to check it's current active status.
        """
        if self._active:
            if not is_active:
                self._active = False
                # self.emit('inactive')
                if cascade:
                    self.parent._update_active()
        else:
            if is_active:
                self._active = True
                # self.emit('active')
                if cascade:
                    self.parent._update_active()

    def toggle_active(self):
        "Toggle the current active status of this test method"
        self.set_active(not self.active)

    def find_tests(self, active=True, status=None):
        return 1, [self.path]


class TestCase(TestNode):
    """A data representation of a test case, wrapping multiple test methods.

    Emits:
        * 'new' when a new node is added
        * 'inactive' when the test method is made inactive in the suite.
        * 'active' when the test method is made active in the suite.
    """
    def __repr__(self):
        return u'TestCase %s' % self.path

    def set_active(self, is_active, cascade=True):
        """Explicitly set the active state of the test case.

        Forces all methods on this test case to set to the same
        active status.

        If cascade is True, the parent test module will be prompted
        to check it's current active status.
        """
        if self._active:
            if not is_active:
                self._active = False
                # self.emit('inactive')
                if cascade:
                    self.parent._update_active()
                for testMethod in self.values():
                    testMethod.set_active(False, cascade=False)
        else:
            if is_active:
                self._active = True
                # self.emit('active')
                if cascade:
                    self.parent._update_active()
                for testMethod in self.values():
                    testMethod.set_active(True, cascade=False)

    def toggle_active(self):
        "Toggle the current active status of this test case"
        self.set_active(not self.active)

    def _update_active(self):
        "Check the active status of all child nodes, and update the status of this node accordingly"
        for testMethod_name, testMethod in self.items():
            if testMethod.active:
                # As soon as we find an active child, this node
                # must be marked active, and no other checks are
                # required.
                self.set_active(True)
                return
        self.set_active(False)


class TestModule(TestNode):
    """A data representation of a module. It may contain test cases, or other modules.

    Emits:
        * 'new' when a new node is added
        * 'inactive' when the test method is made inactive in the suite.
        * 'active' when the test method is made active in the suite.
    """

    def __repr__(self):
        return u'TestModule %s' % self.path

    def set_active(self, is_active, cascade=True):
        """Explicitly set the active state of the test case.

        Forces all test cases and test modules held by this test module
        to be set to the same active status

        If cascade is True, the parent test module will be prompted
        to check it's current active status.
        """
        if self._active:
            if not is_active:
                self._active = False
                # self.emit('inactive')
                if cascade:
                    self.parent._update_active()
                for testModule in self.values():
                    testModule.set_active(False, cascade=False)
        else:
            if is_active:
                self._active = True
                # self.emit('active')
                if cascade:
                    self.parent._update_active()
                for testModule in self.values():
                    testModule.set_active(True, cascade=False)

    def toggle_active(self):
        "Toggle the current active status of this test case"
        self.set_active(not self.active)

    def _purge(self, timestamp):
        """Search all submodules and test cases looking for stale test methods.

        Purge any test module without any test cases, and any test Case with no
        test methods.
        """
        for testModule_name, testModule in self.items():
            testModule._purge(timestamp)
            if len(testModule) == 0:
                self.pop(testModule_name)

    # def _update_active(self):
    #     "Check the active status of all child nodes, and update the status of this node accordingly"
    #     for subModule_name, subModule in self.items():
    #         if subModule.active:
    #             self.set_active(True)
    #             return
    #     self.set_active(False)


class Project(TestNode, Source):
    """A data representation of an project, containing 1+ test apps.
    """
    def __init__(self):
        super().__init__(self, None, None)
        self.errors = []
        self.coverage = False

        self.refresh()

    def __repr__(self):
        return u'Project'

    @classmethod
    def add_arguments(cls, parser):
        """Add project specific commandline arguments to the *parser*
        object. *parser* is an instance of argparse.ArgumentParser.
        """
        pass

    def refresh(self):
        """Rediscover the tests in the test suite.
        """
        runner = subprocess.Popen(
            self.discover_commandline(),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

        test_list = []
        for line in runner.stdout:
            test_list.append(line.strip().decode('utf-8'))

        errors = []
        for line in runner.stderr:
            errors.append(line.strip().decode('utf-8'))
        if errors and not test_list:
            raise ModelLoadError('\n'.join(errors))

        timestamp = datetime.now()

        # Make sure there is a data representation for every test in the list.
        for test_label in test_list:
            self.confirm_exists(test_label)

        # for testModule_name, testModule in self.items():
        #     testModule._purge(timestamp)
        #     if len(testModule) == 0:
        #         self.pop(testModule_name)

        self.errors = errors if errors is not None else []

    # def _update_active(self):
    #     "Exists for API consistency"
    #     pass
