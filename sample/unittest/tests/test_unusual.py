from __future__ import print_function

import sys
import time
from unittest import TestCase, skip, expectedFailure


class UnusualTests(TestCase):
    def test_item_output(self):
        print("Hello?")
        print("More output?")
        print("But this is stderr", file=sys.stderr)
        print("Yet more?")


def slow(self):
    time.sleep(0.2)

for i in range(0, 10):
    setattr(UnusualTests, 'test_slow_{}'.format(i), slow)
