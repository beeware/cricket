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


class TestLabelList(list):
    """Utility datatype.

    Tracks a list of objects. A boolean on the list describes
    if any element in the list is inactive. If this list is extended,
    the inactive status of the other list is combined with this
    one to determine if the new list contains an inactive element.
    """

    def __init__(self, *args):
        super(TestLabelList, self).__init__(*args)
        self.found_inactive = False

    def extend(self, other):
        super(TestLabelList, self).extend(other)
        self.found_inactive = self.found_inactive or other.found_inactive


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
    def set_active(self, is_active):
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

    @property
    def test_labels(self):
        """The list of all active test labels in this Test Case.

        The values from this property can be passed to the test runner
        to identify the tests that need to be executed.

        If all tests in the test case are active, the label of the
        app is returned.
        """
        labels = TestLabelList()
        for testMethod_name, testMethod in self.items():
            if testMethod.active:
                labels.append(testMethod.path)
            else:
                labels.found_inactive = True

        if labels.found_inactive:
            return labels
        return TestLabelList([self.path])

    @property
    def active_test_count(self):
        "Return the number of tests currently active for the test case"
        count = 0
        if self.active:
            for testMethod_name, testMethod in self.items():
                if testMethod.active:
                    count = count + 1
        return count

    def _update_active(self):
        for testMethod_name, testMethod in self.items():
            if testMethod.active:
                if not self.active:
                    self._active = True
                    self.emit('active')
                    self.parent._update_active()
                return
        if self.active:
            self._active = False
            self.emit('inactive')
            self.parent._update_active()


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

    @property
    def test_labels(self):
        """The list of all active test labels in this app.

        The values from this property can be passed to the test runner
        to identify the tests that need to be executed.
        """
        labels = TestLabelList()
        for testCase_name, testCase in self.items():
            if testCase.active:
                labels.extend(testCase.test_labels)
            else:
                labels.found_inactive = True

        if labels.found_inactive:
            return labels
        return TestLabelList([self.path])

    @property
    def active_test_count(self):
        "Return the number of tests currently active for the app"
        count = 0
        if self.active:
            for testCase_name, testCase in self.items():
                count = count + testCase.active_test_count
        return count

    def _update_active(self):
        for testCase_name, testCase in self.items():
            if testCase.active:
                if not self.active:
                    self._active = True
                    self.emit('active')
                return
        if self.active:
            self._active = False
            self.emit('inactive')


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

    @property
    def test_labels(self):
        """The list of all active test labels in this app.

        The values from this property can be passed to the test runner
        to identify the tests that need to be executed.
        """
        labels = TestLabelList()
        for testApp_name, testApp in self.items():
            if testApp.active:
                labels.extend(testApp.test_labels)
            else:
                labels.found_inactive = True

        if labels.found_inactive:
            return labels
        return []

    @property
    def active_test_count(self):
        "Return the number of tests currently active for the project"
        count = 0
        for testApp_name, testApp in self.items():
            count = count + testApp.active_test_count

        return count

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
