'''
The purpose of this module is to set up the Cricket GUI,
load a "project" for discovering and executing tests, and
to initiate the GUI main loop.
'''
from argparse import ArgumentParser

import toga
from cricket.view import Cricket
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
    app = Cricket('Cricket', 'org.pybee.cricket')

    # Try to load the project. If any error occurs during
    # project load, show an error dialog
    project = None
    while project is None:
        try:
            # Create the project objects
            project = Model(options)
        except ModelLoadError as e:
            # Load failed; destroy the project and show an error dialog.
            #   If the user selects cancel, quit.
            app.test_load_error = e.trace
        else:
            app.test_load_error = None

    if project.errors:
        app.ignorable_test_load_error = '\n'.join(project.errors)
    else:
        app.ignorable_test_load_error = None

    # Set the project for the main window.
    # This populates the tree, and sets listeners for
    # future tree modifications.
    app.project = project

    return app
