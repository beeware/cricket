import sys
import time


def test_item_output():
    print("Hello?")
    print("More output?")
    print("But this is stderr", file=sys.stderr)
    print("Yet more?")


def slow():
    time.sleep(0.2)


for i in range(10):
    locals()[f"test_slow_{i}"] = slow
