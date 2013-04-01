from cricket.view import MainWindow
from cricket.django.model import DjangoProject


def main():
    project = DjangoProject()

    view = MainWindow(project)

    try:
        view.mainloop()
    except KeyboardInterrupt:
        view.on_quit()

if __name__ == "__main__":
    main()
