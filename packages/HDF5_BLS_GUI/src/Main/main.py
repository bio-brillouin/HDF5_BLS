from PySide6.QtCore import Slot, QItemSelection, QPoint, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem, QIcon, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFileDialog, QGridLayout, QHBoxLayout, QMainWindow, QMenu, QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QTabWidget, QTableView, QTextBrowser, QTreeView, QVBoxLayout, QWidget

from configparser import ConfigParser
import pyperclip
from functools import partial
import os
from pathlib import Path

from HDF5_BLS import Wrapper
from HDF5_BLS.errors import WrapperError_Overwrite, WrapperError_Save, WrapperError_ArgumentType, WrapperError_StructureError   
from HDF5_BLS_analyse.VIPA import Analyse_VIPA
from HDF5_BLS_treat import Treat
from HDF5_BLS.wrapper import HDF5_group, HDF5_dataset
from HDF5_BLS.load_formats.load_errors import LoadError_creator, LoadError_parameters
from HDF5_BLS.load_data import load_general

from MessageBox_multiple_choice.main import MessageBoxMultipleChoice
from DataProcessing.main import DataProcessingWindow_Analyse, DataProcessingWindow_Treat

import time

class TreeviewItemModel(QStandardItemModel):
    def mimeData(self, indexes):
        mime_data = super().mimeData(indexes)
        if indexes:
            item = self.itemFromIndex(indexes[0])
            if item:
                path = self.get_item_path(item)
                mime_data.setData("application/x-brillouin-path", path.encode("utf-8"))
        return mime_data

    def get_item_path(self, item):
        path = [item.text()]
        while item.parent():
            item = item.parent()
            path.insert(0, item.text())
        return "/".join(path)

class MainWindow(QMainWindow):

    # Initialization of the application

    def __init__(self):
        """Initializes the main window
        """
        super().__init__()

        self.gui_root = str(Path(__file__).resolve().parent.parent.parent)

        # Initializes the wrapper
        self.wrp = Wrapper()

        # Load config file
        self.config = ConfigParser()
        self.config.read(self.gui_root+"/src/Main/config_Main.ini")

        # Set window title and geometry
        self.setWindowTitle(self.config['Default_contents']['title'])
        self.setGeometry(int(self.config['Geometry']['x']),
                         int(self.config['Geometry']['y']),
                         int(self.config['Geometry']['width']),
                         int(self.config['Geometry']['height']))

        # Create the treeview
        self._initialize_architecture_frame()

        # Create the properties frame
        self._initialize_properties_frame()

        # Create the button frame
        self._initialize_button_frame()

        # Create the log frame
        self._initialize_log_frame()

        # Create the log frame
        self._initialize_timer()

        # Update the structure and properties frames
        self.update_treeview()

        # Create the menu bar
        self._initialize_menubar()

        # Layout
        self._initialize_layout()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def _initialize_button_frame(self):
        """Initializes the frame with all the buttons
        """
        # Create the button layout
        self.buttons_layout = QGridLayout()

        # Add the buttons and set their icon size based on the config file
        self.buttons = {}
        self.buttons['new'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/new_db.svg"), parent=self)
        self.buttons['open'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/open_db.svg"), parent=self)
        self.buttons['save'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/save.svg"), parent=self)
        self.buttons['add'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/add_spectra.svg"), parent=self)
        self.buttons['remove'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/remove_spectra.svg"), parent=self)
        self.buttons['export_code'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/export_code.svg"), parent=self)
        self.buttons['csv'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/properties_to_csv.svg"), parent=self)
        self.buttons['close'] = QPushButton(icon=QIcon(f"{self.gui_root}/assets/img/exit.svg"), parent=self)

        # Add tooltips to the buttons
        self.buttons['new'].setToolTip("Create a new HDF5 file")
        self.buttons['open'].setToolTip("Open an HDF5 file")
        self.buttons['save'].setToolTip("Save the current data to an HDF5 file")
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
                    padding: 5px; /* Add some padding if needed */
                }
                                                   
                /* Hover state: Change background for visual feedback */
                QPushButton:hover {
                    background-color: #e1e1e1; /* A light grey */
                    border-radius: 5px; /* Optional: adds rounded corners */
                }

                /* Pressed state: Darker background */
                QPushButton:pressed {
                    background-color: #c1c1c1;
                }
            """)

        # Set the state of the buttons at initialization
        self.buttons['new'].setEnabled(True)
        self.buttons['open'].setEnabled(True)
        self.buttons['save'].setEnabled(True)
        self.buttons['add'].setEnabled(True)
        self.buttons['remove'].setEnabled(False)
        self.buttons['export_code'].setEnabled(False)
        self.buttons['csv'].setEnabled(False)
        self.buttons['close'].setEnabled(True)

        # Place the buttons in the layout
        self.buttons_layout.addWidget(self.buttons['new'], 0, 1, 1, 1)
        self.buttons_layout.addWidget(self.buttons['open'], 0, 2, 1, 1)
        self.buttons_layout.addWidget(self.buttons['save'], 0, 3, 1, 1)
        self.buttons_layout.addWidget(self.buttons['add'], 0, 4, 1, 1)
        self.buttons_layout.addWidget(self.buttons['remove'], 0, 5, 1, 1)
        self.buttons_layout.addWidget(self.buttons['export_code'], 0, 6, 1, 1)
        self.buttons_layout.addWidget(self.buttons['csv'], 0, 7, 1, 1)
        self.buttons_layout.addItem(QSpacerItem(int(self.config["Buttons"]["size_x"]), 
                                                int(self.config["Buttons"]["size_y"]), 
                                                QSizePolicy.Policy.Expanding, 
                                                QSizePolicy.Policy.Minimum), 
                                    0, 8, 1, 1)
        self.buttons_layout.addWidget(self.buttons['close'], 0, 9, 1, 1)

        # Connect the buttons
        self.buttons['new'].clicked.connect(self.new_hdf5)
        self.buttons['open'].clicked.connect(self.open_hdf5)
        self.buttons['add'].clicked.connect(self.add_data)
        self.buttons['remove'].clicked.connect(self.remove_element)
        self.buttons['save'].clicked.connect(self.save_hdf5)
        self.buttons['close'].clicked.connect(self.closeEvent)

        # Create the button frame
        self.buttons_widget = QWidget()
        self.buttons_widget.setLayout(self.buttons_layout)

    def _initialize_layout(self):
        """Initializes the layout of the window
        """
        self.layout = QGridLayout()
        self.layout.addWidget(self.buttons_widget, 1, 1, 1, 3)
        self.layout.addWidget(self.treeview, 3, 1, 1, 1)
        self.layout.addWidget(self.properties_widget, 3, 3, 1, 1)
        self.layout.addWidget(self.log, 5, 1, 1, 3)

    def _initialize_log_frame(self):
        """Initializes the log text browser
        """
        # Create the log widget
        self.log = QTextBrowser()
        self.log.setMaximumHeight(self.log.fontMetrics().height() * self.config["Log"].getint("Height"))

    def _initialize_properties_frame(self):
        """Initializes the frame with the property tabs and the visualization tab.
        """
        # Create the properties widget
        self.properties_tab_wdg = QTabWidget()

        # Create the three tabs
        self.properties_measure_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.properties_measure_wdg, "Measure")
        msr_lyt = QGridLayout(self.properties_measure_wdg)

        self.properties_spectrometer_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.properties_spectrometer_wdg, "Spectrometer")
        spc_lyt = QGridLayout(self.properties_spectrometer_wdg)

        self.properties_other_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.properties_other_wdg, "Other")
        oth_lyt = QGridLayout(self.properties_other_wdg)

        self.visualization_wdg = QWidget()
        self.properties_tab_wdg.addTab(self.visualization_wdg, "Visualization")
        vis_lyt = QGridLayout(self.visualization_wdg)

        # Create the tableviews for the tabs
        self.properties_measure_tableview = QTableView(self.properties_measure_wdg)
        msr_lyt.addWidget(self.properties_measure_tableview, 0, 0, 1, 1)
        msr_lyt.setContentsMargins(0, 0, 0, 0)
        self.properties_spectrometer_tableview = QTableView(self.properties_spectrometer_wdg)
        spc_lyt.addWidget(self.properties_spectrometer_tableview, 0, 0, 1, 1)
        spc_lyt.setContentsMargins(0, 0, 0, 0)
        self.properties_other_tableview = QTableView(self.properties_other_wdg)
        oth_lyt.addWidget(self.properties_other_tableview, 0, 0, 1, 1)
        oth_lyt.setContentsMargins(0, 0, 0, 0)

        # Create the models for the tableviews
        self.properties_measure_model = QStandardItemModel()
        self.properties_measure_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_measure_tableview.setModel(self.properties_measure_model)
        self.properties_spectrometer_model = QStandardItemModel()
        self.properties_spectrometer_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_spectrometer_tableview.setModel(self.properties_spectrometer_model)
        self.properties_other_model = QStandardItemModel()
        self.properties_other_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_other_tableview.setModel(self.properties_other_model)

        # Add buttons for adding and removing attributes
        self.properties_buttons_layout = QHBoxLayout()
        self.btn_add_attribute = QPushButton("Add Attribute")
        self.btn_remove_attribute = QPushButton("Remove Attribute")
        self.properties_buttons_layout.addWidget(self.btn_add_attribute)
        self.properties_buttons_layout.addWidget(self.btn_remove_attribute)
        
        self.properties_layout = QVBoxLayout()
        self.properties_layout.addWidget(self.properties_tab_wdg)
        self.properties_layout.addLayout(self.properties_buttons_layout)
        self.properties_widget = QWidget()
        self.properties_widget.setLayout(self.properties_layout)
        
        # Connect buttons
        self.btn_add_attribute.clicked.connect(self.add_attribute)
        self.btn_remove_attribute.clicked.connect(self.remove_attribute)

    def _initialize_menubar(self):
        """Initializes the menu bar.
        """
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction(QIcon(f"{self.gui_root}/assets/img/new_db.svg"), "&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_hdf5)
        file_menu.addAction(new_action)

        open_action = QAction(QIcon(f"{self.gui_root}/assets/img/open_db.svg"), "&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_hdf5)
        file_menu.addAction(open_action)

        save_action = QAction(QIcon(f"{self.gui_root}/assets/img/save.svg"), "&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_hdf5)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction(QIcon(f"{self.gui_root}/assets/img/exit.svg"), "&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        add_attr_action = QAction("Add Attribute", self)
        add_attr_action.triggered.connect(self.add_attribute)
        edit_menu.addAction(add_attr_action)

        remove_attr_action = QAction("Remove Attribute", self)
        remove_attr_action.triggered.connect(self.remove_attribute)
        edit_menu.addAction(remove_attr_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        export_attrs_action = QAction("Export Normalized Attributes", self)
        export_attrs_action.triggered.connect(self.export_normalized_attributes)
        tools_menu.addAction(export_attrs_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction(QIcon(f"{self.gui_root}/assets/img/help.svg"), "&About", self)
        about_action.triggered.connect(lambda: QMessageBox.about(self, "About HDF5_BLS", "HDF5_BLS GUI\nVersion 1.0"))
        help_menu.addAction(about_action)

    def _initialize_architecture_frame(self):
        """Initializes the architecture frame with the treeview.
        """
        # Create the treeview
        self.treeview = QTreeView()

        # Create the model displayed in the treeview
        self.architecture_file_model = TreeviewItemModel()

        # Set the model of the treeview
        self.treeview.setModel(self.architecture_file_model)

        # Connects the selection of the treeview to the function that handles the event when a treeview element is selected
        self.treeview.selectionModel().selectionChanged.connect(self.treeview_element_selected)

        # Connects the changing of an element of the model to the function that handles these changes
        self.architecture_file_model.dataChanged.connect(self.treeview_element_changed)

        # Set the drag and drop behavior of the treeview
        self.treeview.setAcceptDrops(True)
        self.treeview.setDragEnabled(False)  # Optional: Prevent dragging from TreeView
        self.treeview.setDragDropMode(QAbstractItemView.DropOnly)
        self.treeview.dragEnterEvent = self.treeview_dragEnterEvent
        self.treeview.dragMoveEvent = self.treeview_dragMoveEvent
        self.treeview.dropEvent = self.treeview_dropEvent

        # Set the context menu policy
        self.treeview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeview.customContextMenuRequested.connect(self.treeview_context_menu)

        # Sets the selection mode of the tree view
        self.treeview.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeview.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.treeview.setStyleSheet("""
            QTreeView::item:selected {
                background-color: lightblue;
                color: black;
            }
        """)

        # Set context menu policy for the tree view
        self.treeview.expanded.connect(self.adjust_treeview_columns)
    
    def _initialize_timer(self):
        self.current_hover_index = None  # Initialize the current hover index
        self.hover_timer = QTimer(self) 
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.expand_on_hover)  # Connect to the expand function

    # Closing the window

    @Slot()
    def closeEvent(self, event):
        """Close the window and exit the application.
        """
        # Handle the error if the wrapper is not saved
        if self.wrp.save:
            if not self.handle_error_save(): return
        
        # Delete the temporary file if it exists
        self.wrp.close(delete_temp_file = True)

        # Close the application
        self.close()

    # Error handling

    def handle_error_save(self):
        """Function that handles the error when trying to close the wrapper without saving it. 
        If the user saves it or decides to delete the file, returns True. If the user decides to cancel the action that raised an error, returns False.

        Returns
        -------
        bool
            True if the user saved the wrapper or decided to discard it, False if the user cancelled the action.
        """
        dialog = QMessageBox.question(self,"Unsaved changes", "The file has not been saved yet. Do you want to save it?", QMessageBox.Yes | QMessageBox.No |QMessageBox.Cancel)
        if dialog == QMessageBox.Yes:
            self.save_hdf5()
            self.wrp.close()
        elif dialog == QMessageBox.No:
            self.wrp.save = False
            self.wrp.close()
        elif dialog == QMessageBox.Cancel:
            return False
        return True

    # Updating the models of the treeview and the parameters

    def update_treeview(self):
        """Recreates the model of the treeview with the content of the HDF5 file located under the "Brillouin" group.
        Fills the columns of the treeview with the corresponding attributes of the HDF5 file, following the columns given in the configuration file.
        Selects the first element of the treeview, corresponding to the "Brillouin" element and updates the "treeview_selected" attribute.
        """
        def fill(item: QStandardItem = QStandardItem("Brillouin"), parent: str = "Brillouin"):
            """Recursive function to create the model to be displayed on the treeview.

            Parameters
            ----------
            item : QStandardItem, optional
                The parent item to which append the new items, by default an empty QStandardItem with name "Brillouin"
            parent : str, optional
                The path to the parent item in the HDF5 file, by default "Brillouin"

            Returns
            -------
            QStandardItem
                The item with all the children of the parent organized following the guidelines of the treeview.
            """
            if parent == "Brillouin": 
                item.setData("Brillouin", Qt.UserRole)
            # Go through all the children of the parent in the HDF5 file
            for elt in self.wrp.get_children_elements(path = parent):
                # Create the item with the name of the child in the HDF5 file
                loc_item = QStandardItem(elt)
                loc_item.setData(f"{parent}/{elt}", Qt.UserRole)
                self.set_icon_brillouin_type(loc_item, self.wrp.get_type(path=f"{parent}/{elt}", return_Brillouin_type=True))
                # Create a temporary list to store the items to be added to the model
                temp = [loc_item]
                # Get the attributes of the child in the HDF5 file
                attributes = self.wrp.get_attributes(path = f"{parent}/{elt}")
                # Go through the columns of the treeview and fill the model with the corresponding attributes taken from the HDF5 file
                for properties in self.config['Treeview']['columns'].split(',')[1:]:
                    if properties in attributes:
                        temp.append(QStandardItem(attributes[properties]))
                    else:
                        temp.append(QStandardItem(""))
                # Append the items to the model
                item.appendRow(temp)

                # Recursively fill the model with the children of the child
                fill(loc_item, f"{parent}/{elt}")
            return item

        # Clear the model
        self.architecture_file_model.clear()

        # Fill the model
        temp = self.config['Treeview']['columns'].split(',')
        columns = []
        for e in temp:
            if "MEASURE." in e:
                columns.append(e[8:].replace("_", " "))
            elif "SPECTROMETER." in e:
                columns.append(e[13:].replace("_", " "))
            elif "FILEPROP." in e:
                columns.append(e[10:].replace("_", " "))
            else:
                columns.append(e.replace("_", " "))
        self.architecture_file_model.setHorizontalHeaderLabels(columns)
        self.architecture_file_model.appendRow([fill()])

        # Connects the changing of an element of the model to the function that handles these changes
        self.architecture_file_model.dataChanged.connect(self.treeview_element_changed)

        # Select the first element of the treeview, corresponding to the "Brillouin" element
        self.treeview.setCurrentIndex(self.architecture_file_model.index(0, 0))

    def update_properties(self):
        """Update the properties frame.
        """
        # Extract the attributes of the element selected
        attr = self.wrp.get_attributes(self.treeview.currentIndex().data(Qt.UserRole))

        # Update the tables associated to the measure and spectrometer
        self.properties_measure_model.clear()
        self.properties_measure_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_spectrometer_model.clear()
        self.properties_spectrometer_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])
        self.properties_other_model.clear()
        self.properties_other_model.setHorizontalHeaderLabels(["Name", "Value", "Units"])

        for k, v in attr.items():
            try:
                if "." in k:
                    cat, name = k.split(".")
                    name = name.split("_")
                    if name[-1][0] == "(" and name[-1][-1] == ")": unit = name.pop(-1)[1:-1]
                    else: unit = ""
                    if cat == "MEASURE":
                        self.properties_measure_model.appendRow([QStandardItem(" ".join(name)), QStandardItem(v), QStandardItem(unit)])
                    elif cat == "SPECTROMETER":
                        self.properties_spectrometer_model.appendRow([QStandardItem(" ".join(name)), QStandardItem(v), QStandardItem(unit)])
                    else:
                        if len(v)>100: v = v[:100]+"..."
                        self.properties_other_model.appendRow([QStandardItem(" ".join(k.split("_"))), QStandardItem(v), QStandardItem(unit)])
                else:
                    if len(v)>100: v = v[:100]+"..."
                    self.properties_other_model.appendRow([QStandardItem(" ".join(k.split("_"))), QStandardItem(v), QStandardItem(unit)])
            except:
                pass

        # Enable drop event
        self.properties_tab_wdg.setAcceptDrops(True)
        self.properties_tab_wdg.dropEvent = self.properties_dropEvent
        self.properties_tab_wdg.dragEnterEvent = self.properties_dragEnterEvent
        self.properties_tab_wdg.dragMoveEvent = self.properties_dragMoveEvent

        self.properties_measure_tableview.setAcceptDrops(True)
        self.properties_measure_tableview.dropEvent = self.properties_dropEvent
        self.properties_measure_tableview.dragEnterEvent = self.properties_dragEnterEvent
        self.properties_measure_tableview.dragMoveEvent = self.properties_dragMoveEvent

        self.properties_spectrometer_tableview.setAcceptDrops(True)
        self.properties_spectrometer_tableview.dropEvent = self.properties_dropEvent
        self.properties_spectrometer_tableview.dragEnterEvent = self.properties_dragEnterEvent
        self.properties_spectrometer_tableview.dragMoveEvent = self.properties_dragMoveEvent

        self.properties_other_tableview.setAcceptDrops(True)
        self.properties_other_tableview.dropEvent = self.properties_dropEvent
        self.properties_other_tableview.dragEnterEvent = self.properties_dragEnterEvent
        self.properties_other_tableview.dragMoveEvent = self.properties_dragMoveEvent

    def set_icon_brillouin_type(self, item, brillouin_type):
        """Set the icon of the item corresponding to the brillouin type.

        Parameters
        ----------
        item : QStandardItem
            The item to set the icon of.
        brillouin_type : str
            The brillouin type of the item.
        """
        item.setIcon(QIcon(f"{self.gui_root}/assets/img/{brillouin_type}.svg"))

    # HDF5 global file interaction

    def new_hdf5(self):
        """Create a new HDF5 file.
        """
        if self.wrp.save:
            if not self.handle_error_save():
                return
        
        self.wrp = Wrapper()
        self.filepath = None
            
        # Update treeview
        self.update_treeview()
        self.treeview.setCurrentIndex(self.architecture_file_model.index(0, 0))

        # Update parameters with the parameters of the file
        # self.treeview.currentIndex().data(Qt.UserRole) = "Brillouin"
        # self.update_parameters()

        self.log.append(f"A new file has been created <b>Please save it to a non-temporary location</b>")

    @Slot()
    def open_hdf5(self, filepath = None):
        """Open an HDF5 file and update the tree view and parameters.

        Parameters
        ----------
        filepath : str, optional
            The path to the HDF5 file. If None, a file dialog will open to select a file.
        """
        if filepath is None or filepath == False:
            filepath = QFileDialog.getOpenFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
            if filepath is None: return
            else: self.filepath = filepath
        else:
            self.filepath = filepath 

        if self.wrp.save:
            if not self.handle_error_save():
                return
        
        # Update the wrapper to the new file
        self.wrp = Wrapper(filepath)
            
        # Update treeview
        self.update_treeview()

        # Select the first element of the treeview, corresponding to the "Brillouin" element
        self.treeview.setCurrentIndex(self.architecture_file_model.index(0, 0))
        # self.treeview.currentIndex().data(Qt.UserRole) = "Brillouin"

        # Update properties on the first element of the treeview
        self.update_properties()

        # Enable buttons
        self.buttons['remove'].setEnabled(False)
        self.buttons['export_code'].setEnabled(False)
        self.buttons['csv'].setEnabled(False)

        # Log the opening of the file
        self.log.append(f"<i>{self.filepath}</i> opened")

    def repack(self):
        """Repacks the wrapper to minimize its size.
        """
        self.wrp.repack(force_repack=True)
        self.log.append(f"The HDF5 file located at <i>{self.filepath}</i> has been repacked")

    def save_hdf5(self):
        """Save the current data to an HDF5 file.
        """
        self.filepath = QFileDialog.getSaveFileName(self, "Save File", "", "HDF5 Files (*.h5)")[0]
        if self.filepath:
            # We first try to save the file, if the file already exists, then the user is asked if he wants to overwrite it by the system (not done by this code)
            try:
                self.wrp.save_as_hdf5(self.filepath)
            # If the user continues despite the system error message, we overwrite the file
            except WrapperError_Overwrite:
                self.wrp.save_as_hdf5(self.filepath, overwrite = True)
            self.log.append(f"<i>{self.filepath}</i> has been saved")

    # Data interaction

    def add_data(self, filepaths = None, parent_item = None, update_treeview = True, creator = None, parameters = None):
        """Add a new element to the HDF5 file.
        """
        def check_creator_parameters(filepath, creator, parameters):
            try:
                load_general(filepath, creator = creator, parameters = parameters)
            except LoadError_creator as e:
                creator = str(e).split(": ")[1].split(", ")
                creator, _ = MessageBoxMultipleChoice.get_choice("Please choose the file extension to add from the directories.", creator)
                try:
                    load_general(filepath, creator = creator)
                except LoadError_parameters as e:
                    QMessageBox.warning(self, "Error", "To do: parameters are needed to import the data.")
            except LoadError_parameters as e:
                    QMessageBox.warning(self, "Error", "To do: parameters are needed to import the data.")
            return creator, parameters

        def add_single_file(filepath, parent_item):
            """Adds a single file both to the HDF5 file and the treeview
            """
            if parent_item is None: 
                parent_item = self.architecture_file_model.itemFromIndex(self.treeview.currentIndex())
            name_file = filepath.split("/")[-1].split(".")[0]

            # If the parent group is not a group but a dataset, we change the parent group and the parent item
            if self.wrp.get_type(path=parent_item.data(Qt.UserRole)) == HDF5_dataset:
                add_single_file(filepath, parent_item.parent())
            
            # If parent group is a "root" group, we create a new "measure" group with the name of the file
            elif self.wrp.get_type(path=parent_item.data(Qt.UserRole), return_Brillouin_type=True) == "Root":
                self.add_group(name = name_file, parent_item=parent_item, brillouin_type="Measure")
                parent_item = self.architecture_file_model.itemFromIndex(self.treeview.currentIndex())
                    
            # File addition to the selected group
            try: 
                self.wrp.import_raw_data(filepath = filepath, 
                                         parent_group = parent_item.data(Qt.UserRole), 
                                         name = "Raw data",
                                         creator = creator,
                                         parameters = parameters)
                self.log.append(f"<i>{filepath}</i> imported")
                if update_treeview:
                    item = QStandardItem("Raw data")
                    item.setData(f"{parent_item.data(Qt.UserRole)}/Raw data", Qt.UserRole)
                    self.set_icon_brillouin_type(item, "Raw_data")
                    parent_item.appendRow([item])
                    self.architecture_file_model.indexFromItem(item)
            
            except KeyError: 
                self.wrp.import_PSD(filepath = filepath, 
                                    parent_group = parent_item.data(Qt.UserRole), 
                                    name = "PSD",
                                    creator = creator,
                                    parameters = parameters)
                self.log.append(f"<i>{filepath}</i> imported")
                if update_treeview:
                    item_f = QStandardItem("Frequency")
                    item_f.setData(f"{parent_item.data(Qt.UserRole)}/Frequency", Qt.UserRole)
                    self.set_icon_brillouin_type(item_f, "Frequency")
                    parent_item.appendRow([item_f])
                    item = QStandardItem("PSD")
                    item.setData(f"{parent_item.data(Qt.UserRole)}/PSD", Qt.UserRole)
                    self.set_icon_brillouin_type(item, "PSD")
                    parent_item.appendRow([item])
                    self.architecture_file_model.indexFromItem(item)
                    
            except WrapperError_Overwrite as e:
                dialog = QMessageBox()
                dialog.setIcon(QMessageBox.Warning)
                dialog.setWindowTitle('Warning')
                dialog.setText(f"{e} Do you want to overwrite it, add the droped dataset as an 'Other' dataset or cancel the action?")
                dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
                dialog.button(QMessageBox.Yes).setText('Overwrite')
                dialog.button(QMessageBox.No).setText('Add as an Other dataset')
                dialog.button(QMessageBox.Cancel).setText('Cancel')
                response = dialog.exec_()
                if response == QMessageBox.Yes:
                    self.wrp.import_raw_data(filepath = filepath, 
                                             parent_group=parent_item.data(Qt.UserRole), 
                                             name = "Raw data", overwrite=True)
                    self.architecture_file_model.indexFromItem(parent_item.child(parent_item.rowCount()-1))
                    self.log.append(f"<i>{filepath}</i> imported")
                elif response == QMessageBox.No:
                    QMessageBox.information(self, "To do", "Add the dropped dataset as an 'Other' dataset")
            
            except LoadError_creator as e:
                raise e

            except Exception as e:
                print(e)
                QMessageBox.warning(self, "Error", f"{e}")

        if filepaths is None:
            filepaths = QFileDialog.getOpenFileNames(self, "Select a file to add", "All files (*)")[0]
            if len(filepaths) == 0: return
            creator, parameters = check_creator_parameters(filepaths, creator, parameters)
            self.add_data(filepaths, parent_item, update_treeview)
        elif type(filepaths) == str:
            creator, parameters = check_creator_parameters(filepaths, creator, parameters)
            add_single_file(filepaths, parent_item)
        elif len(filepaths) == 1:
            creator, parameters = check_creator_parameters(filepaths[0], creator, parameters)
            add_single_file(filepaths[0], parent_item)
        else:
            creator, parameters = check_creator_parameters(filepaths[0], creator, parameters)
            for filepath in filepaths:
                add_single_file(filepath, parent_item)

    def add_attribute(self):
        """Add a new attribute to the selected element.
        """
        from .attribute_dialog import AddAttributeDialog
        dialog = AddAttributeDialog(self)
        if dialog.exec_():
            full_name, value = dialog.get_data()
            path = self.treeview.currentIndex().data(Qt.UserRole)
            if path:
                try:
                    self.wrp.add_attributes(attributes={full_name: value}, parent_group=path)
                    self.update_properties()
                    self.log.append(f"Attribute <b>{full_name}</b> added to <i>{path}</i>")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not add attribute: {e}")

    def export_normalized_attributes(self):
        """Export the normalized list of attributes to an Excel file.
        """
        from HDF5_BLS import NormalizedAttributes
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Normalized Attributes", str(Path.home() / "normalized_attributes.xlsx"), "Excel Files (*.xlsx)")
        if filepath:
            try:
                NormalizedAttributes.to_excel(filepath)
                self.log.append(f"Normalized attributes exported to <i>{filepath}</i>")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not export normalized attributes: {e}")

    def remove_attribute(self):
        """Remove an attribute from the selected element.
        """
        print("remove_attribute called")

    def add_directory(self, filepaths, parent_item, update_treeview = True, extension = None, creator = None, parameters = None):
        """Add a directory to the HDF5 file.

        Parameters
        ----------
        filepaths : str or list of str
            The path to the file to add or a list of paths to add.
        parent_group : str, optional
            The parent group where to store the data of the HDF5 file, by default the parent group is the top group "Data". The format of this group should be "Brillouin/Data".
        overwrite : bool, optional
            A flag to indicate wether to update the group or not. Usefull when lists of filepaths are used. By default True for strings, False for lists
        update_treeview : bool
            A flag to indicate wether to update the treeview or not. Usefull when lists of filepaths are used. By default True when filepaths is a string, False for lists
        
        Return
        ------
        QStandardItem
            The item corresponding to the root of the added HDF5 file.
        """     
        def list_extensions_children(filepaths, extensions = []):
            """Recursive function to list all the file extensions in the directory
            """
            if type(filepaths) is str:
                filepath = filepaths
                for f in os.listdir(filepath):
                    if os.path.isdir(os.path.join(filepath, f)):
                        extensions = list_extensions_children(os.path.join(filepath, f), extensions)
                    elif not f.split(".")[-1] in extensions:
                        extensions.append(f.split(".")[-1])
            elif len(filepaths) == 1:
                filepath = filepaths[0]
                extensions = list_extensions_children(filepath, extensions)
            else:
                for f in filepaths:
                    extensions = list_extensions_children(f, extensions)
            return extensions

        # List all the file extensions in the directory
        extensions = list_extensions_children(filepaths)

        # Remove .DS_Store from the list of extensions
        if "DS_Store" in extensions: 
            extensions.remove("DS_Store")
        
        # If dealing with a list of directories, we create a new group for each directory and add their contents to the created group.
        if type(filepaths) == list:
            if extension is None:
                extension, _ = MessageBoxMultipleChoice.get_choice("Please choose the file extension to add from the directories.", extensions)
            for filepath in filepaths:
                name = os.path.basename(filepath)
                if name == "":
                    name = os.path.basename(os.path.dirname(filepath))
                if name in [".DS_Store", ""]: continue
                self.add_group(name = name, parent_item=parent_item, brillouin_type="Root")
                self.add_directory(filepaths = filepath, 
                                   parent_item = self.architecture_file_model.itemFromIndex(self.treeview.currentIndex()), 
                                   update_treeview = False, 
                                   extension=extension)

            self.update_treeview()
            self.update_properties()
            return

        if extension is None:
            extension, _ = MessageBoxMultipleChoice.get_choice("Please choose the file extension to add from the directories.", extensions)
        filepath = filepaths

        # First check that we have everything we need to add the data
        for f in os.listdir(filepath):
            if not os.path.isdir(os.path.join(filepath, f)) and f.split(".")[-1] == extension:
                path = os.path.join(filepath, f)
                try:
                    load_general(path)
                except LoadError_creator as e:
                    creator = str(e).split(": ")[1].split(", ")
                    creator, _ = MessageBoxMultipleChoice.get_choice("Please choose the file extension to add from the directories.", creator)
                    try:
                        load_general(path, creator = creator)
                    except LoadError_parameters as e:
                        QMessageBox.warning(self, "Error", "To do: parameters are needed to import the data.")
                        return
                    break
                except LoadError_parameters as e:
                        QMessageBox.warning(self, "Error", "To do: parameters are needed to import the data.")

        # Then go through the directory and add the data
        for f in os.listdir(filepath):
            if not os.path.isdir(os.path.join(filepath, f)) and f.split(".")[-1] == extension:
                path = os.path.join(filepath, f)
                self.add_data(filepaths = path, 
                              parent_item = parent_item, 
                              update_treeview=False,
                              creator = creator,
                              parameters = parameters)
            elif os.path.isdir(os.path.join(filepath, f)):
                self.add_directory(filepaths = [os.path.join(filepath, f)], 
                                   parent_item = parent_item, 
                                   update_treeview = False, 
                                   extension=extension,
                                   creator = creator,
                                   parameters = parameters)

        index_parent_item = self.architecture_file_model.indexFromItem(parent_item)
        if update_treeview: 
            self.update_treeview()
            self.treeview.setCurrentIndex(index_parent_item)
            self.treeview.expand(index_parent_item)
            self.update_properties()

    def add_group(self, name = "New group", brillouin_type = "Root", parent_item = None):
        """Add a new group to the HDF5 file.
        """
        if parent_item is None:
            parent_item = self.architecture_file_model.itemFromIndex(self.treeview.currentIndex())

        parent_group = parent_item.data(Qt.UserRole)

        if self.wrp.get_type(path=parent_group, return_Brillouin_type=True) != "Root":
            QMessageBox.warning(self, "Warning", "You can only add a group to a group of type 'Root'.")
            return
        
        self.wrp.create_group(name = name, parent_group=parent_group, brillouin_type=brillouin_type)

        # Append the new group to the item
        new_item = QStandardItem(name)
        new_item.setData(f"{parent_group}/{name}", Qt.UserRole)
        self.set_icon_brillouin_type(new_item, brillouin_type)
        parent_item.appendRow([new_item])
        new_index = self.architecture_file_model.indexFromItem(new_item)

        # Expand the treeview to the new item and select it
        # self.treeview.currentIndex().data(Qt.UserRole) = f"{parent_group}/{name}"
        self.treeview.setCurrentIndex(new_index)
        self.treeview.expand(new_index)

        # Edit the name of the new group if it has been created with default name
        if name == "New group":
            self.treeview.edit(new_index) 

    def add_hdf5(self, filepaths, parent_item, update_treeview = True):
        """Adds an HDF5 file to the treeview and wrapper under the given parent item

        Parameters
        ----------
        filepaths : str or list of str
            The path to the file to add or a list of paths to add.
        parent_item : QStandardItem
            The item corresponding to the parent under which to add the filepath.
        update_treeview : bool
            A flag to indicate wether to update the treeview or not. Usefull when lists of filepaths are used. By default True for strings, False for lists
        
        Return
        ------
        QStandardItem
            The item corresponding to the root of the added HDF5 file.
        """     
        # If dealing with a list of HDF5 files
        if type(filepaths) == list:
            for filepath in filepaths:
                self.add_hdf5(filepath, parent_item, update_treeview=False)
            self.update_treeview()
            return
        # If dealing with a single HDF5 file
        else:
            filepath = filepaths

        # If the HDF5 file we are working on is empty
        if len(self.wrp.get_children_elements()) == 0:
            self.open_hdf5(filepath)

        # If the opened file is not empty, we ask the user what to do (update wrapper or add files to opened one)
        else:
            # We start by asking the user what to do: close the current file and open the dropped file or add the data to the opened file
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Question)
            dialog.setWindowTitle('Precisions')
            dialog.setText('Do you want to add the data to the opened file or create a new one?')
            dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            buttonY = dialog.button(QMessageBox.Yes)
            buttonY.setText('Add to current file')
            buttonN = dialog.button(QMessageBox.No)
            buttonN.setText('Close current file and open dropped file')
            dialog.exec_()
            
            # The user wants to add the data to the opened file
            if dialog.clickedButton() == buttonY: 
                try:
                    self.wrp.add_hdf5(filepath = filepath, parent_group = parent_item.data(Qt.UserRole))
                except Exception as e:
                    QMessageBox.warning("Error", e)

            # The user wants to create a new file
            elif dialog.clickedButton() == buttonN: 
                # Try to close the current file. If the file hasn't been saved, an error is raised and handled
                try: 
                    self.wrp.close()
                except WrapperError_Save:
                    if not self.handle_error_save(): return 
                    
                # If the user dropped only one file, then we open it meaning we update the wrapper to this file
                self.open_hdf5(filepath = filepath)

            if update_treeview: self.update_treeview()
        
        self.buttons['add'].setEnabled(True)
        self.buttons['remove'].setEnabled(True)
        self.buttons['export_code'].setEnabled(True)
        self.buttons['csv'].setEnabled(True)

        self.treeview.setCurrentIndex(self.architecture_file_model.index(0, 0))
        self.treeview.expand(self.architecture_file_model.index(0, 0))

    def merge_sub_datasets(self):
        """Merge all the sub-datasets of the selected group.
        """
        QMessageBox.information(self, "Not implemented", "To do")

    def remove_element(self):
        """Remove the selected element from the HDF5 file.
        """
        if self.treeview.currentIndex().data(Qt.UserRole) == "Brillouin":
            QMessageBox.warning(self, "Warning", "You can't remove the root element")
            return
        
        # Get the item corresponding to the selected element in the treeview
        item = self.architecture_file_model.itemFromIndex(self.treeview.currentIndex())

        # Warn the user that the action cannot be undone
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle('Warning')
        dialog.setText('Are you sure you want to remove the element <b>"'+item.text()+'"</b> from the HDF5 file?')
        dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        buttonY = dialog.button(QMessageBox.Yes)
        buttonY.setText('Remove element')
        dialog.exec_()
        
        # If the user confirms the action, we remove the element
        if dialog.clickedButton() == buttonY:
            self.wrp.delete_element(path = self.treeview.currentIndex().data(Qt.UserRole))

            # Get the index of the parent item in the treeview
            parent_index = self.architecture_file_model.indexFromItem(item.parent())

            # Delete the item from the treeview
            item.parent().removeRow(item.row())

            # Select the parent item in the treeview
            self.treeview.setCurrentIndex(parent_index)
            # self.treeview.currentIndex().data(Qt.UserRole) = parent_index.data(Qt.UserRole)

    # Data processing

    def get_PSD(self):
        """Get the PSD from the selected element.
        """
        def extract_data(parent_group, types):
            """Extract the raw data from the selected group.
            """
            temp = []
            if self.wrp.get_type(path=parent_group) == HDF5_group:
                for elt in self.wrp.get_children_elements(path=parent_group):
                    temp += extract_data(f"{parent_group}/{elt}", types)
                return temp
            else:
                if self.wrp.get_type(path=parent_group, return_Brillouin_type=True) in types:
                    return [parent_group]
                else:
                    up_group = "/".join(parent_group.split("/")[:-1])
                    for elt in self.wrp.get_children_elements(path=up_group):
                        if self.wrp.get_type(path=f"{up_group}/{elt}", return_Brillouin_type=True) in types:
                            return [f"{up_group}/{elt}"]
                    return []

        # Get the paths to all selected items in the treeview
        selected_indexes = self.treeview.selectionModel().selectedIndexes()
        paths = [index.data(Qt.UserRole) for index in selected_indexes if index.data(Qt.UserRole) is not None]

        # Get the spectrometer type
        spectrometer_type = None
        for path in paths:
            if "SPECTROMETER.Type" in self.wrp.get_attributes(path=path).keys(): 
                if spectrometer_type is None: 
                    spectrometer_type = self.wrp.get_attributes(path=path)["SPECTROMETER.Type"]
                elif self.wrp.get_attributes(path=path)["SPECTROMETER.Type"] != spectrometer_type:
                    spectrometer_type = False

        if spectrometer_type is False:
            QMessageBox. warning(self, "Different spectrometers", "It seems you have selected data obtained with different spectrometers. Please treat these data separately.")
            return
        if spectrometer_type in ["VIPA", "VIPA streak"]:
            processing = Analyse_VIPA
        else:
            QMessageBox. information(self, "Not implemented", "The type of spectrometer indicated is not implemented.")
            return

        # Get the datasets to consider for the extraction of the PSD
        types, _ = MessageBoxMultipleChoice.get_choice(text = "Please choose the Brillouin types of the dataset to consider for processing.", 
                                                      list_choice = ["Raw_data, PSD", "Raw_data", "PSD"],
                                                      parent = self)
        if types is None: return

        # Get the datasets to consider for the extraction of the PSD
        types = list(types.split(", "))
        elements = []
        for path in paths:
            elements += extract_data(path, types)

        # Open the second GUI window for processing the data
        data_process, elements = DataProcessingWindow_Analyse.get_results_PSD(self.wrp, elements, processing, parent=self)
        if data_process is None:return
    
        # Get the frequency array and algorithm from the data_process object
        frequency = data_process.x
        algorithm = data_process.silent_return_string_algorithm()

        # Add frequency and algorithm to the selected elements
        for path, index, element in zip(paths, selected_indexes, elements):
            self.wrp.add_frequency(frequency, parent_group=path, name="Frequency", overwrite=True)
            self.wrp.add_attributes({"Process_PSD": algorithm}, parent_group=path, overwrite=True)
            self.wrp.change_brillouin_type(path=element, brillouin_type="PSD")

        # Get the row and column of the last element and expand the treeview to it
        self.update_treeview()
        item = self.get_item_from_path(path)
        self.treeview.setCurrentIndex(self.architecture_file_model.indexFromItem(item))
        self.treeview.expand(self.architecture_file_model.indexFromItem(item))
        self.update_properties()

    def get_results(self):
        """Applies the treatment to the selected element
        """
        def extract_data(parent_group, types):
            """Extract the raw data from the selected group.
            """
            temp = []
            if self.wrp.get_type(path=parent_group) == HDF5_group:
                for elt in self.wrp.get_children_elements(path=parent_group):
                    temp += extract_data(f"{parent_group}/{elt}", types)
                return temp
            else:
                if self.wrp.get_type(path=parent_group, return_Brillouin_type=True) in types:
                    return [parent_group]
                else:
                    up_group = "/".join(parent_group.split("/")[:-1])
                    for elt in self.wrp.get_children_elements(path=up_group):
                        if self.wrp.get_type(path=f"{up_group}/{elt}", return_Brillouin_type=True) in types:
                            return [f"{up_group}/{elt}"]
                    return []

        # Get the paths to all selected items in the treeview
        selected_indexes = self.treeview.selectionModel().selectedIndexes()
        paths = [index.data(Qt.UserRole) for index in selected_indexes if index.data(Qt.UserRole) is not None]

        # Limit treatment to only one PSD at a time
        if len(paths) > 1:
            QMessageBox.warning(self, "More than one treatment", "It seems you have selected multiple datasets for the treatment. Currently only one dataset can be treated at a time.")
            return
        path = paths[0]

        # Check if there is a PSD in the group (or group of the element) selected
        if self.wrp.get_type(path = path) == HDF5_dataset:
            path = "/".join(path.split("/")[-1])
        psd, freq = '', ''
        for child in self.wrp.get_children_elements(path = path):
            if self.wrp.get_type(path = f"{path}/{child}", return_Brillouin_type = True) == "Frequency":
                freq = f"{path}/{child}"
            elif self.wrp.get_type(path = f"{path}/{child}", return_Brillouin_type = True) == "PSD":
                psd = f"{path}/{child}"
        if len(psd)*len(freq) == 0:
            QMessageBox.warning(self, "No PSD or Frequency array", "It seems there either is no PSD to use or no Frequency array associated to it.")
            return

        # Open the second GUI window for processing the data
        data_process, elements = DataProcessingWindow_Treat.get_results_Treat(self.wrp, psd, freq, parent=self)
        if data_process is None:return

        print(data_process.shift)
    
        # # Get the frequency array and algorithm from the data_process object
        # frequency = data_process.x
        # algorithm = data_process.silent_return_string_algorithm()

        # # Add frequency and algorithm to the selected elements
        # for path, index, element in zip(paths, selected_indexes, elements):
        #     self.wrp.add_frequency(frequency, parent_group=path, name="Frequency", overwrite=True)
        #     self.wrp.add_attributes({"Process_PSD": algorithm}, parent_group=path, overwrite=True)
        #     self.wrp.change_brillouin_type(path=element, brillouin_type="PSD")

        # # Get the row and column of the last element and expand the treeview to it
        # self.update_treeview()
        # item = self.get_item_from_path(path)
        # self.treeview.setCurrentIndex(self.architecture_file_model.indexFromItem(item))
        # self.treeview.expand(self.architecture_file_model.indexFromItem(item))
        # self.update_properties()

    # Context menus

    def treeview_context_menu(self, position: QPoint):
        """ Show the context menu when right-clicking on an element in the tree view.

        Parameters
        ----------
        position : QPoint
            The position where the context menu should be displayed.
        """
        def add_action_general(menu, menu_actions, associated_action):
            """General actions common to all elements of an HDF5 file.

            Parameters
            ----------
            menu : QMenu
                The main context menu
            menu_actions : dic
                Dictionnary of actions to add to the menu
            associated_action : dic
                Dictionnary of associated functions to the actions
            """
            menu_actions["export_path"] = menu.addAction("Copy path to clipboard")
            associated_action["export_path"] = self.export_path_clipboard

            menu_actions["import"] = menu.addAction("Import element")
            associated_action["import"] = self.add_data
            
        def add_action_groups(menu, menu_actions, associated_action):
            """Actions specific to groups.

            Parameters
            ----------
            menu : QMenu
                The main context menu
            menu_actions : dic
                Dictionnary of actions to add to the menu
            associated_action : dic
                Dictionnary of associated functions to the actions
            """
            def sub_menu_Brillouin_type_group():
                """Actions to change the Brillouin type of a group.

                Parameters
                ----------
                menu : QMenu
                    The main context menu
                menu_actions : dic
                    Dictionnary of actions to add to the menu
                associated_action : dic
                    Dictionnary of associated functions to the actions
                """
                def apply_change(value):
                    self.wrp.change_brillouin_type(path=self.treeview.currentIndex().data(Qt.UserRole), brillouin_type=value)
                    self.set_icon_brillouin_type(self.architecture_file_model.itemFromIndex(self.treeview.currentIndex()), value)

                # Clear the menu
                menu_actions["edit_type_group"].clear()

                # Add actions for each group type
                for tpe in self.wrp.BRILLOUIN_TYPES_GROUPS:
                    menu_actions[f"edit_type_group_{tpe}"] = QAction(tpe.replace("_", " "), self)
                    menu_actions[f"edit_type_group_{tpe}"].triggered.connect(partial(apply_change, value=tpe))
                    menu_actions["edit_type_group"].addAction(menu_actions[f"edit_type_group_{tpe}"])
                
            def add_action_group_root(menu, menu_actions, associated_action):
                """Actions specific to root groups

                Parameters
                ----------
                menu : QMeny
                    Main menu of the context menu
                menu_actions : dic
                    Dictionnary of actions to add to the menu
                associated_action : dic
                    Dictionnary of associated functions to the actions
                """
                menu_actions["add_group"] = menu.addAction("New sub-group")
                associated_action["add_group"] = self.add_group
                menu_actions["merge_sub_datasets"] = menu.addAction("Merge all sub-datasets of the group")
                associated_action["merge_sub_datasets"] = self.merge_sub_datasets

            def add_action_group_measure(menu, menu_actions, associated_action):
                """Actions specific to measure, calibration_spectrum and impulse_response groups

                Parameters
                ----------
                menu : QMenu
                    The main context menu
                menu_actions : dic
                    Dictionnary of actions to add to the menu
                associated_action : dic
                    Dictionnary of associated functions to the actions
                """
                list_children = self.wrp.get_children_elements(path=self.treeview.currentIndex().data(Qt.UserRole), Brillouin_type="PSD")
                if len(list_children) == 1:
                    elt = list_children[0]
                    if len(self.wrp[f"{self.treeview.currentIndex().data(Qt.UserRole)}/{elt}"].shape) in [3, 4]:
                        menu_actions["export_brim"] = menu.addAction("Export group as a brim file")
                        associated_action["export_brim"] = self.export_brim

            menu_actions["edit_type_group"] = menu.addMenu("Edit Type")
            menu_actions["edit_type_group"].aboutToShow.connect(sub_menu_Brillouin_type_group)
            menu.addSeparator()
            menu_actions["export_group"] = menu.addAction("Export group as a HDF5 file")
            associated_action["export_group"] = self.export_HDF5_group
            menu.addSeparator()
            menu_actions["get_PSD"] = menu.addAction("Get PSD")
            associated_action["get_PSD"] = self.get_PSD
            menu_actions["get_results"] = menu.addAction("Get Results")
            associated_action["get_results"] = self.get_results
            menu.addSeparator()

            # Add actions in function of the Brillouin type of the selected item
            if self.wrp.get_type(path=self.treeview.currentIndex().data(Qt.UserRole), return_Brillouin_type=True) == "Root":
                add_action_group_root(menu, menu_actions, associated_action)
            elif self.wrp.get_type(path=self.treeview.currentIndex().data(Qt.UserRole), return_Brillouin_type=True) in ["Calibration_spectrum", "Impulse_response", "Measure"]:
                add_action_group_measure(menu, menu_actions, associated_action)

        def add_action_datasets(menu, menu_actions, associated_action):
            def sub_menu_Brillouin_type_dataset():
                def apply_change(value):
                    self.wrp.change_brillouin_type(path=self.treeview.currentIndex().data(Qt.UserRole), brillouin_type=value)
                    self.set_icon_brillouin_type(self.architecture_file_model.itemFromIndex(self.treeview.currentIndex()), value)

                menu_actions["edit_type_dataset"].clear()

                for tpe in self.wrp.BRILLOUIN_TYPES_DATASETS:
                    menu_actions[f"edit_type_dataset_{tpe}"] = QAction(tpe.replace("_", " "), self)
                    menu_actions[f"edit_type_dataset_{tpe}"].triggered.connect(partial(apply_change, value=tpe))
                    menu_actions["edit_type_dataset"].addAction(menu_actions[f"edit_type_dataset_{tpe}"])

            def sub_menu_export_dataset():
                # Clear the menu
                menu_actions["export_dataset"].clear()

                # Export the dataset as a numpy array
                menu_actions["export_numpy_array"] = QAction("Export dataset as a numpy array", self)
                menu_actions["export_numpy_array"].triggered.connect(self.export_numpy_array)
                menu_actions["export_dataset"].addAction(menu_actions["export_numpy_array"])
                
                # If the dataset can be exported as an image, allow the user to do so
                shape = [s for s in self.wrp[self.treeview.currentIndex().data(Qt.UserRole)].shape if s > 1]
                if len(shape) == 2:
                    menu_actions["export_image"] = QAction("Export dataset as an image", self)
                    menu_actions["export_image"].triggered.connect(self.export_numpy_array)
                    menu_actions["export_dataset"].addAction(menu_actions["export_image"])

            def add_actions_dataset_PSD(menu, menu_actions, associated_action):
                menu.addSeparator()
                menu_actions["get_PSD"] = menu.addAction("Get PSD")
                associated_action["get_PSD"] = self.get_PSD
                menu.addSeparator()

            menu_actions["edit_type_dataset"] = menu.addMenu("Edit Type")
            menu_actions["edit_type_dataset"].aboutToShow.connect(sub_menu_Brillouin_type_dataset)
            menu_actions["export_dataset"] = menu.addMenu("Export dataset")
            menu_actions["export_dataset"].aboutToShow.connect(sub_menu_export_dataset)
            if self.wrp.get_type(path=self.treeview.currentIndex().data(Qt.UserRole), return_Brillouin_type=True) in ["Frequency","Raw_data", "PSD"]:
                add_actions_dataset_PSD(menu, menu_actions, associated_action)

        indexes = self.treeview.selectedIndexes()

        # If there is a selected element
        if indexes:
            # Initialize the menu
            menu = QMenu()
            menu_actions = {}
            associated_action = {}

            # Starts by adding actions common to all elements
            add_action_general(menu, menu_actions, associated_action)
            menu.addSeparator()

            # Add actions in function of the type of the selected item (group or dataset)
            if self.wrp.get_type(path=self.treeview.currentIndex().data(Qt.UserRole)) == HDF5_group:
                add_action_groups(menu, menu_actions, associated_action)

            elif self.wrp.get_type(path=self.treeview.currentIndex().data(Qt.UserRole)) == HDF5_dataset:
                add_action_datasets(menu, menu_actions, associated_action)

            # Execute the menu
            action = menu.exec_(self.treeview.viewport().mapToGlobal(position))
            for act in menu_actions.keys():
                if action == menu_actions[act] and act in associated_action.keys():
                    associated_action[act]()

    # Export methods

    def export_brim(self):
        """Export the selected group as a brim file.
        """
        QMessageBox.information(self, "Not implemented", "To do")

    def export_HDF5_group(self):
        """Export the selected group as a HDF5 file.
        """
        QMessageBox.information(self, "Not implemented", "To do")
    
    def export_image(self):
        """Export the selected dataset as an image.
        """ 
        QMessageBox.information(self, "Not implemented", "To do")

    def export_path_clipboard(self):
        """Copy the path of the selected element to the clipboard.
        """
        pyperclip.copy(self.treeview.currentIndex().data(Qt.UserRole))
        QMessageBox.information(self, "Copied to clipboard", f"The following path to the data has been copied to the clipboard: {self.treeview.currentIndex().data(Qt.UserRole)}")

    def export_numpy_array(self):
        """Export the selected dataset as a numpy array.
        """ 
        QMessageBox.information(self, "Not implemented", "To do")

    # Interactions with properties frame and tableview

    @Slot()
    def properties_dragEnterEvent(self, event: QDragEnterEvent):
        """Handle the drag enter event for the table view.

        Parameters
        ----------
        event : QDragEnterEvent
            The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore() 

    @Slot()
    def properties_dragMoveEvent(self, event: QDragEnterEvent):
        """Handle the drag enter event for the table view.

        Parameters
        ----------
        event : QDragEnterEvent
            The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @Slot()
    def properties_dropEvent(self, event: QDropEvent):
        """Updates the parameters of the selected element when a .csv file is dropped on the table view.

        Parameters
        ----------
        event : QDropEvent
            The drop event.
        """
        if event.mimeData().hasUrls():
            urls = [url.toLocalFile() for url in event.mimeData().urls()]
            # Check if the user is trying to drop multiple files, if so raise a warning
            if len(urls) > 1: 
                QMessageBox.warning(self, "Warning", "Only one property file can be dropped at a time")
            elif len(urls) == 1:
                url = urls[0]
                # Check if the file is a spreadsheet
                if url.split(".")[-1] in self.config["DragDrop"]["properties_extensions"].split(","):
                    if len(self.wrp.get_children_elements(self.treeview.currentIndex().data(Qt.UserRole)))>1:
                        response = QMessageBox.information(self, "Warning", "Do you want to update the properties of each element of the selected group or dataset?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                        if response == QMessageBox.Yes:
                            self.wrp.import_properties_data(filepath = url, path = self.treeview.currentIndex().data(Qt.UserRole), delete_child_attributes = True)
                            self.update_properties()
                        elif response == QMessageBox.Cancel:
                            return
                        else:
                            self.wrp.import_properties_data(filepath = url, parent_group = self.treeview.currentIndex().data(Qt.UserRole), delete_child_attributes = True)
                            self.update_properties()
                    else:
                        self.wrp.import_properties_data(filepath = url, 
                                                        path = self.treeview.currentIndex().data(Qt.UserRole), 
                                                        delete_child_attributes = True)
                        self.update_properties()
                else: 
                    QMessageBox.warning(self, "Warning", "Only .csv, .xlsx or .xls property files can be used")
            event.accept()
        else: 
            event.ignore()

    # Interactions with architecture frame and treeview

    def adjust_treeview_columns(self, index):
        """Resize the first column to fit its contents when a treeview item is expanded."""
        self.treeview.resizeColumnToContents(0)

    @Slot()
    def expand_on_hover(self):
        """Expand treeview items when hovered over.
        """
        if self.current_hover_index is not None:
            self.treeview.expand(self.current_hover_index)  # Expand the item

    def get_item_from_path(self, path):
        """Get the item corresponding to a path.

        Parameters
        ----------
        path : str
            The path to the item in the form "Brillouin/Group/Element".

        Returns
        -------
        QStandardItem
            The item corresponding to the path.
        """
        parent = self.architecture_file_model.itemFromIndex(self.architecture_file_model.index(0, 0))
        base_path = "Brillouin"

        for p in path.split("/")[1:]:
            # Go through the children of the parent
            for child in range(parent.rowCount()):
                # If the child has the same name as the path, return the child
                item = parent.child(child)
                if item.data(Qt.UserRole) == base_path + "/" + p:
                    parent = item
                    base_path += "/" + p
                    break
        
        return parent

    @Slot()
    def treeview_dragEnterEvent(self, event: QDragEnterEvent):
        """Handle the drag enter event for the table view.

        Parameters
        ----------
        event : QDragEnterEvent
            The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.accept()
        elif event.mimeData().hasFormat("application/x-brillouin-path"):
            event.accept()
        else:
            event.ignore()

    @Slot()
    def treeview_dragMoveEvent(self, event: QDragEnterEvent):
        """Handle the drag move event for the tree view.

        Parameters
        ----------
        event : QDragEnterEvent
            The drag move event.
        """
        if event.mimeData().hasUrls() or event.mimeData().hasText() or event.mimeData().hasFormat("application/x-brillouin-path"):
            index = self.treeview.indexAt(event.pos())
            if index.isValid():
                # Highlight/select the item under the cursor
                self.treeview.setCurrentIndex(index)

                # Check if the item is a group (not a dataset)
                item = self.architecture_file_model.itemFromIndex(index)
                is_group = self.wrp.get_type(path=item.data(Qt.UserRole)) == HDF5_group

                # If hovering over a new item, restart the timer
                if self.current_hover_index != index:
                    self.hover_timer.stop()
                    self.current_hover_index = index

                    if is_group:
                        self.hover_timer.start(500)  # 0.5 seconds

                # If not a group, stop the timer
                elif not is_group:
                    self.hover_timer.stop()
                    self.current_hover_index = None

            event.accept()
        else:
            event.ignore()

    @Slot()
    def treeview_dropEvent(self, event: QDropEvent):
        """Handle the drop event for the treeview.
        """ 
        self.hover_timer.stop()
        self.current_hover_index = None

        # Get the target item and path
        parent_index = self.treeview.indexAt(event.pos()) if not self.treeview.indexAt(event.pos()).data(Qt.UserRole) is None else self.treeview.indexAt(QPoint(0,0))
        parent_item = self.architecture_file_model.itemFromIndex(parent_index) if parent_index.isValid() else self.architecture_file_model.itemFromIndex(self.treeview.rootIndex())

        # External file drop
        if event.mimeData().hasUrls():
            event.accept()
            filepaths = [url.toLocalFile() for url in event.mimeData().urls()]

            # Check that if multiple files are dropped, they are all of the same type
            for filepath in filepaths:
                if os.path.isdir(filepaths[0]):
                    if not os.path.isdir(filepath):
                        QMessageBox.warning(self, "Warning", "You cannot add files and directories at the same time.")
                        return
                elif filepath.split(".")[-1] != filepaths[0].split(".")[-1]:
                    QMessageBox.warning(self, "Warning", "Files with different extensions were selected. Please select any number of only one file type.")
                    return

            # If we are adding HDF5 files
            if filepaths[0].split(".")[-1] in ["hdf5", "h5"]:
                self.add_hdf5(filepaths, parent_item) # OK
            elif filepaths[0].split("/")[-1] == "":
                self.add_directory(filepaths, parent_item, update_treeview = True)
            else:
                self.add_data(filepaths, parent_item) # OK
            self.treeview.expand(self.treeview.currentIndex())

        # Internal tree drag-drop
        elif event.mimeData().hasFormat("application/x-brillouin-path"):
            dragged_path = str(event.mimeData().data("application/x-brillouin-path"), encoding='utf-8')
            self.wrp.move(path = dragged_path, new_path = parent_item.data(Qt.UserRole))
            # self.treeview.currentIndex().data(Qt.UserRole) = parent_item.data(Qt.UserRole)+"/"+dragged_path.split("/")[-1]
            self.update_treeview()
            self.update_properties()
            # self.expand_treeview_path(self.treeview.currentIndex().data(Qt.UserRole))
            event.accept()

        else:
            event.ignore()
    
    def treeview_element_changed(self, topLeft, bottomRight, roles):
        """Handle the event when a tree view element is changed.

        Parameters
        ----------
        topLeft : QModelIndex
            The top-left index of the changed data in the model.
        bottomRight : QModelIndex
            The bottom-right index of the changed data in the model.
        roles : list
            The roles that triggered the change.
        """
        def fill(item: QStandardItem = QStandardItem("Brillouin"), parent: str = "Brillouin"):
            """Recursive function to create the model to be displayed on the treeview.

            Parameters
            ----------
            item : QStandardItem, optional
                The parent item to which append the new items, by default an empty QStandardItem with name "Brillouin"
            parent : str, optional
                The path to the parent item in the HDF5 file, by default "Brillouin"

            Returns
            -------
            QStandardItem
                The item with all the children of the parent organized following the guidelines of the treeview.
            """
            if parent == "Brillouin": 
                item.setData("Brillouin", Qt.UserRole)
                self.set_icon_brillouin_type(item, self.wrp.get_type(path=item.data(Qt.UserRole)))

            # Go through all the children of the parent in the HDF5 file
            for elt in self.wrp.get_children_elements(path = parent):
                # Create the item with the name of the child in the HDF5 file
                loc_item = QStandardItem(elt)
                loc_item.setData(f"{parent}/{elt}", Qt.UserRole)
                self.set_icon_brillouin_type(loc_item, self.wrp.get_type(path=f"{parent}/{elt}", return_Brillouin_type=True))
                # Create a temporary list to store the items to be added to the model
                temp = [loc_item]
                # Get the attributes of the child in the HDF5 file
                attributes = self.wrp.get_attributes(path = f"{parent}/{elt}")
                # Go through the columns of the treeview and fill the model with the corresponding attributes taken from the HDF5 file
                for properties in self.config['Treeview']['columns'].split(',')[1:]:
                    if properties in attributes:
                        temp.append(QStandardItem(attributes[properties]))
                    else:
                        temp.append(QStandardItem(""))
                # Append the items to the model
                item.appendRow(temp)
                # Recursively fill the model with the children of the child
                fill(loc_item, f"{parent}/{elt}")
            return item

        # Ensure we're detecting edits, not just selection changes
        if Qt.EditRole in roles:
            column = self.config['Treeview']['columns'].split(',')[topLeft.column()]
            new_value = topLeft.data(Qt.EditRole)

            # Handle changes based on the column
            if column == "Name":  # Name column
                item = self.architecture_file_model.itemFromIndex(topLeft)
                self.wrp.change_name(path=self.treeview.currentIndex().data(Qt.UserRole), name=new_value)
                # self.treeview.currentIndex().data(Qt.UserRole) = "/".join(self.treeview.currentIndex().data(Qt.UserRole).split("/")[:-1])+"/"+new_value
                item.setText(new_value)
                item.setData(self.treeview.currentIndex().data(Qt.UserRole), Qt.UserRole)

            else:
                # If the new value is the same as the old one, we don't update the attribute
                current_attributes = self.wrp.get_attributes(path=self.treeview.currentIndex().data(Qt.UserRole))
                if column in current_attributes.keys() and current_attributes[column] == new_value: 
                    return
                
                try: 
                    self.wrp.update_property(name = column, value = new_value, path=self.treeview.currentIndex().data(Qt.UserRole))
                except WrapperError_ArgumentType as e:
                    apply_all = QMessageBox.question(self, "Apply to all sub-groups?", f"Do you want to apply this change to all the sub-elements of the selected group?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                    if apply_all == QMessageBox.Yes:
                        self.wrp.update_property(name = column, value = new_value, path=self.treeview.currentIndex().data(Qt.UserRole), apply_to_all = True)
                    elif apply_all == QMessageBox.Cancel:
                        return
                    else:
                        self.wrp.update_property(name = column, value = new_value, path=self.treeview.currentIndex().data(Qt.UserRole), apply_to_all = False)
                # Update column of selected item
                parent_index_col0 = topLeft.sibling(topLeft.row(), 0) 
                item = self.architecture_file_model.itemFromIndex(parent_index_col0)
                self.architecture_file_model.itemFromIndex(topLeft).setText(new_value)

                # Remove all the children of the selected element
                item.removeRows(0, item.rowCount())

                # Fill all the children of the selected element
                fill(item, self.treeview.currentIndex().data(Qt.UserRole))
            
            self.update_properties()

    @Slot()
    def treeview_element_selected(self, event: QItemSelection):
        """Handle the event when a treeview element is selected.
        Updates the "treeview_selected" attribute and the "treeview_selected_multiple" attribute (if multiple elements are selected).
        Updates the property frame associated to the selected element.
        Activates the "Export code" button if the selected element is a dataset.
        """
        # Get the selected indexes
        selected_indexes = self.treeview.selectionModel().selectedIndexes()

        if selected_indexes:
            # Get the first selected index (assuming single selection) and update the treeview_selected attribute
            # self.treeview.currentIndex().data(Qt.UserRole) = selected_indexes[0].data(Qt.UserRole)

            # Update the properties frame
            self.update_properties()

            # Enable the "Export code" button if the selected element is a dataset
            if self.wrp.get_type(path=self.treeview.currentIndex().data(Qt.UserRole)) == HDF5_dataset:
                self.buttons['export_code'].setEnabled(False)
            else:
                self.buttons['export_code'].setEnabled(True)