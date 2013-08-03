'''
This is the main entry point for running Django test suites.
'''
from cricket.main import main as cricket_main
from cricket.django.model import DjangoProject


def main():
    cricket_main(DjangoProject)


if __name__ == "__main__":
    main()
