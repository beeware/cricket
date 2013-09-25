"""A module containing a data representation for the test suite.

This is the "Model" of the MVC world.

Each object in the model is an event source; views/controllers
can bind to events on the model to be notified of changes.
"""
from datetime import datetime

from cricket.events import EventSource


class ModelLoadError(Exception):
    def __init__(self, trace):
        super(ModelLoadError, self).__init__()
        self.trace = trace


class TestMethod(EventSource):
    """A data representation of an individual test method.

    Emits:
        * 'new' when a new node is added
        * 'inactive' when the test method is made inactive in the suite.
        * 'active' when the test method is made active in the suite.
        * 'status_update' when the pass/fail status of the method is updated.
    """
    STATUS_PASS = 100
    STATUS_SKIP = 200
    STATUS_FAIL = 300
    STATUS_EXPECTED_FAIL = 310
    STATUS_UNEXPECTED_SUCCESS = 320
    STATUS_ERROR = 400

    FAILING_STATES = (STATUS_FAIL, STATUS_UNEXPECTED_SUCCESS, STATUS_ERROR)

    STATUS_LABELS = {
        STATUS_PASS: 'passed',
        STATUS_SKIP: 'skipped',
        STATUS_FAIL: 'failures',
        STATUS_EXPECTED_FAIL: 'expected failures',
        STATUS_UNEXPECTED_SUCCESS: 'unexpected successes',
        STATUS_ERROR: 'errors',
    }

    def __init__(self, name, testCase):
        self.name = name
        self.description = ''
        self._active = True
        self._result = None

        # Set the parent of the TestMethod
        self.parent = testCase
        self.parent[name] = self
        self.parent._update_active()

        # Announce that there is a new test method
        self.emit('new')

    def __repr__(self):
        return u'TestMethod %s' % self.path

    @property
    def path(self):
        "The dotted-path name that identifies this test method to the test runner"
        return u'%s.%s' % (self.parent.path, self.name)

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

    def set_active(self, is_active, cascade=True):
        """Explicitly set the active state of the test method

        If cascade is True, the parent testCase will be prompted
        to check it's current active status.
        """
        if self._active:
            if not is_active:
                self._active = False
                self.emit('inactive')
                if cascade:
                    self.parent._update_active()
        else:
            if is_active:
                self._active = True
                self.emit('active')
                if cascade:
                    self.parent._update_active()

    def toggle_active(self):
        "Toggle the current active status of this test method"
        self.set_active(not self.active)

    @property
    def status(self):
        try:
            return self._result['status']
        except TypeError:
            return None

    @property
    def output(self):
        try:
            return self._result['output']
        except TypeError:
            return None

    @property
    def error(self):
        try:
            return self._result['error']
        except TypeError:
            return None

    @property
    def duration(self):
        try:
            return self._result['duration']
        except TypeError:
            return None

    def set_result(self, status, output, error, duration):
        self._result = {
            'status': status,
            'output': output,
            'error': error,
            'duration': duration,
        }
        self.emit('status_update')


class TestCase(dict, EventSource):
    """A data representation of a test case, wrapping multiple test methods.

    Emits:
        * 'new' when a new node is added
        * 'inactive' when the test method is made inactive in the suite.
        * 'active' when the test method is made active in the suite.
    """
    def __init__(self, name, testApp):
        super(TestCase, self).__init__()
        self.name = name
        self._active = True

        # Set the parent of the TestCase
        self.parent = testApp
        self.parent[name] = self
        self.parent._update_active()

        # Announce that there is a new TestCase
        self.emit('new')

    def __repr__(self):
        return u'TestCase %s' % self.path

    @property
    def path(self):
        "The dotted-path name that identifies this Test Case to the test runner"
        return u'%s.%s' % (self.parent.path, self.name)

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

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
                self.emit('inactive')
                if cascade:
                    self.parent._update_active()
                for testMethod in self.values():
                    testMethod.set_active(False, cascade=False)
        else:
            if is_active:
                self._active = True
                self.emit('active')
                if cascade:
                    self.parent._update_active()
                for testMethod in self.values():
                    testMethod.set_active(True, cascade=False)

    def toggle_active(self):
        "Toggle the current active status of this test case"
        self.set_active(not self.active)

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

        for testMethod_name, testMethod in self.items():
            include = True
            # If only active tests have been requested, the method
            # must be active.
            if active and not testMethod.active:
                include = False

            # If a list of statuses has been provided, the
            # method status must be in that list.
            if status and testMethod.status not in status:
                include = False

            # If a list of test labels has been provided, the method
            # must be named explicitly
            if labels and testMethod.path not in labels:
                include = False

            if include:
                count = count + 1
                tests.append(testMethod.path)

        # If all the tests are included, then just reference the test case.
        if len(self) == count:
            return len(self), self.path

        return count, tests

    def _purge(self, timestamp):
        "Purge any test method that isn't current as of the timestamp"
        for testMethod_name, testMethod in self.items():
            if testMethod.timestamp != timestamp:
                self.pop(testMethod_name)

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


class TestModule(dict, EventSource):
    """A data representation of a module. It may contain test cases, or other modules.

    Emits:
        * 'new' when a new node is added
        * 'inactive' when the test method is made inactive in the suite.
        * 'active' when the test method is made active in the suite.
    """
    def __init__(self, name, parent):
        super(TestModule, self).__init__()
        self.name = name
        self._active = True

        # Set the parent of the TestModule.
        self.parent = parent
        self.parent[name] = self

        # Announce that there is a new test case
        self.emit('new')

    def __repr__(self):
        return u'TestModule %s' % self.path

    @property
    def path(self):
        "The dotted-path name that identifies this app to the test runner"
        if self.parent.path:
            return u'%s.%s' % (self.parent.path, self.name)
        return self.name

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

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
                self.emit('inactive')
                if cascade:
                    self.parent._update_active()
                for testModule in self.values():
                    testModule.set_active(False, cascade=False)
        else:
            if is_active:
                self._active = True
                self.emit('active')
                if cascade:
                    self.parent._update_active()
                for testModule in self.values():
                    testModule.set_active(True, cascade=False)

    def toggle_active(self):
        "Toggle the current active status of this test case"
        self.set_active(not self.active)

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
        for testModule_name, testModule in self.items():
            include = True

            # If only active tests have been requested, the module
            # must be active.
            if active and not testModule.active:
                include = False

            # If a list of test labels has been provided, either the
            # module, or a test *in* the module, must be named explicitly.
            if labels:
                if testModule.path in labels:
                    # The module is named explicitly. Include all active
                    # subtests of this module
                    subcount, subtests = testModule.find_tests(True, status)
                else:
                    # The module isn't named. Look for all subtests.
                    # Search for subtests that match.
                    subcount, subtests = testModule.find_tests(active, status, labels)
            else:
                subcount, subtests = testModule.find_tests(active, status)

            if include:
                count = count + subcount

                if isinstance(subtests, list):
                    found_partial = True
                    tests.extend(subtests)
                else:
                    tests.append(subtests)

        # No partials found; just reference the app.
        if not found_partial:
            return count, self.path

        return count, tests

    def _purge(self, timestamp):
        """Search all submodules and test cases looking for stale test methods.

        Purge any test module without any test cases, and any test Case with no
        test methods.
        """
        for testModule_name, testModule in self.items():
            testModule._purge(timestamp)
            if len(testModule) == 0:
                self.pop(testModule_name)

    def _update_active(self):
        "Check the active status of all child nodes, and update the status of this node accordingly"
        for subModule_name, subModule in self.items():
            if subModule.active:
                self.set_active(True)
                return
        self.set_active(False)


class Project(dict, EventSource):
    """A data representation of an project, containing 1+ test apps.
    """
    def __init__(self):
        super(Project, self).__init__()
        self.errors = []
        self.coverage = False

    def __repr__(self):
        return u'Project'

    @classmethod
    def add_arguments(cls, parser):
        """Add project specific commandline arguments to the *parser*
        object. *parser* is an instance of argparse.ArgumentParser.
        """
        pass

    @property
    def path(self):
        "The dotted-path name that identifies this project to the test runner"
        return ''

    def find_tests(self, active=True, status=None, labels=None):
        """Find the test labels matching the search criteria.

        Returns a count of tests found, plus the labels needed to
        execute those tests.
        """
        tests = []
        count = 0

        found_partial = False
        for testApp_name, testApp in self.items():
            include = True

            # If only active tests have been requested, the module
            # must be active.
            if active and not testApp.active:
                include = False

            # If a list of test labels has been provided, either the
            # module, or a test *in* the module, must be named explicitly.
            if labels:
                if testApp.path in labels:
                    # The module is named explicitly. Include all active
                    # subtests of this module
                    subcount, subtests = testApp.find_tests(True, status)
                else:
                    # The module isn't named. Look for all subtests.
                    # Search for subtests that match.
                    subcount, subtests = testApp.find_tests(active, status, labels)
            else:
                subcount, subtests = testApp.find_tests(active, status)

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

    def confirm_exists(self, test_label, timestamp=None):
        """Confirm that the given test label exists in the current data model.

        If it doesn't, create a representation for it.
        """
        parts = test_label.split('.')
        if len(parts) < 2:
            return

        parentModule = self
        for testModule_name in parts[:-2]:
            try:
                testModule = parentModule[testModule_name]
            except KeyError:
                testModule = TestModule(testModule_name, parentModule)
            parentModule = testModule

        try:
            testCase = parentModule[parts[-2]]
        except KeyError:
            testCase = TestCase(parts[-2], parentModule)

        try:
            testMethod = testCase[parts[-1]]
        except KeyError:
            testMethod = TestMethod(parts[-1], testCase)

        testMethod.timestamp = timestamp
        return testMethod

    def refresh(self, test_list, errors=None):
        """Refresh the project representation so that it contains only the tests in test_list

        test_list should be a list of dotted-path test names.
        """
        timestamp = datetime.now()

        # Make sure there is a data representation for every test in the list.
        for test_label in test_list:
            self.confirm_exists(test_label, timestamp)

        for testModule_name, testModule in self.items():
            testModule._purge(timestamp)
            if len(testModule) == 0:
                self.pop(testModule_name)

        self.errors = errors if errors is not None else []

    def _update_active(self):
        "Exists for API consistency"
        pass
