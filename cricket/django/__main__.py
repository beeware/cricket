'''
This is the main entry point for running Django test suites.
'''
from cricket.main import main
from cricket.django.model import DjangoProject

if __name__ == "__main__":
    main(DjangoProject)
