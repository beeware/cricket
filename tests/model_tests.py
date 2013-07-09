import mock

from cricket.compat import unittest
from cricket.model import Project, ModelLoadError


class TestProject(unittest.TestCase):

    def setUp(self):
        super(TestProject, self).setUp()
        Project.discover_commandline = mock.MagicMock()

        self.test_list = [
            'tests.FunkyTestCase.test_something_unnecessary',
            'more_tests.FunkyTestCase.test_this_doesnt_make_sense',
        ]
        self.error_list = [
            'ERROR: you broke it, fool!',
        ]

    @mock.patch('cricket.model.subprocess.Popen')
    def test_project_has_error_list_from_stderr(self, sub_mock):
        io_mock = mock.MagicMock()
        io_mock.stdout = self.test_list
        io_mock.stderr = self.error_list
        sub_mock.return_value = io_mock

        project = Project()

        self.assertEquals(project.errors, self.error_list)
        self.assertItemsEqual(project.keys(), ['tests', 'more_tests'])

    @mock.patch('cricket.model.subprocess.Popen')
    def test_raises_exception_when_errors_no_tests(self, sub_mock):
        io_mock = mock.MagicMock()
        io_mock.stdout = []
        io_mock.stderr = self.error_list
        sub_mock.return_value = io_mock

        self.assertRaises(ModelLoadError, Project)

    @mock.patch('cricket.model.subprocess.Popen')
    def test_finds_test_modules_without_errors(self, sub_mock):
        io_mock = mock.MagicMock()
        io_mock.stdout = self.test_list
        io_mock.stderr = []
        sub_mock.return_value = io_mock

        project = Project()
        self.assertEquals(project.errors, [])
        self.assertItemsEqual(project.keys(), ['tests', 'more_tests'])
