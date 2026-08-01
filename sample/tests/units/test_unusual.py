import sys
import time
from unittest import TestCase


class UnusualTests(TestCase):
    def test_item_output(self):
        print("Hello?")
        print("More output?")
        print("But this is stderr", file=sys.stderr)
        print("Yet more?")


def slow(self):
    time.sleep(0.2)


for i in range(10):
    setattr(UnusualTests, f"test_slow_{i}", slow)
