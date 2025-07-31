import sys
import os
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import time

from Main import main

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    main_win = main.MainWindow()
    main_win.show()
    sys.exit(app.exec())
    
