import subprocess

class PyTestDiscoverer:

    def __init__(self):

        self.testoutput = None
        self.pytest_commandline = [
            'py.test',
            '--collectonly'
            ]


    def recognise(self, line):
        '''
        Just capturing runnable test modules at this stage
        '''

        if '<TestCaseFunction' in line:
            return True

        return False



    def collect_pytests(self):
        '''
        Collect a list of runnable tests
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

            if self.recognise(line):
                self.testoutput.append(line)

        return self.testoutput
            