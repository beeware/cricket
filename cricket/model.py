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
    def __init__(self, source, path, name):
        super().__init__()
        self._child_labels = []
        self._child_nodes = {}

        self._source = source

        self._path = path
        self._name = name
        self._active = True

    ######################################################################
    # Methods required by the TreeSource interface
    ######################################################################

    def __len__(self):
        return len(self._child_labels)

    def __getitem__(self, index_or_name):
        if isinstance(index_or_name, (int, slice)):
            return self._child_nodes[self._child_labels[index_or_name]]
        else:
            return self._child_nodes[index_or_name]

    def can_have_children(self):
        return True

    ######################################################################
    # Methods used by Cricket
    ######################################################################

    def __setitem__(self, label, child):
        # Insert the item, sort the list,
        # and find out where the item was inserted.
        self._child_labels.append(label)
        self._child_labels.sort()
        index = self._child_labels.index(label)

        self._child_nodes[label] = child

        self._source._notify('insert', parent=self, index=index, item=child)

    def __delitem__(self, label):
        # Find the label in the list of children, and remove it.
        index = self._child_labels.index(label)
        self._child_nodes[label] = child

        self._source._notify('remove', item=child)
        del self._child_labels[index]
        del self._child_nodes[label]

    @property
    def path(self):
        "The dotted-path name that identifies this node to the test runner"
        return self._path

    @property
    def name(self):
        "The identifying name for this node"
        return self._name

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

    def find_tests(self, active=True, status=None, labels=None):
        """Find the test labels matching the search criteria.

        This will check:
            * active: if the method is currently an active test
            * status: if the last run status of the method is in the provided list
            * labels: if the method label is in the provided list

        Returns a count of tests found, plus the labels needed to
        execute those tests.
        """
        tests = []
        count = 0
        found_partial = False
        for child_label, child_node in self._child_nodes.items():
            # If only active tests have been requested,
            # the child node must be active.
            # If only "status == X" tests have been requested,
            # the child node must have that status.
            if active and not child_node.active:
                # There's at least one child marked inactive;
                # this node is therefore a partial selection
                subcount = 0
                subtests = []
                found_partial = True
            elif status and child_node.status not in status:
                # There's at least one child marked inactive;
                # this node is therefore a partial selection
                subcount = 0
                subtests = []
                found_partial = True
            else:
                if labels:
                    # A specific set of tests has been requested.
                    if child_node.path in labels:
                        # This child node exactly matches a requested label.
                        # Find *all* subtests of this node.
                        subcount, subtests = child_node.find_tests(active, status)

                        # If subtests have been found, but the list of subtests
                        # is None, then this node's path can be provided as a
                        # specifier for "all subtests of this node"
                        if subtests is None:
                            subtests = [child_node.path]
                        else:
                            # At least one descendent of this child is excluded
                            # that means this node is a partial match.
                            found_partial = True
                    else:
                        # Search children of this child for the provided labels.
                        subcount, subtests = child_node.find_tests(active, status, labels)

                        # If subtests have been found, but the list of subtests
                        # is None, then this node's path can be provided as a
                        # specifier for "all subtests of this node"
                        if subtests is None:
                            subtests = [child_node.path]
                        else:
                            # At least one descendent of this child is excluded
                            # that means this node is a partial match.
                            found_partial = True

                else:
                    # All tests have been requested.
                    subcount, subtests = child_node.find_tests(active, status)

                    # If subtests have been found, but the list of subtests
                    # is empty, then this node's path can be provided as a
                    # specifier for "all subtests of this node"
                    if subtests is None:
                        subtests = [child_node.path]
                    else:
                        # At least one descendent of this child is excluded
                        # that means this node is a partial match.
                        found_partial = True

            count = count + subcount
            tests.extend(subtests)


        # No children were a partial match; therefore, this entire
        # node is being executed. Return the count of subtests found,
        # with a test list of None to flag the complete status.
        if not found_partial:
            return count, None

        # Return the count of tests, and the labels needed to target them.
        return count, tests


class TestMethod:
    """A data representation of an individual test method.
    """
    STATUS_UNKNOWN = None
    STATUS_PASS = 100
    STATUS_SKIP = 200
    STATUS_EXPECTED_FAIL = 300
    STATUS_UNEXPECTED_SUCCESS = 400
    STATUS_FAIL = 500
    STATUS_ERROR = 600

    FAILING_STATES = (STATUS_FAIL, STATUS_UNEXPECTED_SUCCESS, STATUS_ERROR)

    STATUS_ICONS = {
        STATUS_UNKNOWN: toga.Icon('icons/status/unknown.png'),
        STATUS_PASS: toga.Icon('icons/status/pass.png'),
        STATUS_SKIP: toga.Icon('icons/status/skip.png'),
        STATUS_EXPECTED_FAIL: toga.Icon('icons/status/expected_fail.png'),
        STATUS_UNEXPECTED_SUCCESS: toga.Icon('icons/status/unexpected_success.png'),
        STATUS_FAIL: toga.Icon('icons/status/fail.png'),
        STATUS_ERROR: toga.Icon('icons/status/error.png'),
    }

    def __init__(self, source, path, name):
        self._source = source

        self._path = path
        self._name = name
        self._active = True

        # Test status
        self._description = ''
        self._status = self.STATUS_UNKNOWN
        self._output = None
        self._error = None
        self._duration = None

    def __repr__(self):
        return '<TestMethod %s>' % self.path

    ######################################################################
    # Methods required by the TreeSource interface
    ######################################################################

    def can_have_children(self):
        return False

    ######################################################################
    # Methods used by Cricket
    ######################################################################

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    @property
    def label(self):
        "The display label for the node"
        return (self.STATUS_ICONS[self.status], self.name)

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

        self._source._notify('change', item=self)

    def set_active(self, is_active, cascade=True):
        """Explicitly set the active state of the test method

        If cascade is True, the parent testCase will be prompted
        to check it's current active status.
        """
        if self._active:
            if not is_active:
                self._active = False
                if cascade:
                    self.parent._update_active()
        else:
            if is_active:
                self._active = True
                if cascade:
                    self.parent._update_active()

    def toggle_active(self):
        "Toggle the current active status of this test method"
        self.set_active(not self.active)

    def find_tests(self, active=True, status=None, labels=None):
        if labels:
            if self.path in labels:
                return 1, None
            else:
                return 0, []
        else:
            return 1, None


class TestCase(TestNode):
    """A data representation of a test case, wrapping multiple test methods.
    """
    TEST_CASE_ICON = toga.Icon('icons/test_case.png')

    def __repr__(self):
        return '<TestCase %s>' % self.path

    @property
    def label(self):
        "The display label for the node"
        return (self.TEST_CASE_ICON, self.name)

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
    """
    TEST_MODULE_ICON = toga.Icon('icons/test_module.png')

    def __repr__(self):
        return '<TestModule %s>' % self.path

    @property
    def label(self):
        "The display label for the node"
        return (self.TEST_MODULE_ICON, self.name)

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


class TestSuite(TestNode, Source):
    """A data representation of a test suite, containing 1+ test cases.
    """
    def __init__(self):
        super().__init__(self, None, None)
        self.errors = []
        self.coverage = False

    def __repr__(self):
        return '<TestSuite>'

    def refresh(self, test_list=None, errors=None):
        """Rediscover the tests in the test suite.
        """
        if test_list is None:
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
        for test_id in test_list:
            self.put_test(test_id)

        self.errors = errors if errors is not None else []

    def put_test(self, test_id):
        """An idempotent insert method for tests.

        Ensures that a test identified as `test_id` exists in the test tree.
        """
        parent = self

        for NodeClass, part in self.split_test_id(test_id):
            try:
                child = parent[part]
            except KeyError:
                child = NodeClass(
                    source=self,
                    path=self.join_path(parent, NodeClass, part),
                    name=part
                )
                parent[part] = child
            parent = child

        return child

    def del_test(self, test_id):
        parent = self
        parents = []
        for NodeClass, part in self.split_test_id(test_id):
            try:
                child = parent[part]
                parents.append(parent)
                parent = child
            except KeyError:
                # We've found a part of the path does doesn't
                # exist in the tree - that means we can bail.
                return

        # If we complete iterating, we've found a test with this id.
        # So, we can delete the child...
        del parents[-1][child.name]

        # ... then we can walk back up the list of parents,
        # deleting any parent that has no children.
        # If at any point we find a parent with children,
        # we can bail (as the parent of a node with children
        # must also have children)
        while parents:
            child = parents.pop()
            if len(child) == 0:
                del parents[-1][child.name]
            else:
                return


class TestSuiteProblems(TestSuite):
    def __init__(self, suite):
        super().__init__()
        self.suite = suite
        # Listen to any changes on the test suite
        self.suite.add_listener(self)

    def __repr__(self):
        return '<TestSuiteProblems>'

    def change(self, item):
        if item.status in TestMethod.FAILING_STATES:
            # Test didn't pass. Make sure it exists in the problem tree.
            failing_item = self.put_test(item.path)

            failing_item.set_result(
                description=item.description,
                status=item.status,
                output=item.output,
                error=item.error,
                duration=item.duration
            )
        else:
            self.del_test(item.path)

    def split_test_id(self, test_id):
        return self.suite.split_test_id(test_id)

    def join_path(self, parent, klass, part):
        return self.suite.join_path(parent, klass, part)
