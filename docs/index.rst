Cricket
=======

Cricket is part of the `BeeWare suite`_. The project website is `http://pybee.org/cricket`_.

Cricket is a graphical tool that helps projects with large test suites **identify failures without waiting** for all your tests to finish.

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

.. _BeeWare suite: http://pybee.org/
.. _http://pybee.org/cricket: http://pybee.org/cricket
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

``cricket-django`` will also work in Django's own tests directory -- i.e., you
can use ``cricket-django`` to run Django's own test suite (for Django 1.6 or
later).

In a unittest project, install cricket, and then run it::

    $ pip install cricket
    $ cricket-unittest

This will pop up a GUI window. Hit "Run all", and watch your test suite
execute.

Problems under Ubuntu
~~~~~~~~~~~~~~~~~~~~~

Ubuntu's packaging of Python omits the ``idlelib`` library from it's base
package. If you're using Python 2.7 on Ubuntu 13.04, you can install
``idlelib`` by running::

    $ sudo apt-get install idle-python2.7

For other versions of Python and Ubuntu, you'll need to adjust this as
appropriate.

Problems under Windows
~~~~~~~~~~~~~~~~~~~~~~

If you're running Cricket in a virtualenv, you'll need to set an
environment variable so that Cricket can find the TCL graphics library::

    $ set TCL_LIBRARY=c:\Python27\tcl\tcl8.5

You'll need to adjust the exact path to reflect your local Python install.
You may find it helpful to put this line in the ``activate.bat`` script
for your virtual environment so that it is automatically set whenever the
virtualenv is activated.

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
