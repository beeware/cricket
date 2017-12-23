'''
This is the main entry point for running Django test suites.
'''
from cricket.main import main as cricket_main
from cricket.django.model import DjangoTestSuite


def main():
    return cricket_main(DjangoTestSuite)


if __name__ == "__main__":
    main().main_loop()
