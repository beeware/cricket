'''
The purpose of this module is to set up the Cricket GUI,
load a "project" for discovering and executing tests, and
to initiate the GUI main loop.
'''
from Tkinter import *

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
    # Set up the root Tk context
    root = Tk()

    # Construct an empty window
    view = MainWindow(root)

    # Try to load the project. If any error occurs during
    # project load, show an error dialog
    project = None
    while project is None:
        try:
            project = Model()
        except ModelLoadError as e:
            dialog = TestLoadErrorDialog(root, e.trace)
            if dialog.status == dialog.CANCEL:
                sys.exit(1)

    if project.errors:
        dialog = IgnorableTestLoadErrorDialog(root, '\n'.join(project.errors))
        if dialog.status == dialog.CANCEL:
            sys.exit(1)

    # Set the project for the main window.
    # This populates the tree, and sets listeners for
    # future tree modifications.
    view.project = project

    # Run the main loop
    try:
        view.mainloop()
    except KeyboardInterrupt:
        view.on_quit()
