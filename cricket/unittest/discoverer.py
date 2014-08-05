'''
The whole purpose of this module is to generate printed output.
It should be of the form:

'module.testcase.specifictest'
'module.testcase.specifictest2'
'module2.testcase.specifictest'

etc

Its primary API is the command-line, but it can
just as easily be called programmatically (see __main__)
'''

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


class PyTestDiscoverer:

    def __init__(self, start='.', pattern='test*.py', top=None):
        self.start = start
        self.pattern = pattern
        self.top = top
        self.collected_tests = []

    def __str__(self):
        '''
        Builds the dotted namespace expected by cricket
        '''
        resultstr = '\n'.join(self.collected_tests)
        return resultstr.strip()

    def collect_tests(self):
        '''
        Collect a list of potentially runnable tests
        '''
        loader = unittest.TestLoader()
        suite = loader.discover(self.start, self.pattern, self.top)
        flatresults = list(consume(suite))
        named = [r.id() for r in flatresults]
        self.collected_tests = named


if __name__ == '__main__':
    from argparse import ArgumentParser
    from cricket.unittest.options import add_arguments

    parser = ArgumentParser()
    add_arguments(parser)
    options = parser.parse_args()

    PTD = PyTestDiscoverer(options.start, options.pattern, options.top)
    PTD.collect_tests()
    print str(PTD)
