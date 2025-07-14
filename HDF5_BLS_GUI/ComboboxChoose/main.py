from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ComboboxChoose.UI.multiple_choice_ui import Ui_Dialog

class ComboboxChoose(qtw.QDialog, Ui_Dialog):
    def __init__(self, text, list_choices, element_italic = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.l_Text.setText(text)

        if element_italic is None:
            element_italic = [False for i in range(len(list_choices))]

        i=0
        for choice, italic in zip(list_choices, element_italic):
            self.cb_Structure.addItem(choice)
            if italic:
                font = self.cb_Structure.font()
                font.setItalic(True)
                self.cb_Structure.setItemData(i, font, qtc.Qt.FontRole)
            i+=1

    def get_selected_structure(self):
        return self.cb_Structure.currentText()

        
    
        

