import sys
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from Main import main


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = main.MainWindow()

    window.show()

    sys.exit(app.exec())
