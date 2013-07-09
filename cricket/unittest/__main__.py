'''
This is the main entry point for running unittest test suites.
'''
from cricket.main import main
from cricket.unittest.model import PyTestProject

if __name__ == "__main__":
    main(PyTestProject)
