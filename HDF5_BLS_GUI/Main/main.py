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

        # Initiates the log
        self.textBrowser_Log.setText("Welcome to a new HDF5_BLS GUI session")

        # Initiates the tree view properties
        self.treeView.setAcceptDrops(True)
        self.treeView.setDragEnabled(False)  # Optional: Prevent dragging from TreeView
        self.treeView.setDragDropMode(qtw.QAbstractItemView.DropOnly)
        self.treeView.dragEnterEvent = self.treeView_dragEnterEvent
        self.treeView.dragMoveEvent = self.treeView_dragMoveEvent
        self.treeView.dropEvent = self.treeView_dropEvent

        self.treeview_selected = None

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
        
        if self.wrapper.type_path(parent_path) == wrapper.Wrapper:
            self.wrapper.add_data_group_to_wrapper_from_filepath(filepath, parent_path)
        else:
            parent_path = "/".join(parent_path.split("/")[:-1])
            self.wrapper.add_data_group_to_wrapper_from_filepath(filepath, parent_path)
        
        self.update_treeview()

        self.treeview_selected = "Data"
        self.update_parameters()

        self.expand_treeview_path(parent_path)

        # Logging the added data
        path_names = []
        if not parent_path is None:
            temp = self.wrapper
            for e in parent_path.split("/")[1:]:
                temp = temp.data[e]
                if "FILEPROP.Name" in temp.attributes:
                    path_names.append(temp.attributes["FILEPROP.Name"])
                elif "Name" in temp.data_attributes:
                    path_names.append(temp.data_attributes["Name"])
                else:
                    path_names.append(e)
        else:
            path_names.append("Root")
        path_names = "/".join(path_names)

        self.textBrowser_Log.append(f"<i>{filepath}</i> added to <b>{path_names}</b> ({parent_path})")
    
    def convert_csv(self):
        filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "CSV Files (*.csv)")[0]
        qtw.QMessageBox.information(self,
            "To Do",
            "To do",
            buttons=qtw.QMessageBox.Ok,
            defaultButton=qtw.QMessageBox.Ok,
        )

    @qtc.Slot()
    def expand_on_hover(self):
        """
        Expands the tree item under the cursor when the timer expires.
        """
        if self.current_hover_index is not None:
            self.treeView.expand(self.current_hover_index)  # Expand the item

    def expand_treeview_path(self, path):
        """
        Expand the tree view to show the given path.
        :param path: The hierarchical path (e.g., "Root/Group1/Group2").
        """
        # Start from the root item
        root_index = self.treeView.model().index(0, 0)  # Assuming the first row is the root
        current_index = root_index

        # Expand the root item
        self.treeView.setExpanded(root_index, True)

        # Traverse the path and expand
        if path is None:
            pass
        else:
            path_parts = path.split("/")
            data_temp = self.wrapper

            for part in path_parts[1:]:  # Skip the root part
                found = False
                data_temp = data_temp.data[part]
                try: 
                    name = data_temp.attributes["FILEPROP.Name"]
                    for row in range(self.treeView.model().rowCount(current_index)):
                        child_index = self.treeView.model().index(row, 0, current_index)
                        if child_index.data() == name:
                            current_index = child_index
                            self.treeView.setExpanded(current_index, True)  # Expand the parent
                            found = True
                            break
                    if not found:
                        break  # Path not found; stop further expansion
                except:
                    break  # Path not found; stop further expansion
    
    def export_code_line(self):
        self.textBrowser_Log.append(f"Path to file: <b>{self.treeview_selected}</b>")
        text = "from HDF5_BLS import wrapper\n"
        text += "import h5py as h5\n\n"
        path = self.treeview_selected.split('/')[1:]
        text += f"path = ['{"','".join(path)}']\n"
        text += f"wrp = wrapper.load_hdf5_file('your_filepath.h5') # Please indicate here the filepath of the h5 file\n"
        text += "for e in path:\n"
        text += "    wrp = wrp.data[e]\n"

        elt = self.wrapper 
        for e in path:
            elt = elt.data[e]
        print(type(elt))
        if isinstance(elt, np.ndarray):
            text += f"data = wrp[:]"

        print(text)

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

        # Update parameters with the parameters of the file
        self.treeview_selected = "Data"
        self.update_parameters()

        self.textBrowser_Log.append(f"<i>{filepath}</i> opened")
        
    def remove_data(self):
        qtw.QMessageBox.information(self,
            "To Do",
            "To do",
            buttons=qtw.QMessageBox.Ok,
            defaultButton=qtw.QMessageBox.Ok,
        )

    def save_hdf5(self):
        filepath = qtw.QFileDialog.getSaveFileName(self, "Save File", "", "HDF5 Files (*.h5)")[0]
        self.wrapper.save_as_hdf5(filepath)

    @qtc.Slot()
    def set_buttons(self):
        self.b_NewHDF5.clicked.connect(self.new_hdf5)
        self.b_OpenHDF5.clicked.connect(self.open_hdf5)
        self.b_Save.clicked.connect(self.save_hdf5)
        self.b_AddData.clicked.connect(self.add_data)
        self.b_RemoveData.clicked.connect(self.remove_data)
        self.b_ExportCodeLine.clicked.connect(self.export_code_line)
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

    @qtc.Slot()
    def treeview_element_selected(self, event: qtc.QItemSelection):
        """
        Gets the path of the selected item in the tree view.
        """
        self.b_ExportCodeLine.setEnabled(True)
        selected_indexes = self.treeView.selectionModel().selectedIndexes()
        if selected_indexes:
            # Get the first selected index (assuming single selection)
            selected_index = selected_indexes[0]
            path = selected_index.data(qtc.Qt.UserRole)
            self.textBrowser_Log.append(f"Selected item: <b>{path}</b>")
            self.treeview_selected = path
            self.update_parameters()

    @qtc.Slot()
    def update_parameters(self):
        # Update the wrapper attributes to have all the attributes of the specified version
        self.wrapper.import_properties_data(f'spreadsheets/attributes_v{wrapper.BLS_HDF5_Version}.csv', update = False)

        # Extract the attributes of the element selected
        elt = self.wrapper
        attr = elt.attributes
        if self.treeview_selected != "Data":
            path = self.treeview_selected.split("/")[1:]
            for e in path:
                if isinstance(elt.data[e], h5py._hl.group.Group) or isinstance(elt.data[e], wrapper.Wrapper):
                    elt = elt.data[e]
                    attr.update(elt.attributes)
                else:
                    if e in elt.data_attributes:
                        attr.update(elt.data_attributes[e])
                        break

        # Update the tables associated to the measure and spectrometer
        self.model_table_Measure = qtg.QStandardItemModel()
        self.model_table_Measure.setHorizontalHeaderLabels(["Parameter", "Value", "Units"])
        self.model_table_Spectrometer = qtg.QStandardItemModel()
        self.model_table_Spectrometer.setHorizontalHeaderLabels(["Parameter", "Value", "Units"])

        for k, v in attr.items():
            try:
                cat, name = k.split(".")
                name = name.split("_")
                if name[-1][0] == "(" and name[-1][-1] == ")":
                    unit = name.pop(-1)[1:-1]
                else:
                    unit = ""
                if cat == "MEASURE":
                    self.model_table_Measure.appendRow([qtg.QStandardItem(" ".join(name)), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
                elif cat == "SPECTROMETER":
                    self.model_table_Spectrometer.appendRow([qtg.QStandardItem(" ".join(name)), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
            except:
                pass
        
        self.tableView_Measure.setModel(self.model_table_Measure)    
        self.tableView_Spectrometer.setModel(self.model_table_Spectrometer)

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

        # Collapse all items for visibility
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
    def initialize_table_view(self):
        """
        Creates a model with 3 columns and sets it to the tableview.
        """        
        # Changes the names of the frames of the tab widget
        self.tabWidget.setTabText(0, "Measure")
        self.tabWidget.setTabText(1, "Spectrometer")   

        # Creates a model with 3 columns and sets it to the tableview.
        self.model_table_Measure = qtg.QStandardItemModel()
        self.model_table_Measure.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.model_table_Spectrometer = qtg.QStandardItemModel()
        self.model_table_Spectrometer.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.tableView_Measure.setModel(self.model_table_Measure)    
        self.tableView_Spectrometer.setModel(self.model_table_Spectrometer)

    @qtc.Slot()
    def table_view_dragEnterEvent(self, event: qtg.QDragEnterEvent):
        """
        Handles drag enter events.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def table_view_dragMoveEvent(self, event: qtg.QDragMoveEvent):
        """
        Handles drag move events. Starts a timer to expand the tree item under the cursor if hovered for 0.5 seconds.
        """
        if event.mimeData().hasUrls():
            index = self.tableView_Measure.indexAt(event.pos())
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
    def table_view_dropEvent(self, event: qtg.QDropEvent):
        """
        Handles drop events. Prints the file path and the tree view element under which the file was dropped.
        """
        self.hover_timer.stop()  # Stop the timer when the drop occurs
        self.current_hover_index = None  # Reset the current hover index

        if event.mimeData().hasUrls():
            index_Measure = self.tableView_Measure.indexAt(event.pos())
            index_Spectrometer = self.tableView_Spectrometer.indexAt(event.pos())

            for url in event.mimeData().urls():
                file_path = url.toLocalFile()  # Convert URL to file path
                if file_path:
                    self.table_view_handle_drop(file_path)

            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def table_view_handle_drop(self, file_path, parent_path):
        if parent_path == "Root" and file_path.endswith(".h5"):
                self.open_hdf5(file_path)
        elif file_path.endswith(".h5"):
                self.wrapper.add_hdf5_to_wrapper(file_path, parent_path)
                self.textBrowser_Log.append(f"Data added from {file_path} to {parent_path}")
                self.update_treeview()
        else:
            self.add_data(filepath = file_path, parent_path = parent_path)

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
    def treeview_handle_drop(self, filepath, parent_path):
        if parent_path == "Root" and filepath.endswith(".h5"):
                self.open_hdf5(filepath)
        elif filepath.endswith(".h5"):
                self.wrapper.add_hdf5_to_wrapper(filepath, parent_path)

                self.update_treeview()

                 # Logging the added data
                path_names = []
                if not parent_path is None:
                    temp = self.wrapper
                    for e in parent_path.split("/")[1:]:
                        temp = temp.data[e]
                        if "FILEPROP.Name" in temp.attributes:
                            path_names.append(temp.attributes["FILEPROP.Name"])
                        elif "Name" in temp.data_attributes:
                            path_names.append(temp.data_attributes["Name"])
                        else:
                            path_names.append(e)
                else:
                    path_names.append("Root")
                path_names = "/".join(path_names)

                self.textBrowser_Log.append(f"<i>{filepath}</i> added to <b>{path_names}</b> ({parent_path})")
        else:
            self.add_data(filepath = filepath, parent_path = parent_path)