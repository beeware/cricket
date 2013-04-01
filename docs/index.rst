.. Django-Cricket documentation master file, created by
   sphinx-quickstart on Sat Feb  9 10:44:39 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Cricket
=======

Cricket a graphical tool that helps you run your test suites.

Normal unittest test runners dumps all output to the console, and provide very
little detail while the suite is running. As a result:

 * You can't start looking at failures until the test suite has completed running,

 * It isn't a very accessible format for identifying patterns in test failures,

 * It can be hard (or cumbersome) to re-run any tests that have failed.

If you're running a test suite with an expensive suite setup/teardown method,
there may also be performance optimizations that can be made. For example, if
you're running a Django test suite, and the test database isn't changing
between runs,  you only need to create the database once, then re-use it.
Depending on your database setup, this can save a lot of running time.

Why the name ``cricket``? `Test Cricket`_ is the most prestigious version of
the game of cricket. Games last for up to 5 days... just like running some
test suites. The usual approach for making cricket watchable is a generous
dose of beer; in programming, `Balmer Peak`_ limits come into effect, so
something else is required... :-)

.. _Test Cricket: http://en.wikipedia.org/wiki/Test_cricket
.. _Balmer Peak: http://xkcd.com/323/

Quickstart
----------

At present, Cricket only has support for Django project test suites.

In your Django project, install cricket, and then run it:

    $ pip install cricket
    $ python -m cricket.django

This will pop up a GUI window. Hit "Run all", and watch your test suite
execute.


Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

