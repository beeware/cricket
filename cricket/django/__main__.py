from Tkinter import *

from cricket.view import MainWindow, TestLoadErrorDialog
from cricket.model import ModelLoadError
from cricket.django.model import DjangoProject


def main():
    # Set up the root Tk context
    root = Tk()

    # Construct an empty window
    view = MainWindow(root)

    # Try to load the project. If any error occurs during
    # project load, show an error dialog
    project = None
    while project is None:
        try:
            project = DjangoProject()
        except ModelLoadError, e:
            TestLoadErrorDialog(root, e.trace)

    # Set the project for the main window.
    # This populates the tree, and sets listeners for
    # future tree modifications.
    view.project = project

    # Run the main loop
    try:
        view.mainloop()
    except KeyboardInterrupt:
        view.on_quit()

if __name__ == "__main__":
    main()
