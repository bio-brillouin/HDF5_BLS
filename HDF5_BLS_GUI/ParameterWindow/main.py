from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg

from ParameterWindow.UI.parameterWindow_ui import Ui_Dialog

class ParameterWindow(qtw.QDialog, Ui_Dialog):
    def __init__(self, text, list_parameters, root_path = None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(qtc.Qt.NonModal)

        self.root_path = root_path

        l_Text = qtw.QLabel(text)
        l_Text.setObjectName(u"l_Text")
        self.gridLayout_2.addWidget(l_Text, 0, 0, 1, 2)

        self.parameters = self.create_parameter_frame(list_parameters)

    def create_parameter_frame(self, list_parameters):
        dic = {}
        for i, e in enumerate(list_parameters):
            if "file_" in e:
                term = e.split("_")[1]
                label = qtw.QLabel(e)
                line_edit = qtw.QLineEdit()
                button = qtw.QPushButton("select file")
                button.clicked.connect(lambda: self.select_file(term, line_edit))

                self.gridLayout_2.addWidget(label, i+1, 0, 1, 1)
                self.gridLayout_2.addWidget(line_edit, i+1, 1, 1, 1)
                self.gridLayout_2.addWidget(button, i+1, 2, 1, 1)

                dic[e] = line_edit
            elif "bool_" in e:
                label = qtw.QLabel(e)
                checkbox = qtw.QCheckBox()

                self.gridLayout_2.addWidget(label, i+1, 0, 1, 1)
                self.gridLayout_2.addWidget(checkbox, i+1, 1, 1, 1)

                dic[e] = checkbox
            else:
                label = qtw.QLabel(e)
                line_edit = qtw.QLineEdit()

                self.gridLayout_2.addWidget(label, i+1, 0, 1, 1)
                self.gridLayout_2.addWidget(line_edit, i+1, 1, 1, 2)

                dic[e] = line_edit
        return dic

    def select_file(self, term, line_edit): 
        file_dialog = qtw.QFileDialog()
        file_dialog.setFileMode(qtw.QFileDialog.ExistingFile)
        if self.root_path: file_dialog.setDirectory(self.root_path)
        file_dialog.setNameFilter(f"{term} file (*.{term})")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            print("HERE - ", file_path)
            self.parameters[f"file_{term}"].setText(file_path)

    def get_selected_structure(self):
        values = {}
        for e in self.parameters.keys():
            try:
                values[e] = self.parameters[e].text()
            except:
                values[e] = self.parameters[e].checkState()
        return values

        
    
        
