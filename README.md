[<img src="https://beeware.org/project/projects/tools/cricket/cricket.png" width="72" alt="image" />](https://beeware.org/cricket)

# Cricket

[![Python versions](https://img.shields.io/pypi/pyversions/cricket.svg)](https://pypi.python.org/pypi/cricket)

[![Project version](https://img.shields.io/pypi/v/cricket.svg)](https://pypi.python.org/pypi/cricket)

[![Development status](https://img.shields.io/pypi/status/cricket.svg)](https://pypi.python.org/pypi/cricket)

[![Project license](https://img.shields.io/pypi/l/cricket.svg)](https://github.com/beeware/cricket/blob/main/LICENSE)

[![Build Status](https://github.com/beeware/cricket/workflows/CI/badge.svg?branch=main)](https://github.com/beeware/cricket/actions)

[![Discord server](https://img.shields.io/discord/836455665257021440?label=Discord%20Chat&logo=discord&style=plastic)](https://beeware.org/bee/chat/)

Cricket is part of the [BeeWare suite](https://beeware.org). The project
website is [https://beeware.org/cricket]().

Cricket is a graphical tool that helps you run your test suites.

Normal test runners dump all output to the console, and provide very
little detail while the suite is running. As a result:

- You can't start looking at failures until the test suite has completed
  running,
- It isn't a very accessible format for identifying patterns in test
  failures,
- It can be hard (or cumbersome) to re-run any tests that have failed.

Why the name `cricket`? [Test
Cricket](http://en.wikipedia.org/wiki/Test_cricket) is the most
prestigious version of the game of cricket. Games last for up to 5
days... just like running some test suites. The usual approach for
making cricket watchable is a generous dose of beer; in programming,
[Ballmer Peak](http://xkcd.com/323/) limits come into effect, so
something else is required...

## Quickstart

At present, Cricket has support for:

- unittest test suites; and
- [pytest](https://pytest.org) test suites; and
- [Django](https://djangoproject.com) 1.6+ project test suites

To use Cricket, install it with pip:

    $ pip install cricket

Then, to run your unittest suite:

    $ cricket-unittest

Or, in a pytest project:

    $ cricket-pytest

Or, in a Django project:

    $ cricket-django

`cricket-django` will also work in Django's own tests directory -- i.e.,
you can use `cricket-django` to run Django's own test suite (for Django
1.6 or later).

Running cricket will display a GUI window. Hit "Run all", and watch your
test suite execute. A progress bar is displayed in the bottom right hand
corner of the window, along with an estimate of time remaining.

While the suite is running, you can click on test names to see the
output of that test. The icon in the tree, and the summary panel on the
right, will display the status of the test, as well as any output or
error text.

## Documentation

Documentation for cricket can be found on [Read The
Docs](https://cricket.readthedocs.io).

## Community

Cricket is part of the [BeeWare suite](https://beeware.org). You can
talk to the community through:

- [@beeware@fosstodon.org on Mastodon](https://fosstodon.org/@beeware)
- [Discord](https://beeware.org/bee/chat/)

We foster a welcoming and respectful community as described in our
[BeeWare Community Code of
Conduct](https://beeware.org/community/behavior/).

## Contributing

If you experience problems with Cricket, [log them on
GitHub](https://github.com/beeware/cricket/issues).

If you want to contribute, please [fork the
project](https://github.com/beeware/cricket) and [submit a pull
request](https://github.com/beeware/cricket/pulls).

## Acknowledgements

Icons for Cricket come from [Icons8](https://icons8.com), and are used
under the terms of a [CC BY-ND
3.0](https://creativecommons.org/licenses/by-nd/3.0/) license.
