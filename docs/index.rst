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
    $ cricket-django

In a unittest project, install cricket, and then run it::

    $ pip install cricket
    $ cricket-unittest

This will pop up a GUI window. Hit "Run all", and watch your test suite
execute.

Problems under Ubuntu
~~~~~~~~~~~~~~~~~~~~~

Ubuntu's packaging of Python omits the ``idlelib`` library from it's base
packge. If you're using Python 2.7 on Ubuntu 13.04, you can install
``idlelib`` by running::

    $ sudo apt-get install idle-python2.7

For other versions of Python and Ubuntu, you'll need to adjust this as
appropriate.

Contents:

.. toctree::
   :maxdepth: 2
   :glob:

   internals/contributing
   internals/backends
   internals/roadmap
   releases

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
