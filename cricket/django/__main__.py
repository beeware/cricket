from cricket.view import View
from cricket.django.model import DjangoProject


def main():
    project = DjangoProject()

    view = View(project)

    try:
        view.mainloop()
    except KeyboardInterrupt:
        view.on_quit()

if __name__ == "__main__":
    main()
