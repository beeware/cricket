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

    def __init__(self):

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
        suite = loader.discover('.')
        flatresults = list(consume(suite))
        named = [r.id() for r in flatresults]
        self.collected_tests = named


if __name__ == '__main__':

    PTD = PyTestDiscoverer()
    PTD.collect_tests()
    print(str(PTD))
