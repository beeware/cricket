import json
import unittest


def consume(iterable):
    input = list(iterable)
    while input:
        item = input.pop(0)
        try:
            data = iter(item)
            input = list(data) + input
        except:
            yield item


def discover_tests():
    '''
    Collect a list of potentially runnable tests
    '''

    loader = unittest.TestLoader()
    suite = loader.discover('.')

    for test in list(consume(suite)):
        print(test.id())


if __name__ == '__main__':
    discover_tests()
