from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from HelpFunction.UI.help_function_ui import Ui_Form

class HelpFunction(qtw.QDialog, Ui_Form):
    def __init__(self, parent=None, function_name = None, docstring = None):
        super().__init__(parent)
        self.setupUi(self)

        self.l_main.setText(f"Docstring of the function <b>{function_name}:</b>")

        split_doc = docstring.split("\n\n")
        if len(split_doc) > 2: split_doc.pop(2) # Delete return statement of docstring

        self.text_docstring.setText("\n\n".join(split_doc))

        self.b_close.clicked.connect(self.close)    

        
    
        

