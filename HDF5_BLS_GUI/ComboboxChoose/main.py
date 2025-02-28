from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ComboboxChoose.UI.multiple_choice_ui import Ui_Dialog

class ComboboxChoose(qtw.QDialog, Ui_Dialog):
    def __init__(self, text, list_choices, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.l_Text.setText(text)

        self.cb_Structure.addItems(list_choices)

    def get_selected_structure(self):
        return self.cb_Structure.currentText()

        
    
        

