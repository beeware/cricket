'''
The purpose of this module is to set up the Cricket GUI,
load a Test Suite for discovering and executing tests, and
to initiate the GUI main loop.
'''
from argparse import ArgumentParser

import toga
from cricket.view import Cricket
from cricket.model import ModelLoadError


def main(Model):
    """Run the main loop of the app.

    Take the test_suite Model as the argument. This model will be
    instantiated as part of the main loop.
    """
    parser = ArgumentParser()

    parser.add_argument("--version", help="Display version number and exit", action="store_true")

    options = parser.parse_args()

    # Check the shortcut options
    if options.version:
        import cricket
        print(cricket.__version__)
        return

    # Construct a Toga application
    app = Cricket('Cricket', 'org.pybee.cricket', icon=toga.Icon('icons/cricket'))

    # Try to load the test_suite. If any error occurs during
    # test suite load, show an error dialog
    test_suite = None
    while test_suite is None:
        try:
            # Create the test_suite objects
            test_suite = Model(options)
            test_suite.refresh()
        except ModelLoadError as e:
            # Load failed; destroy the test_suite and show an error dialog.
            #   If the user selects cancel, quit.
            app.test_load_error = e.trace
        else:
            app.test_load_error = None

    if test_suite.errors:
        app.ignorable_test_load_error = '\n'.join(test_suite.errors)
    else:
        app.ignorable_test_load_error = None

    # Set the test_suite for the main window.
    # This populates the tree, and sets listeners for
    # future tree modifications.
    app.test_suite = test_suite

    return app
