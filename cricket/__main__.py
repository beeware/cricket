from cricket.view import View
from cricket.model import Project


def main():
    project = Project()

    view = View(project)

    try:
        view.mainloop()
    except KeyboardInterrupt:
        view.on_quit()

if __name__ == "__main__":
    main()
