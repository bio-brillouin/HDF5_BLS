import sys
from PySide6.QtWidgets import QApplication, QMainWindow

from Main.main import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()