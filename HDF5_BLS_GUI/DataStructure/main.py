from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from DataStructure.UI.data_structure_ui import Ui_Dialog

class DataStructure(qtw.QDialog, Ui_Dialog):
    def __init__(self, parent=None, shape=None):
        super().__init__(parent)
        self.setupUi(self)

        self.l_Text.setText(f"The selected data file has the following shape {shape}")

        structures = []
        groups = [[1]]
        data_dim = [list(shape)]

        for i in shape: 
            structures.append("("+"x".join(str(e) for e in groups[-1])+") groups and arrays of dimension ("+"x".join(str(e) for e in data_dim[-1])+")")
            groups.append(groups[-1]+[i])
            data_dim.append(data_dim[-1][1:])

        self.cb_Structure.addItems(structures)

    def get_selected_structure(self):
        return self.cb_Structure.currentText()

        
    
        

