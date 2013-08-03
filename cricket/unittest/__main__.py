'''
This is the main entry point for running unittest test suites.
'''
from cricket.main import main as cricket_main
from cricket.unittest.model import UnittestProject


def main():
    cricket_main(UnittestProject)


if __name__ == "__main__":
    main()
