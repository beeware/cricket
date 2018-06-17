# -*- coding: utf-8 -*-
import json
import os
import sys
import time

import pluggy
import py
import pytest


def pytest_addoption(parser):
    group = parser.getgroup("cricket", "BeeWare Cricket integration")
    group.addoption(
        '--cricket-mode', dest="cricket_mode", metavar="cricket_mode",
        action="store", choices=["discover", "execute", "off"], default="off",
        help="Cricket output mode")


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    if config.option.cricket_mode != 'off':
        # Unregister the default terminal reporter.
        config.pluginmanager.unregister(name="terminalreporter")

        # Force the traceback style to native.
        config.option.tbstyle = 'native'

    if config.option.cricket_mode == 'discover':
        reporter = CricketDiscoverReporter(config, file=sys.stdout)
        config.pluginmanager.register(reporter, "terminalreporter")
    elif config.option.cricket_mode == 'execute':
        reporter = CricketExecuteReporter(config, file=sys.stdout)
        config.pluginmanager.register(reporter, "terminalreporter")


class CricketReporter:
    def __init__(self, config, file=None):
        self.config = config
        self.file = file if file is not None else sys.stdout

        self.stats = {}

        # This is needed for compatibility; some other plugins
        # rely on the fact that there is a terminalreporter
        # plugin that has a _tw attribute.
        import _pytest.config
        self._tw = _pytest.config.create_terminal_writer(config, file)

    def print(self, *args, **kwargs):
        print(*args, **kwargs, file=self.file)

    def report(self, **kwargs):
        self.print(json.dumps(kwargs))

    def pytest_internalerror(self, excrepr):
        for line in str(excrepr).split("\n"):
            self.print("INTERNALERROR> " + line)
        return 1


class CricketDiscoverReporter(CricketReporter):
    def pytest_itemcollected(self, item):
        dirparts = item.nodeid.split('/')
        pathparts = dirparts[-1].split('::')

        parts = [
            ('dir', dirpart)
            for dirpart in dirparts
        ]

        if len(pathparts) == 2:
            parts.extend([
                ('file', pathparts[0]),
                ('test', pathparts[1]),
            ])
        elif len(pathparts) == 3:
            parts.extend([
                ('file', pathparts[0]),
                ('class', pathparts[1]),
                ('test', pathparts[2]),
            ])

        self.report(
            id=item.nodeid,
            path=parts
        )

    def pytest_collection_modifyitems(self, items, config):
        # In discovery mode, we don't actually want to run
        # the tests - so modify the list of test items
        # to be empty.
        items[:] = []


class CricketExecuteReporter(CricketReporter):
    def pytest_sessionstart(self, session):
        self._started = False

    def pytest_runtest_logstart(self, nodeid, location):
        if not self._started:
            self.print('\x02')  # ASCII STX (Start of Text)
            self._started = True

        self.report(
            path=nodeid,
            start_time=time.time()
        )

    def report_pass(self, report):
        self.report(
            status='OK',
            end_time=time.time(),
            description=report.nodeid,
            output=report.capstdout,
        )

    def report_fail(self, report):
        self.report(
            status='F',
            end_time=time.time(),
            description=report.nodeid,
            error=str(report.longrepr),
            output=report.capstdout,
        )

    def report_error(self, report):
        self.report(
            status='E',
            end_time=time.time(),
            description=report.nodeid,
            error=str(report.longrepr),
            output=report.capstdout,
        )

    def report_skip(self, report):
        self.report(
            status='s',
            end_time=time.time(),
            description=report.nodeid,
            error=report.longrepr[2],
            output=report.capstdout,
        )

    def report_expected_failure(self, report):
        self.report(
            status='x',
            end_time=time.time(),
            description=report.nodeid,
            error=str(report.longrepr),
            output=report.capstdout,
        )

    def report_unexpected_success(self, report):
        self.report(
            status='u',
            end_time=time.time(),
            description=report.nodeid,
            output=report.capstdout,
        )

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            if report.failed:
                if report.longrepr == 'Unexpected success':
                    # pytest raw xfail
                    self.report_unexpected_success(report)
                else:
                    if '\nAssertionError: ' in str(report.longrepr) \
                            or '\nFailed: ' in str(report.longrepr):
                        # pytest assertion
                        # unittest self.assert()
                        self.report_fail(report)
                    elif str(report.longrepr).startswith('[XPASS('):
                        # pytest xfail(strict=True)
                        self.report_unexpected_success(report)
                    else:
                        self.report_error(report)
            elif report.skipped:
                if isinstance(report.longrepr, tuple):
                    self.report_skip(report)
                else:
                    self.report_expected_failure(report)
            else:
                self.report_pass(report)
        else:
            if report.failed:
                self.report_error(report)
            elif report.skipped:
                if isinstance(report.longrepr, tuple):
                    self.report_skip(report)
                else:
                    self.report_expected_failure(report)

    def pytest_sessionfinish(self, exitstatus):
        self.print('\x03')    # ASCII ETX (End of Text)
