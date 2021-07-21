import sys
from callbacks import GUI

import faulthandler; faulthandler.enable()

from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = GUI()
    window.show()
    window.move(0, 30) # position of the main GUI
    sys.exit(app.exec_()) #this starts the main thread to run the GUI
