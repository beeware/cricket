import sys
import time


def test_item_output():
    print("Hello?")
    print("More output?")
    print("But this is stderr", file=sys.stderr)
    print("Yet more?")


def slow():
    time.sleep(0.2)


for i in range(0, 10):
    locals()['test_slow_{}'.format(i)] = slow
