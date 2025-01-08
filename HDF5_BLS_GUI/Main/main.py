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

    wraper = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
    
        # Set the buttons to functions
        self.set_buttons()

        # Set the menu to functions
        self.set_menu()

        # Initiates the table view
        self.initialize_table_view()

    @qtc.Slot()
    def activate_buttons(self):
        if self.wraper is not None:
            self.b_AddData.setEnabled(True)
            if len(list(self.wraper.data.keys())) > 0:
                self.b_RemoveData.setEnabled(True)
                self.b_Save.setEnabled(True)
                self.b_ConvertCSV.setEnabled(True)

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
        self.wraper = wrapper.Wrapper()

        # Update treeview
        self.update_treeview()
    
    def open_hdf5(self):
        filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
        self.wraper = wrapper.load_hdf5_file(filepath)
        
        # Update treeview
        self.update_treeview()
    
    def save_hdf5(self):
        filepath = qtw.QFileDialog.getSaveFileName(self, "Save File", "", "HDF5 Files (*.h5)")[0]
        self.wraper.save_hdf5_file(filepath)
    
    def add_data(self, event = None, filepath = None):
        if filepath is None:
            filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")[0]
        self.wraper.add_data_to_wraper(filepath)
    
    def remove_data(self):
        self.wraper.remove_data_from_wraper()

    def convert_csv(self):
        filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "CSV Files (*.csv)")[0]
        print(filepath)

    @qtc.Slot()
    def update_treeview(self):     
        def add_child(wrp, element, parent, path):
            item_path = f"{path}/{element}".replace("//", "/")
            if isinstance(wrp.data[element], np.ndarray) or isinstance(wrp.data[element], h5py._hl.dataset.Dataset):
                name, date, sample = "Not Specified", '', ''
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
        if "FILEPROP.Name" in self.wraper.attributes.keys(): name = self.wraper.attributes["FILEPROP.Name"]
        if "MEASURE.Sample" in self.wraper.attributes.keys(): sample = self.wraper.attributes["MEASURE.Sample"]
        if "MEASURE.Date" in self.wraper.attributes.keys(): date = self.wraper.attributes["MEASURE.Date"]
        
        root = qtg.QStandardItem(name)
        root.setData("Data", qtc.Qt.UserRole)
        for e in self.wraper.data.keys(): 
            add_child(self.wraper, e, root, "Data") 

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
    
    @qtc.Slot()
    def treeView_dragEnterEvent(self, event: qtg.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def treeView_dragMoveEvent(self, event: qtg.QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def treeView_dropEvent(self, event: qtg.QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()  # Convert the URL to a file path
                if file_path:  # Ensure the path is valid
                    self.add_data(filepath = file_path)
            event.accept()
        else:
            event.ignore()
        
    @qtc.Slot(qtc.QItemSelection, qtc.QItemSelection)
    def treeview_element_selected(self, selected, deselected):
        """
        Prints the path of the selected item in the tree view.
        """
        indexes = self.treeView.selectionModel().selectedIndexes()
        if indexes:
            selected_item = self.model.itemFromIndex(indexes[0])  # Get the first selected item
            item_path = selected_item.data(qtc.Qt.UserRole)  # Retrieve the stored path
            items = item_path.split("/")[1:]
            attributes = self.wraper.attributes
            wrap_temp = self.wraper.data
            for e in items:
                attributes.update(wrap_temp[e].attributes)
                wrap_temp = wrap_temp.data[e]
            print(f"Selected item path: {item_path}\nAttributes: {attributes}")
        
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

   