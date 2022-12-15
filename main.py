import GUI
import logic
import logging


def main():
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    gui_logger = logging.getLogger("GUI")
    gui_logger.setLevel(logging.DEBUG)
    db_logger = logging.getLogger("Database")
    db_logger.setLevel(logging.DEBUG)
    GUI.Root.logger = gui_logger
    logic.Database.logger = db_logger
    window = GUI.Root(logic.Database())
    window.mainloop()



if __name__ == "__main__":
    main()
