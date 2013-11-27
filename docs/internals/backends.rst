Writing a Cricket backend
=========================

Why you might want to do this
-----------------------------

A number of test execution environments are not necessarily supported. This
includes pytest, GUI test tools, or even custom stuff. The sky is the limit.
Or, you might just want to understand the architecture.

Helicopter Overview of the Architecture
---------------------------------------

The main directory consists of events, executor, model, pipes, view and
widgets. The ones which are the concern of the GUI are events, view and
widgets. The ones which concern the backend are model, executor and pipes.
The one which you need to really understand is pipes, but that's not the best
starting point.

The best starting point is either the unittest or django subdirectory. The GUI
is first built by the relevant backend, and the backend provides standard
callbacks for the GUI.

Layout of a Backend System
--------------------------

A Cricket backend should contain the following 4 files:

   * ``__main__.py`` - The entry point for the user.

   * ``discoverer.py`` - Generates the list of available tests

   * ``executor.py`` - Wraps execution of test functions

   * ``model.py`` - Defines the method for executing the discoverer and executor

Requirements of a backend
-------------------------

Both the Django and the unittest backend take advantage of the unittest module
to create and execute test suites. The core file pipes.PipedTestRunner will
run unittest-style tests and provide the appropriately well-formed output
expected by the GUI. However, it is a valid choice for the executor to produce
output of the same for onto stdout itself. The only hard requirement is that
the executor function stream onto stdout a series of well-formed outputs. To
understand the full detail, examine pipes.py.

The Django and the unittest mechanisms for executing tests are different. The
Django backend is a thin hook into the Django test execution machinery. The
unittest backend is a slightly less thin hook into the unittest modele. The
key requirements of the executor backend are:

  1. The ability to stream well-formed output to stdout
  2. The ability to limit/target test execution according to supplied labels

At the time of writing, sys.argv[1:] will be the list of dotted-namespaced
names of tests which should be run. More complex command-line calls are simply
not supported at this stage. A very useful task would be to do some more
thinking on this interface.
