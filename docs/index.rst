.. Django-Cricket documentation master file, created by
   sphinx-quickstart on Sat Feb  9 10:44:39 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Django-Cricket's documentation!
==========================================

Cricket a graphical tool that helps you run your Django test suite.

Django's test runner dumps all output to the console, and only at completion
of the test run. This isn't a very helpful format for identifying when (and
why) tests have failed, it doesn't let you start looking at failures until
the test suite has completed running, it isn't a very accessible format for
identifying patterns in test failures, and doesn't make it trivial to re-run
any tests that have failed.

There are also performance optimizations that can be made if the test database
isn't changing between runs -- you only need to create the database once, then
re-use it. Depending on your database setup, this can save a lot of running
time.

Why the name ``cricket``? Test Cricket is the most prestigious version of the
game of cricket. Games last for up to 5 days... just like running some test
suites :-)


Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

