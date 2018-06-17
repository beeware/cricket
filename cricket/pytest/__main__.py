'''
This is the main entry point for running pytest test suites.
'''
from cricket.app import main as cricket_main
from cricket.pytest.model import PyTestTestSuite


def main():
    return cricket_main(PyTestTestSuite)


if __name__ == "__main__":
    main().main_loop()
