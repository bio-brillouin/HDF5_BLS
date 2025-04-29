from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ProgressBar.UI.progress_bar_ui import Ui_Form

class ProgressBar(qtw.QDialog, Ui_Form):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.progressBar.setRange(0, 100)
        self.tB_Log.append(text)

    def update_progress(self, value, log_message=None):
        self.progressBar.setValue(value)
        if log_message:
            self.tB_Log.append(log_message)

        
    
        

