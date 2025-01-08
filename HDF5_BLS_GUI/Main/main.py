import sys
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import numpy as np
import h5py

from Main.UI.main_window_ui import Ui_w_Main

import sys
from HDF5_BLS import wrapper, load_data

class MainWindow(qtw.QMainWindow, Ui_w_Main):

    wrapper = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
    
        # Set the buttons to functions
        self.set_buttons()

        # Set the menu to functions
        self.set_menu()

        # Set up the timer to measure the time spent when dragging an item into the table
        self.hover_timer = qtc.QTimer(self) 
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.expand_on_hover)  # Connect to the expand function
        self.current_hover_index = None  # Track the current item being hovered over

        # Initiates the table view
        self.initialize_table_view()

        # Initiates the tree view properties
        self.treeView.setAcceptDrops(True)
        self.treeView.setDragEnabled(False)  # Optional: Prevent dragging from TreeView
        self.treeView.setDragDropMode(qtw.QAbstractItemView.DropOnly)
        self.treeView.dragEnterEvent = self.treeView_dragEnterEvent
        self.treeView.dragMoveEvent = self.treeView_dragMoveEvent
        self.treeView.dropEvent = self.treeView_dropEvent

    @qtc.Slot()
    def activate_buttons(self):
        if self.wrapper is not None:
            self.b_AddData.setEnabled(True)
            if len(list(self.wrapper.data.keys())) > 0:
                self.b_RemoveData.setEnabled(True)
                self.b_Save.setEnabled(True)
                self.b_ConvertCSV.setEnabled(True)

    def add_data(self, event = None, filepath = None, parent_path = None):
        if filepath is None:
            filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")[0]
        if parent_path == "Root":
            parent_path = None
            self.wrapper = wrapper.Wrapper()
        self.wrapper.add_data_group_to_wrapper_from_filepath(filepath, parent_path)
        print(self.wrapper.data.keys())
        self.update_treeview()
        # qtw.QMessageBox.information( self,
        #     "To Do",
        #     "To do",
        #     buttons=qtw.QMessageBox.Ok,
        #     defaultButton=qtw.QMessageBox.Ok,
        # )

    def convert_csv(self):
        filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "CSV Files (*.csv)")[0]
        print(filepath)

    @qtc.Slot()
    def set_buttons(self):
        self.b_NewHDF5.clicked.connect(self.new_hdf5)
        self.b_OpenHDF5.clicked.connect(self.open_hdf5)
        self.b_Save.clicked.connect(self.save_hdf5)
        self.b_AddData.clicked.connect(self.add_data)
        self.b_RemoveData.clicked.connect(self.remove_data)
        self.b_ConvertCSV.clicked.connect(self.convert_csv)
        self.b_Close.clicked.connect(self.close)
    
    @qtc.Slot()
    def set_menu(self):
        self.a_NewHDF5.triggered.connect(self.new_hdf5)
        self.a_OpenHDF5.triggered.connect(self.open_hdf5)
        self.a_Save.triggered.connect(self.save_hdf5)
        self.a_AddData.triggered.connect(self.add_data)
        self.a_AddData.triggered.connect(self.add_data)
        self.a_ConvertCSV.triggered.connect(self.convert_csv)

    def new_hdf5(self):
        self.wrapper = wrapper.Wrapper()

        # Update treeview
        self.update_treeview()
    
    def open_hdf5(self, filepath = None):
        if filepath is None:
            filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
        self.wrapper = wrapper.load_hdf5_file(filepath)
        
        # Update treeview
        self.update_treeview()
    
    def save_hdf5(self):
        filepath = qtw.QFileDialog.getSaveFileName(self, "Save File", "", "HDF5 Files (*.h5)")[0]
        self.wrapper.save_hdf5_file(filepath)
    
    def remove_data(self):
        self.wrapper.remove_data_from_wraper()

    @qtc.Slot()
    def update_treeview(self):     
        def add_child(wrp, element, parent, path):
            item_path = f"{path}/{element}".replace("//", "/")
            if isinstance(wrp.data[element], np.ndarray) or isinstance(wrp.data[element], h5py._hl.dataset.Dataset):
                name, date, sample = element, '', ''
                if element in wrp.data_attributes.keys():
                    if "Name" in wrp.data_attributes[element].keys(): name = wrp.data_attributes[element]["Name"]
                    if "Date" in wrp.data_attributes[element].keys(): date = wrp.data_attributes[element]["Date"]
                    if "Sample" in wrp.data_attributes[element].keys(): sample = wrp.data_attributes[element]["Sample"]
                name_item = qtg.QStandardItem(name)
                name_item.setData(item_path, qtc.Qt.UserRole)
                parent.appendRow([name_item, qtg.QStandardItem(sample), qtg.QStandardItem(date)])
                
            elif isinstance(wrp.data[element], wrapper.Wrapper): 
                    wrp = wrp.data[element]

                    name, date, sample = "Data", "", ""

                    if "FILEPROP.Name" in wrp.attributes.keys(): name = wrp.attributes["FILEPROP.Name"]
                    if "MEASURE.Sample" in wrp.attributes.keys(): sample = wrp.attributes["MEASURE.Sample"]
                    if "MEASURE.Date" in wrp.attributes.keys(): date = wrp.attributes["MEASURE.Date"]

                    loc = qtg.QStandardItem(name)
                    loc.setData(item_path, qtc.Qt.UserRole)
                    for e in wrp.data.keys(): add_child(wrp, e, loc, item_path) 

                    parent.appendRow([loc, qtg.QStandardItem(sample), qtg.QStandardItem(date)])
                    
            else: 
                print(f"Not implemented for type: {type(wrp.data[element])}")

        # Create a model with 3 columns
        self.model = qtg.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Sample", "Date"])
        
        # Add first item
        name, date, sample = "Root", "", ""
        if "FILEPROP.Name" in self.wrapper.attributes.keys(): name = self.wrapper.attributes["FILEPROP.Name"]
        if "MEASURE.Sample" in self.wrapper.attributes.keys(): sample = self.wrapper.attributes["MEASURE.Sample"]
        if "MEASURE.Date" in self.wrapper.attributes.keys(): date = self.wrapper.attributes["MEASURE.Date"]
        
        root = qtg.QStandardItem(name)
        root.setData("Data", qtc.Qt.UserRole)
        for e in self.wrapper.data.keys(): 
            add_child(self.wrapper, e, root, "Data") 

        self.model.appendRow([root, qtg.QStandardItem(sample), qtg.QStandardItem(date)])

        # Set the model to the TreeView
        self.treeView.setModel(self.model)

        # Expand all items for visibility
        self.treeView.collapseAll()

        # Optional: Adjust column widths
        self.treeView.header().setStretchLastSection(False)
        self.treeView.header().setDefaultSectionSize(100)

        # Binds selected elements to the function treeview_element_selected
        self.treeView.selectionModel().selectionChanged.connect(self.treeview_element_selected)

        # Sets all dragged objects to the treeview to call self.add_data(filepath) where the filepath is the path of the dragged object
        self.treeView.setAcceptDrops(True)
        self.treeView.setDragEnabled(False)  # Optional: Prevent dragging from TreeView
        self.treeView.setDragDropMode(qtw.QAbstractItemView.DropOnly)

        # Bind drag-and-drop event handlers
        self.treeView.dragEnterEvent = self.treeView_dragEnterEvent
        self.treeView.dragMoveEvent = self.treeView_dragMoveEvent
        self.treeView.dropEvent = self.treeView_dropEvent

        # Activate buttons
        self.activate_buttons()

    @qtc.Slot(qtc.QItemSelection, qtc.QItemSelection)
    def treeview_element_selected(self, selected, deselected):
        """
        Prints the path of the selected item in the tree view.
        """
        qtw.QMessageBox.information(self,
            "To Do",
            "To do",
            buttons=qtw.QMessageBox.Ok,
            defaultButton=qtw.QMessageBox.Ok,
        )
        # indexes = self.treeView.selectionModel().selectedIndexes()
        # if indexes:
        #     selected_item = self.model.itemFromIndex(indexes[0])  # Get the first selected item
        #     item_path = selected_item.data(qtc.Qt.UserRole)  # Retrieve the stored path
        #     items = item_path.split("/")[1:]
        #     attributes = self.wrapper.attributes
        #     wrap_temp = self.wrapper.data
        #     for e in items:
        #         attributes.update(wrap_temp[e].attributes)
        #         wrap_temp = wrap_temp.data[e]
        #     print(f"Selected item path: {item_path}\nAttributes: {attributes}")
        
    @qtc.Slot()
    def initialize_table_view(self):
        """
        Creates a model with 3 columns and sets it to the tableview.
        """        
        # Changes the names of the frames of the tab widget
        self.tabWidget.setTabText(0, "Measure")
        self.tabWidget.setTabText(1, "Spectrometer")   

        # Creates a model with 3 columns and sets it to the tableview.
        self.model_table_Measure = qtg.QStandardItemModel()
        self.model_table_Measure.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        self.model_table_Spectrometer = qtg.QStandardItemModel()
        self.model_table_Spectrometer.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        self.tableView_Measure.setModel(self.model_table_Measure)    
        self.tableView_Spectrometer.setModel(self.model_table_Spectrometer)

    @qtc.Slot()
    def treeView_dragEnterEvent(self, event: qtg.QDragEnterEvent):
        """
        Handles drag enter events.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def treeView_dragMoveEvent(self, event: qtg.QDragMoveEvent):
        """
        Handles drag move events. Starts a timer to expand the tree item under the cursor if hovered for 0.5 seconds.
        """
        if event.mimeData().hasUrls():
            index = self.treeView.indexAt(event.pos())
            if index.isValid():
                if self.current_hover_index != index:  # If a new item is hovered
                    self.hover_timer.stop()  # Stop any previous timers
                    self.current_hover_index = index  # Update the current item
                    item = self.model.itemFromIndex(index)
                    if item.hasChildren():
                        self.hover_timer.start(500)  # Start a 0.5-second timer
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def expand_on_hover(self):
        """
        Expands the tree item under the cursor when the timer expires.
        """
        if self.current_hover_index is not None:
            self.treeView.expand(self.current_hover_index)  # Expand the item

    @qtc.Slot()
    def treeView_dropEvent(self, event: qtg.QDropEvent):
        """
        Handles drop events. Prints the file path and the tree view element under which the file was dropped.
        """
        self.hover_timer.stop()  # Stop the timer when the drop occurs
        self.current_hover_index = None  # Reset the current hover index

        if event.mimeData().hasUrls():
            index = self.treeView.indexAt(event.pos())
            parent_item = self.model.itemFromIndex(index) if index.isValid() else None

            for url in event.mimeData().urls():
                file_path = url.toLocalFile()  # Convert URL to file path
                if file_path:
                    parent_path = parent_item.data(qtc.Qt.UserRole) if parent_item else "Root"
                    self.treeview_handle_drop(file_path, parent_path)

            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def treeview_handle_drop(self, file_path, parent_path):
        if parent_path == "Root":
            if file_path.endswith(".h5"):
                self.open_hdf5(file_path)
            else:
                self.add_data(filepath = file_path, parent_path = parent_path)