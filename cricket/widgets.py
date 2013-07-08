try:
    from idlelib.WidgetRedirector import WidgetRedirector
except ImportError:
    import platform
    import sys
    if platform.linux_distribution()[0] == 'Ubuntu':
        raise Exception("idlelib could not be found. " +
                        "You may need to install IDLE - try running " +
                        "'sudo apt-get install idle-python%s.%s'" % (
                            sys.version_info[0:2]
                        ))
    else:
        raise Exception("idlelib could not be found. " +
                        "Check your operating system instructions " +
                        "to work out how to install IDLE and idlelib.")

from Tkinter import *
from ttk import *


def tk_break(*args, **kwargs):
    "Return a Tk 'break' event result."
    return "break"


class ReadOnlyText(Text):
    """A Text widget that redirects the insert and delete
    handlers so that they are no-ops. This effectively makes
    the widget readonly with respect to keyboard input handlers.

    Adapted from http://tkinter.unpythonic.net/wiki/ReadOnlyText, which
    is itself adapting a solution described here: http://wiki.tcl.tk/1152
    """
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)

        self.redirector = WidgetRedirector(self)
        self.insert = self.redirector.register("insert", tk_break)
        self.delete = self.redirector.register("delete", tk_break)
