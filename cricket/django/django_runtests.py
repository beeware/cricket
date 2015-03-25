#!/usr/bin/env python
import os
import warnings
import argparse

from django.utils import importlib

import runtests


def django_tests(runner, labels):
    state = runtests.setup(1, labels)

    module_name, runner_class_name = runner.rsplit('.', 1)
    module = importlib.import_module(module_name)
    TestRunner = getattr(module, runner_class_name)

    runner = TestRunner(
        verbosity=1,
        interactive=False,
        failfast=False,
    )

    # Catch warnings thrown in test DB setup -- remove in Django 1.9
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            "Custom SQL location '<app_label>/models/sql' is deprecated, "
            "use '<app_label>/sql' instead.",
            PendingDeprecationWarning
        )
        failures = runner.run_tests(labels or runtests.get_installed())

    runtests.teardown(state)
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--settings", help="The settings file to use.", action="store")
    parser.add_argument("--testrunner", help="The test runner to use.", action="store")
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Test labels to execute.')

    options = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", options.settings)

    django_tests(options.testrunner, options.args)
