from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QDialogButtonBox
)
from PySide6.QtCore import Qt
from pathlib import Path
from configparser import ConfigParser

class AlgorithmWizard(QDialog):
    def __init__(self, title="", version="0.1", author="", institution="", description="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Algorithm wizard")
        
        self.gui_root = str(Path(__file__).resolve().parent.parent.parent)

        # Load config file
        self.config = ConfigParser()
        self.config.read(f"{Path(__file__).resolve().parent}/config_Algorithm.ini")

        self.setGeometry(self.config["Geometry"].getint("x"),
                         self.config["Geometry"].getint("y"),
                         self.config["Geometry"].getint("width"),
                         self.config["Geometry"].getint("height"))

        self._setup_ui()
        self._set_initial_values(title, version, author, institution, description)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title and Version
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Title:"))
        self.e_title = QLineEdit()
        row1.addWidget(self.e_title)
        
        row1.addWidget(QLabel("Version:"))
        self.e_version = QLineEdit()
        self.e_version.setFixedWidth(60)
        row1.addWidget(self.e_version)
        layout.addLayout(row1)

        # Author and Institution
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Author & Institution:"))
        self.e_author_inst = QLineEdit()
        self.e_author_inst.setPlaceholderText("Author (Institution)")
        row2.addWidget(self.e_author_inst)
        layout.addLayout(row2)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.t_description = QTextEdit()
        layout.addWidget(self.t_description)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("Apply")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _set_initial_values(self, title, version, author, institution, description):
        self.e_title.setText(title)
        self.e_version.setText(version)
        
        # If institution is provided separately (from legacy data), combine it
        if author and institution:
            self.e_author_inst.setText(f"{author} ({institution})")
        else:
            self.e_author_inst.setText(author)
            
        self.t_description.setPlainText(description)

    def get_data(self):
        """Returns the metadata from the fields."""
        return {
            "name": self.e_title.text(),
            "version": self.e_version.text(),
            "author": self.e_author_inst.text(),
            "description": self.t_description.toPlainText()
        }
