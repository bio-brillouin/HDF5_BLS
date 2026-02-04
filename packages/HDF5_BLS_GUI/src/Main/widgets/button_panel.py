from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Signal

class ButtonPanel(QWidget):
    new_requested = Signal()
    open_requested = Signal()
    save_requested = Signal()
    repack_requested = Signal()
    add_requested = Signal()
    remove_requested = Signal()
    export_code_requested = Signal()
    csv_requested = Signal()
    close_requested = Signal()

    def __init__(self, config, gui_root, parent=None):
        """Initializes the frame with all the buttons.
        """
        super().__init__(parent)
        self.config = config
        self.gui_root = gui_root
        self._initialize_buttons()

    def _initialize_buttons(self):
        # Create the button layout
        self.buttons_layout = QGridLayout(self)

        # Add the buttons and set their icon size based on the config file
        self.buttons = {}
        self.buttons['new'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/new_db.svg"), parent=self)
        self.buttons['open'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/open_db.svg"), parent=self)
        self.buttons['save'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/save.svg"), parent=self)
        self.buttons['repack'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/convert_bh5.svg"), parent=self)
        self.buttons['add'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/add_spectra.svg"), parent=self)
        self.buttons['remove'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/remove_spectra.svg"), parent=self)
        self.buttons['export_code'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/export_code.svg"), parent=self)
        self.buttons['csv'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/properties_to_csv.svg"), parent=self)
        self.buttons['close'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/exit.svg"), parent=self)

        # Add tooltips to the buttons
        self.buttons['new'].setToolTip("Create a new HDF5 file")
        self.buttons['open'].setToolTip("Open an HDF5 file")
        self.buttons['save'].setToolTip("Save the current data to an HDF5 file")
        self.buttons['repack'].setToolTip("Repack the HDF5 file")
        self.buttons['add'].setToolTip("Add a new spectrum to the HDF5 file")
        self.buttons['remove'].setToolTip("Remove an element from the HDF5 file")
        self.buttons['export_code'].setToolTip("Export the code of the current file")
        self.buttons['csv'].setToolTip("Export the selected element to a CSV file")

        # Set the size of the buttons at initialization
        icon_size = QSize(int(self.config["Buttons"]["size_x"]), int(self.config["Buttons"]["size_y"]))
        for button_key in self.buttons.keys():
            self.buttons[button_key].setIconSize(icon_size)
            self.buttons[button_key].setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 5px;
                }
                                                   
                QPushButton:hover {
                    background-color: #e1e1e1;
                    border-radius: 5px;
                }

                QPushButton:pressed {
                    background-color: #c1c1c1;
                }
            """)

        # Set the state of the buttons at initialization
        self.buttons['new'].setEnabled(True)
        self.buttons['open'].setEnabled(True)
        self.buttons['save'].setEnabled(True)
        self.buttons['repack'].setEnabled(True)
        self.buttons['add'].setEnabled(True)
        self.buttons['remove'].setEnabled(False)
        self.buttons['export_code'].setEnabled(False)
        self.buttons['csv'].setEnabled(False)
        self.buttons['close'].setEnabled(True)

        # Place the buttons in the layout
        self.buttons_layout.addWidget(self.buttons['new'], 0, 1, 1, 1)
        self.buttons_layout.addWidget(self.buttons['open'], 0, 2, 1, 1)
        self.buttons_layout.addWidget(self.buttons['save'], 0, 3, 1, 1)
        self.buttons_layout.addWidget(self.buttons['repack'], 0, 4, 1, 1)
        self.buttons_layout.addWidget(self.buttons['add'], 0, 5, 1, 1)
        self.buttons_layout.addWidget(self.buttons['remove'], 0, 6, 1, 1)
        self.buttons_layout.addWidget(self.buttons['export_code'], 0, 7, 1, 1)
        self.buttons_layout.addWidget(self.buttons['csv'], 0, 8, 1, 1)
        self.buttons_layout.addItem(QSpacerItem(int(self.config["Buttons"]["size_x"]), 
                                                int(self.config["Buttons"]["size_y"]), 
                                                QSizePolicy.Policy.Expanding, 
                                                QSizePolicy.Policy.Minimum), 
                                    0, 9, 1, 1)
        self.buttons_layout.addWidget(self.buttons['close'], 0, 10, 1, 1)

        # Connect the buttons
        self.buttons['new'].clicked.connect(self.new_requested)
        self.buttons['open'].clicked.connect(self.open_requested)
        self.buttons['repack'].clicked.connect(self.repack_requested)
        self.buttons['add'].clicked.connect(self.add_requested)
        self.buttons['remove'].clicked.connect(self.remove_requested)
        self.buttons['save'].clicked.connect(self.save_requested)
        self.buttons['export_code'].clicked.connect(self.export_code_requested)
        self.buttons['csv'].clicked.connect(self.csv_requested)
        self.buttons['close'].clicked.connect(self.close_requested)

    def set_button_enabled(self, button_key, enabled):
        if button_key in self.buttons:
            self.buttons[button_key].setEnabled(enabled)
