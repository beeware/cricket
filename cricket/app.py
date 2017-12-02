'''
The purpose of this module is to set up the Cricket GUI,
load a "project" for discovering and executing tests, and
to initiate the GUI main loop.
'''
from argparse import ArgumentParser
import subprocess
import sys

import toga
from cricket.view import (
    MainWindow,
    TestLoadErrorDialog,
    IgnorableTestLoadErrorDialog
)
from cricket.model import ModelLoadError


def main(Model):
    """Run the main loop of the app.

    Take the project Model as the argument. This model will be
    instantiated as part of the main loop.
    """
    parser = ArgumentParser()

    parser.add_argument("--version", help="Display version number and exit", action="store_true")

    Model.add_arguments(parser)
    options = parser.parse_args()

    # Check the shortcut options
    if options.version:
        import cricket
        print(cricket.__version__)
        return

    # Construct a Toga application
    view = MainWindow('Cricket', 'org.pybee.cricket')

    # Try to load the project. If any error occurs during
    # project load, show an error dialog
    project = None
    while project is None:
        try:
            # Create the project objects
            project = Model(options)

            runner = subprocess.Popen(
                project.discover_commandline(),
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

            project.refresh(test_list, errors)
        except ModelLoadError as e:
            # Load failed; destroy the project and show an error dialog.
            #   If the user selects cancel, quit.
            view.test_load_error = e.trace
        else:
            view.test_load_error = None

    if project.errors:
        view.ignorable_test_load_error = '\n'.join(project.errors)
    else:
        view.ignorable_test_load_error = None

    # Set the project for the main window.
    # This populates the tree, and sets listeners for
    # future tree modifications.
    view.project = project

    # Run the main loop
    view.main_loop()
