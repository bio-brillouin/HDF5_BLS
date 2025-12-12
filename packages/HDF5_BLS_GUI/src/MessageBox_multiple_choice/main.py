from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QApplication
)
from PySide6.QtCore import Qt
import sys
from pathlib import Path

from configparser import ConfigParser

class MessageBoxMultipleChoice(QDialog):
    def __init__(self, text, list_choice, element_italic=None, parent=None):
        super().__init__(parent)

        self.gui_root = str(Path(__file__).resolve().parent.parent.parent)

        # Load config file
        self.config = ConfigParser()
        self.config.read(f"{self.gui_root}/src/MessageBox_multiple_choice/config_Main.ini")

        # Set window title and geometry
        self.setWindowTitle("Choose an option")
        self.setGeometry(self.config["Geometry"].getint("x"),
                         self.config["Geometry"].getint("y"),
                         self.config["Geometry"].getint("width"),
                         self.config["Geometry"].getint("height"))
        
        # Initialize the dialog
        self.selected_choice = None
        self.result = None

        layout = QVBoxLayout(self)

        label = QLabel(text)
        layout.addWidget(label)

        self.combobox = QComboBox()
        for i, choice in enumerate(list_choice):
            self.combobox.addItem(choice)
            if element_italic and element_italic[i]:
                font = self.combobox.font()
                font.setItalic(True)
                self.combobox.setItemData(i, font, role=Qt.FontRole)
        layout.addWidget(self.combobox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

    def accept(self):
        self.selected_choice = self.combobox.currentText()
        self.result = "ok"
        super().accept()

    def reject(self):
        self.selected_choice = None
        self.result = "cancel"
        super().reject()

    @staticmethod
    def get_choice(text, list_choice, element_italic=None, parent=None):
        app = QApplication.instance() or QApplication(sys.argv)
        dialog = MessageBoxMultipleChoice(text, list_choice, element_italic, parent)
        dialog.exec_()
        return dialog.selected_choice, dialog.result

# Example usage:
if __name__ == "__main__":
    text = "Please select an option:"
    choices = ["Option 1", "Option 2", "Option 3"]
    italics = [False, True, False]
    selected, result = MessageBoxMultipleChoice.get_choice(text, choices, italics)
    print("Selected:", selected, "Result:", result)