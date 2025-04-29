import sys
import os
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import time

# Add the HDF5_BLS package to the Python path
current_dir = os.path.abspath(os.path.dirname(__file__))
relative_path_libs = os.path.join(current_dir,"HDF5_BLS", "..", "..")
absolute_path_libs = os.path.abspath(relative_path_libs)
sys.path.append(absolute_path_libs)

from Main import main

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    main_win = main.MainWindow()
    main_win.show()
    sys.exit(app.exec())
    


