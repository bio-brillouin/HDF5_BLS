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

    # # Set up splash screen
    # pixmap = qtg.QPixmap(400, 300)
    # pixmap.fill(qtc.Qt.black)
    # splash = qtw.QSplashScreen(pixmap)
    # splash.showMessage("Starting...", alignment=qtc.Qt.AlignBottom | qtc.Qt.AlignCenter, color=qtc.Qt.white)
    # splash.show()

    # def load_modules(splash):
    #     modules = ["Loading UI...", "Connecting to Database...", "Loading Settings...", "Initializing Plugins..."]
    #     for i, msg in enumerate(modules):
    #         splash.showMessage(msg, alignment=qtc.Qt.AlignBottom | qtc.Qt.AlignCenter, color=qtc.Qt.white)
    #         qtw.QApplication.processEvents()  # Allows GUI to update
    #         time.sleep(0.1)  # Simulate loading time

    # qtc.QTimer.singleShot(100, lambda: load_modules(splash))

    # # Wait for all modules to "load", then show main window
    # def start_main():
    #     main_win = main.MainWindow()
    #     splash.finish(main_win)
    #     main_win.show()

    # qtc.QTimer.singleShot(1000, start_main)  # Match this with the load_modules time

    


