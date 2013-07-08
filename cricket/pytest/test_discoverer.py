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

import re
import subprocess

RAW_EXPR = '\'\S*\''

# TODO: This would almost certainly be FAR simpler 
# using unittest.TestLoader.discover()

def get_fname(line):
    '''
    Transform e.g. <TestCaseFunction 'test_testCollection'>
    into
    test_testCollection
    '''
  
    c_expr = re.compile(RAW_EXPR)
    match = c_expr.search(line)
    fname = match.group()
    fname = fname [1:-1]

    return fname

class PyTestDiscoverer:
    '''

    '''

    def __init__(self):

        self.test_output = {}
        self.pytest_commandline = [
            'py.test',
            '--collectonly'
            ]


    def __str__(self):

        resultstr = ''

        for module in self.test_output.keys():
            for case in self.test_output[module]:
                for fname in self.test_output[module][case]:

                    resultstr += '\n' 
                    resultstr += '.'.join([module, case, fname])

        return resultstr.strip()


    def collect_tests(self):
        '''
        Collect a list of potentially runnable tests
        '''
        
        runner = subprocess.Popen(
            self.pytest_commandline,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )        

        self.testoutput = []
        for line in runner.stdout:
            line = line.strip()
            last_modulename = "ERROR"
            last_casename = "NONE"

            if '<Module' in line:
                modulename = get_fname(line)
                self.test_output[modulename] = {}
                last_modulename = modulename

            if '<UnitTestCase' in line:
                casename = get_fname(line)
                self.test_output[modulename][casename] = []
                last_casename = casename

            if '<TestCaseFunction' in line:
                fname = get_fname(line)
                self.test_output[modulename][casename].append(fname)


            
if __name__ == '__main__':

    PTD = PyTestDiscoverer()
    PTD.collect_tests()
    print str(PTD)