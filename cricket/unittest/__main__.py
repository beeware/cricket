'''
This is the main entry point for running unittest test suites.
'''
from cricket.app import main as cricket_main
from cricket.unittest.model import UnittestProject


def main():
    return cricket_main(UnittestProject)


if __name__ == "__main__":
    main().main_loop()
