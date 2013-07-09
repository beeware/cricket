Cricket
=======

Cricket a graphical tool that helps you run your test suites.

Normal unittest test runners dump all output to the console, and provide very
little detail while the suite is running. As a result:

 * You can't start looking at failures until the test suite has completed running,

 * It isn't a very accessible format for identifying patterns in test failures,

 * It can be hard (or cumbersome) to re-run any tests that have failed.

Why the name ``cricket``? `Test Cricket`_ is the most prestigious version of
the game of cricket. Games last for up to 5 days... just like running some
test suites. The usual approach for making cricket watchable is a generous
dose of beer; in programming, `Balmer Peak`_ limits come into effect, so
something else is required...

.. _Test Cricket: http://en.wikipedia.org/wiki/Test_cricket
.. _Balmer Peak: http://xkcd.com/323/

Quickstart
----------

At present, Cricket has support for:

    * Pre-Django 1.6 project test suites,
    * Django 1.6+ project test suites using unittest2-style discovery, and
    * unittest project test suites.

In your Django project, install cricket, and then run it::

    $ pip install cricket
    $ python -m cricket.django

In a unittest project, install cricket, and then run it::

    $ pip install cricket
    $ python -m cricket.unittest

This will pop up a GUI window. Hit "Run all", and watch your test suite
execute. A progress bar is displayed in the bottom right hand corner of
the window, along with an estimate of time remaining.

While the suite is running, you can click on test names to see the output
of that test. If the test passed, it will be displayed in green; other test
results will be shown in other colors.

Problems under Ubuntu
~~~~~~~~~~~~~~~~~~~~~

Ubuntu's packaging of Python omits the ``idlelib`` library from it's base
packge. If you're using Python 2.7 on Ubuntu 13.04, you can install
``idlelib`` by running::

    $ sudo apt-get install idle-python2.7

For other versions of Python and Ubuntu, you'll need to adjust this as
appropriate.

Development
-----------

The recommended way of setting up your development envrionment for ``cricket``
is to install a virtual environment, install the required dependencies and
start coding. Assuming that you are using ``virtualenvwrapper``, you only have
to run::

    $ git clone git@github.com:freakboy3742/cricket.git
    $ cde cricket
    $ mkvirtualenv cricket

Cricket uses ``unittest`` (or ``unittest2`` for Python < 2.7) for its own test
suite as well as additional helper modules for testing. To install all the
requirements for cricket, you have to run the following commands within your
virutal envrionment::

    $ pip install -e .
    $ pip install -r requirements_dev.txt

In case you are running a python version ``< 2.7`` please use the
``requirements_dev_python2.7.txt`` instead because ``unittest2`` is not part
of the standard library for these version.

Now you are ready to start hacking! Have fun!
