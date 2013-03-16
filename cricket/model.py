"""A module containing a data representation for the test suite.

This is the "Model" of the MVC world.

Each object in the model is an event source; views/controllers
can bind to events on the model to be notified of changes.
"""
from datetime import datetime
import subprocess


class EventSource(object):
    """A source of GUI events.

    An event source can receive handlers for events, and
    can emit events.
    """
    _events = {}

    @classmethod
    def bind(cls, event, handler):
        cls._events.setdefault(cls, {}).setdefault(event, []).append(handler)

    def emit(self, event, **data):
        try:
            for handler in self._events[self.__class__][event]:
                handler(self, **data)
        except KeyError:
            # No handler registered for event.
            pass


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

    @active.setter
    def active(self, is_active):
        if self._active:
            if not is_active:
                self._active = False
                self.emit('inactive')
                self.parent._update_active()
        else:
            if is_active:
                self._active = True
                self.emit('active')
                self.parent._update_active()

    def toggle_active(self):
        "Toggle the current active status of this test method"
        if self._active:
            self._active = False
            self.emit('inactive')
            self.parent._update_active()
        else:
            self._active = True
            self.emit('active')
            self.parent._update_active()

    @property
    def status(self):
        try:
            return self._result['status']
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

    def set_result(self, status, error, duration):
        self._result = {
            'status': status,
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
        return u'%s.%s' % (self.parent.name, self.name)

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

    @active.setter
    def active(self, is_active):
        if self._active:
            if not is_active:
                self._active = False
                self.emit('inactive')
                self.parent._update_active()
        else:
            if is_active:
                self._active = True
                self.emit('active')
                self.parent._update_active()

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

            # If a list of tests has been provided, either
            # the full test method or the case or the app must be
            # mentioned explicitly.
            if labels and not (
                        testMethod.path in labels or
                        self.path in labels or
                        self.parent.name in labels
                    ):
                include = False

            if include:
                count = count + 1
                tests.append(testMethod.path)

        # If all the tests are included, then just reference the test case.
        if len(self) == count:
            return len(self), self.path

        return count, tests

    def _update_active(self):
        "Check the active status of all child nodes, and update the status of this node accordingly"
        for testMethod_name, testMethod in self.items():
            if testMethod.active:
                # As soon as we find an active child, this node
                # must be marked active, and no other checks are
                # required.
                self.active = True
                return
        self.active = False


class TestApp(dict, EventSource):
    """A data representation of an app, containing 1+ test cases.

    Emits:
        * 'new' when a new node is added
        * 'inactive' when the test method is made inactive in the suite.
        * 'active' when the test method is made active in the suite.
    """
    def __init__(self, name, project):
        super(TestApp, self).__init__()
        self.name = name
        self._active = True

        # Set the parent of the TestApp.
        self.parent = project
        self.parent[name] = self

        # Announce that there is a new test case
        self.emit('new')

    def __repr__(self):
        return u'TestApp %s' % self.path

    @property
    def path(self):
        "The dotted-path name that identifies this app to the test runner"
        return self.name

    @property
    def active(self):
        "Is this test method currently active?"
        return self._active

    @active.setter
    def active(self, is_active):
        if self._active:
            if not is_active:
                self._active = False
                self.emit('inactive')
        else:
            if is_active:
                self._active = True
                self.emit('active')

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
        for testCase_name, testCase in self.items():
            subcount, subtests = testCase.find_tests(active, status, labels)

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

    def _update_active(self):
        "Check the active status of all child nodes, and update the status of this node accordingly"
        for testCase_name, testCase in self.items():
            if testCase.active:
                self.active = True
                return
        self.active = False


class Project(dict, EventSource):
    """A data representation of an project, containing 1+ test apps.
    """
    def __init__(self):
        super(Project, self).__init__()

        self.discover_tests()

    def __repr__(self):
        return u'Project'

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
            subcount, sublabels = testApp.find_tests(active, status, labels)
            count = count + subcount

            if isinstance(sublabels, list):
                found_partial = True
                tests.extend(sublabels)
            else:
                tests.append(sublabels)

        # No partials found; just reference the app.
        if not found_partial:
            return count, []

        return count, tests

    def confirm_exists(self, test_label, timestamp=None):
        """Confirm that the given test label exists in the current data model.

        If it doesn't, create a representation for it.
        """
        testApp_name, testCase_name, testMethod_name = test_label.split('.')

        try:
            testApp = self[testApp_name]
        except KeyError:
            testApp = TestApp(testApp_name, self)

        try:
            testCase = testApp[testCase_name]
        except KeyError:
            testCase = TestCase(testCase_name, testApp)

        try:
            testMethod = testCase[testMethod_name]
        except KeyError:
            testMethod = TestMethod(testMethod_name, testCase)

        testMethod.timestamp = timestamp
        return testMethod

    def discover_tests(self):
        "Discover all available tests in a project."
        runner = subprocess.Popen(
            ['python', 'manage.py', 'test', '--testrunner=cricket.runners.TestDiscoverer'],
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=None,
            shell=False,
        )

        test_list = []
        for line in runner.stdout:
            test_list.append(line.strip())

        self.refresh(test_list)

    def refresh(self, test_list):
        """Refresh the project representation so that it contains only the tests in test_list

        test_list should be a list of dotted-path test names.
        """
        timestamp = datetime.now()

        # Make sure there is a data representation for every test in the list.
        for test_label in test_list:
            self.confirm_exists(test_label, timestamp)

        # Search for any stale tests in the data set.
        for testApp_name, testApp in self.items():
            for testCase_name, testCase in testApp.items():
                for testMethod_name, testMethod in testCase.items():
                    if testMethod.timestamp != timestamp:
                        testCase.pop(testMethod_name)
                if len(testCase) == 0:
                    testApp.pop(testCase_name)
            if len(testApp) == 0:
                self.pop(testApp_name)
