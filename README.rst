.. image:: http://pybee.org/project/projects/tools/cricket/cricket.png
    :width: 72px
    :target: https://pybee.org/cricket

Cricket
=======

.. image:: https://img.shields.io/pypi/pyversions/cricket.svg
    :target: https://pypi.python.org/pypi/cricket

.. image:: https://img.shields.io/pypi/v/cricket.svg
    :target: https://pypi.python.org/pypi/cricket

.. image:: https://img.shields.io/pypi/status/cricket.svg
    :target: https://pypi.python.org/pypi/cricket

.. image:: https://img.shields.io/pypi/l/cricket.svg
    :target: https://github.com/pybee/cricket/blob/master/LICENSE

.. image:: https://beekeeper.herokuapp.com/projects/pybee/cricket/shield
    :target: https://beekeeper.herokuapp.com/projects/pybee/cricket

.. image:: https://badges.gitter.im/pybee/general.svg
    :target: https://gitter.im/pybee/general

Cricket is part of the `BeeWare suite`_. The project website is `http://pybee.org/cricket`_.

Cricket is a graphical tool that helps you run your test suites.

Normal test runners dump all output to the console, and provide very little
detail while the suite is running. As a result:

* You can't start looking at failures until the test suite has completed running,

* It isn't a very accessible format for identifying patterns in test failures,

* It can be hard (or cumbersome) to re-run any tests that have failed.

Why the name ``cricket``? `Test Cricket`_ is the most prestigious version of
the game of cricket. Games last for up to 5 days... just like running some
test suites. The usual approach for making cricket watchable is a generous
dose of beer; in programming, `Ballmer Peak`_ limits come into effect, so
something else is required...

.. _BeeWare suite: http://pybee.org/
.. _http://pybee.org/cricket: http://pybee.org/cricket
.. _Test Cricket: http://en.wikipedia.org/wiki/Test_cricket
.. _Ballmer Peak: http://xkcd.com/323/


Quickstart
----------

At present, Cricket has support for:

* `Django <https://djangoproject.com>`__ 1.6+ project test suites using unittest2-style discovery; and
* unittest project test suites; and
* `pytest <https://pytest.org>`__ test suites.

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
execute. A progress bar is displayed in the bottom right hand corner of
the window, along with an estimate of time remaining.

While the suite is running, you can click on test names to see the output
of that test. If the test passed, it will be displayed in green; other test
results will be shown in other colors.

Documentation
-------------

Documentation for cricket can be found on `Read The Docs`_.

Community
---------

Cricket is part of the `BeeWare suite`_. You can talk to the community through:

* `@pybeeware on Twitter`_

* The `pybee/general`_ channel on Gitter.

We foster a welcoming and respectful community as described in our
`BeeWare Community Code of Conduct`_.

Acknowledgements
----------------

Icons for Cricket come from `Icons8 <https://icons8.com>`__, and are used under the terms of a `CC BY-ND 3.0 <https://creativecommons.org/licenses/by-nd/3.0/>`__ license.

Contributing
------------

If you experience problems with cricket, `log them on GitHub`_. If you want to contribute code, please `fork the code`_ and `submit a pull request`_.

.. _Read The Docs: https://cricket.readthedocs.io
.. _@pybeeware on Twitter: https://twitter.com/pybeeware
.. _pybee/general: https://gitter.im/pybee/general
.. _BeeWare Community Code of Conduct: http://pybee.org/community/behavior/
.. _log them on Github: https://github.com/pybee/cricket/issues
.. _fork the code: https://github.com/pybee/cricket
.. _submit a pull request: https://github.com/pybee/cricket/pulls
