import sys
import os
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import numpy as np
import h5py
import pyperclip

from Main.UI.main_window_ui import Ui_w_Main

from HDF5_BLS import wrapper, load_data

class MainWindow(qtw.QMainWindow, Ui_w_Main):
    """Main window class for the HDF5_BLS GUI application.
    This class handles the main window of the application, including the setup of UI elements,
    event handling, and interaction with the HDF5 wrapper.

    Attributes
        wrapper : wrapper.Wrapper or None
            The HDF5 wrapper object used to manage HDF5 files.
        hover_timer : qtc.QTimer
            Timer to measure the time spent when dragging an item into the table.
        current_hover_index : QModelIndex or None
            Index of the current item being hovered over in the tree view.
        treeview_selected : str or None
            Path of the currently selected item in the tree view.
        filepath : str or None
            Path to the currently opened HDF5 file.

    Methods
        activate_buttons()
            Method to activate buttons based on the current state of the application.
        add_data(event=None, filepath=None, parent_path=None)
            Method to add data to the current HDF5 file.
        convert_csv()  
            Method to convert a CSV file to the HDF5 format.
        expand_on_hover()
            Method to expand tree view items when hovered over.
        expand_treeview_path(path)
            Method to expand the tree view to a specific path.
        export_code_line()
            Method to export the selected code line.
        new_hdf5()
            Method to create a new HDF5 file.
        open_hdf5(filepath=None)
            Method to open an HDF5 file and update the tree view and parameters.
        remove_data()
            Method to remove data from the current HDF5 file.
        save_hdf5(saveas=False)
            Method to save the current data to an HDF5 file.
        set_buttons()
            Method to connect buttons to their respective functions.
        set_menu()
            Method to set up the menu for the application.
        treeview_element_selected(event)
            Method to handle the event when a tree view element is selected.
        update_parameters(filepath=None)
            Method to update the parameters based on the selected tree view element.
        update_treeview()
            Method to update the tree view with the current data.
        initialize_table_view()
            Method to initialize the table view with the necessary settings.
        table_view_dragEnterEvent(event)
            Method to handle the drag enter event for the table view.
        table_view_dragMoveEvent(event)
            Method to handle the drag move event for the table view.
        table_view_dropEvent(event)
            Method to handle the drop event for the table view.
        table_view_handle_drop(file_path)
            Method to handle the drop action for the table view.
        treeView_dragEnterEvent(event)
            Method to handle the drag enter event for the tree view.
        treeView_dragMoveEvent(event)
            Method to handle the drag move event for the tree view.
        treeView_dropEvent(event)
            Method to handle the drop event for the tree view.
        treeview_handle_drop(filepath, parent_path)
            Method to handle the drop action for the tree view.
    """

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

        # Sets the selection mode of the tree view
        self.treeView.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        self.treeView.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        self.treeView.setStyleSheet("""
            QTreeView::item:selected {
                background-color: lightblue;
                color: black;
            }
        """)

        # Sets the selection mode of the table views
        self.tableView_Measure.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        self.tableView_Measure.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        self.tableView_Spectrometer.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        self.tableView_Spectrometer.setSelectionMode(qtw.QAbstractItemView.SingleSelection)

        # Ensure models are set before connecting signals
        self.model_table_Measure = qtg.QStandardItemModel()
        self.model_table_Spectrometer = qtg.QStandardItemModel()
        self.tableView_Measure.setModel(self.model_table_Measure)
        self.tableView_Spectrometer.setModel(self.model_table_Spectrometer)

        # Connect signals to the slot
        self.tableView_Measure.selectionModel().selectionChanged.connect(self.update_parameters_from_table_view)
        self.tableView_Spectrometer.selectionModel().selectionChanged.connect(self.update_parameters_from_table_view)
        self.model_table_Measure.itemChanged.connect(self.update_parameters_from_table_view)
        self.model_table_Spectrometer.itemChanged.connect(self.update_parameters_from_table_view)

        self.treeview_selected = None
        self.filepath = None
        self.file_changed = False

    @qtc.Slot()
    def activate_buttons(self):
        """
        Activate buttons based on the current state of the application.

        Returns
        -------
        None
        """
        if self.wrapper is not None:
            self.b_AddData.setEnabled(True)
            if len(list(self.wrapper.data.keys())) > 0:
                self.b_RemoveData.setEnabled(True)
                self.b_Save.setEnabled(True)
                self.b_ConvertCSV.setEnabled(True)

    def add_data(self, event=None, filepath=None, parent_path=None):
        """
        Add data to the current HDF5 file.

        Parameters
        ----------
        event : qtc.QEvent, optional
            The event that triggered the function call. Default is None.
        filepath : str, optional
            The path to the file to add. If None, a file dialog will open to select a file. Default is None.
        parent_path : str, optional
            The parent path of the added data. If None, the data will be added to the root of the HDF5 file. Default is None.
        
        Returns
        -------
        None
        """
        if filepath is None:
            filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")[0]

        if filepath is None:
            return

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
        self.file_changed = True
    
    def close_plus(self):
        """
        Close the window and exit the application.

        Returns
        -------
        None
        """
        if self.file_changed:
            reply = qtw.QMessageBox.question(self, "Unsaved changes", "Do you want to save the changes?", qtw.QMessageBox.Yes | qtw.QMessageBox.No)
            if reply == qtw.QMessageBox.Yes:
                self.save_hdf5()
        self.close()

    def convert_csv(self):
        """
        Convert a CSV file to the HDF5 format.

        Returns
        -------
        None
        """
        if not self.treeview_selected is None:
            filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "CSV Files (*.csv)")[0]
            path = self.treeview_selected.split('/')[1:]
            elt = self.wrapper
            attributes = self.wrapper.attributes
            for e in path: 
                elt = elt.data[e]
                attributes.update(elt.attributes)
            wrp_temp = wrapper.Wrapper(attributes)
            wrp_temp.export_properties_csv(filepath)

    @qtc.Slot()
    def expand_on_hover(self):
        """
        Expand tree view items when hovered over.

        Returns
        -------
        None
        """
        if self.current_hover_index is not None:
            self.treeView.expand(self.current_hover_index)  # Expand the item

    def expand_treeview_path(self, path):
        """
        Expand the tree view to a specific path.

        Parameters
        ----------
        path : str
            The path to expand in the tree view.

        Returns
        -------
        None
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
        """
        Export the selected code line to a Python script that can be used to access the data.

        Returns
        -------
        None
        """
        self.textBrowser_Log.append(f"Path to file: <b>{self.treeview_selected}</b>")
        text = "from HDF5_BLS import wrapper\n"
        text += "import h5py as h5\n\n"
        path = self.treeview_selected.split('/')[1:]
        text += f"path = ['{"','".join(path)}']\n"
        if self.filepath is None:
            text += f"wrp = wrapper.load_hdf5_file('your_filepath.h5') # Please indicate here the filepath of the h5 file\n"
        else:
            text += f"wrp = wrapper.load_hdf5_file('{self.filepath}')\n"
        text += "for e in path: wrp = wrp.data[e]\n"

        elt = self.wrapper 
        for e in path:
            elt = elt.data[e]
        if isinstance(elt, np.ndarray):
            text += f"data = wrp[:] # This is the data of the selected element"
        else:
            text += f"group = wrp # This is the selected element"

        pyperclip.copy(text)

        qtw.QMessageBox.information(self, "Copied to clipboard", f"Code to access the data copied to clipboard")

    def new_hdf5(self):
        """
        Create a new HDF5 file.

        Returns
        -------
        None
        """
        if self.file_changed:
            reply = qtw.QMessageBox.question(self, "Unsaved changes", "Do you want to save the changes?", qtw.QMessageBox.Yes | qtw.QMessageBox.No)
            if reply == qtw.QMessageBox.Yes:
                self.save_hdf5()
            
        self.wrapper.clear()
        self.filepath = None
        self.file_changed = False

        # Update treeview
        self.update_treeview()
    
    def open_hdf5(self, filepath=None):
        """
        Open an HDF5 file and update the tree view and parameters.

        Parameters
        ----------
        filepath : str, optional
            The path to the HDF5 file. If None, a file dialog will open to select a file.

        Returns
        -------
        None
        """
        if self.file_changed:
            reply = qtw.QMessageBox.question(self, "Unsaved changes", "Do you want to save the changes?", qtw.QMessageBox.Yes | qtw.QMessageBox.No)
            if reply == qtw.QMessageBox.Yes:
                self.save_hdf5()
            
            
        if filepath is None:
            self.filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
        else:
            self.filepath = filepath
        self.wrapper = wrapper.load_hdf5_file(self.filepath)
        
        # Update treeview
        self.update_treeview()

        # Update parameters with the parameters of the file
        self.treeview_selected = "Data"
        self.update_parameters()

        self.textBrowser_Log.append(f"<i>{self.filepath}</i> opened")
        self.filepath = self.filepath
        self.file_changed = False
    
    def read_table_view(self, table_view):
        """
        Read the values from the given table view.

        Parameters
        ----------
        table_view : QTableView
            The table view to read the values from.

        Returns
        -------
        dict
            A dictionary with the parameter names as keys and their values and units as values.
        """
        model = table_view.model()
        params = {}
        for row in range(model.rowCount()):
            param_name = model.item(row, 0).text()
            param_value = model.item(row, 1).text()
            param_unit = model.item(row, 2).text()
            params[param_name] = (param_value, param_unit)
        return params

    def remove_data(self):
        qtw.QMessageBox.information(self,
            "To Do",
            "To do",
            buttons=qtw.QMessageBox.Ok,
            defaultButton=qtw.QMessageBox.Ok,
        )

    def save_hdf5(self, saveas=False):
        """
        Save the current data to an HDF5 file.

        Parameters
        ----------
        saveas : bool, optional
            If True, a file dialog will open to select a save location. Default is False.

        Returns
        -------
        None
        """
        if self.filepath is None or saveas:
            self.filepath = qtw.QFileDialog.getSaveFileName(self, "Save File", "", "HDF5 Files (*.h5)")[0]

        self.wrapper.save_as_hdf5(self.filepath)
        self.file_changed = False
        self.textBrowser_Log.append(f"<i>{self.filepath}</i> has been saved")

    @qtc.Slot()
    def set_buttons(self):
        """
        Connect buttons to their respective functions.

        Returns
        -------
        None
        """
        self.b_NewHDF5.clicked.connect(self.new_hdf5)
        self.b_OpenHDF5.clicked.connect(self.open_hdf5)
        self.b_Save.clicked.connect(self.save_hdf5)
        self.b_AddData.clicked.connect(self.add_data)
        self.b_RemoveData.clicked.connect(self.remove_data)
        self.b_ExportCodeLine.clicked.connect(self.export_code_line)
        self.b_ConvertCSV.clicked.connect(self.convert_csv)
        self.b_Close.clicked.connect(self.close_plus)
    
    @qtc.Slot()
    def set_menu(self):
        """
        Set up the menu for the application.

        Returns
        -------
        None
        """
        self.a_NewHDF5.triggered.connect(self.new_hdf5)
        self.a_OpenHDF5.triggered.connect(self.open_hdf5)
        self.a_Save.triggered.connect(self.save_hdf5)
        self.a_SaveFileAs.triggered.connect(lambda: self.save_hdf5(saveas=True))
        self.a_AddData.triggered.connect(self.add_data)
        self.a_ConvertCSV.triggered.connect(self.convert_csv)

    @qtc.Slot()
    def treeview_element_selected(self, event: qtc.QItemSelection):
        """
        Handle the event when a tree view element is selected.

        Returns
        -------
        None
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
    def update_parameters(self, filepath=None):
        """
        Update the parameters based on the selected tree view element.

        Returns
        -------
        None
        """
        # Update the wrapper attributes to have all the attributes of the specified version
        if filepath is None: 
            self.wrapper.import_properties_data(f'spreadsheets/attributes_v{wrapper.BLS_HDF5_Version}.csv', update = False)
        else:
            elt = self.wrapper
            if self.treeview_selected != "Data":
                path = self.treeview_selected.split("/")[1:]
                for e in path[:-1]: 
                    elt = elt.data[e]
                update = qtw.QMessageBox.question(self, "Update properties", "Do you want to update the properties of the wrapper with the properties stored in the file?")
                if update == qtw.QMessageBox.Yes:
                    if isinstance(elt.data[path[-1]], h5py._hl.group.Group) or isinstance(elt.data[path[-1]], wrapper.Wrapper): 
                        elt.data[path[-1]].import_properties_data(filepath, update = True)
                    else:
                        elt.import_properties_data_attributes(path[-1], filepath, update = True)
                else:
                    if isinstance(elt.data[path[-1]], h5py._hl.group.Group) or isinstance(elt.data[path[-1]], wrapper.Wrapper): 
                        elt.data[path[-1]].import_properties_data(filepath, update = False)
                    else:
                        elt.import_properties_data_attributes(path[-1], filepath, update = False)
            else: 
                update = qtw.QMessageBox.question(self, "Update properties", "Do you want to update the properties of the wrapper with the properties stored in the file?")
                if update == qtw.QMessageBox.Yes:
                    self.wrapper.import_properties_data(filepath, update = True)
                else:
                    self.wrapper.import_properties_data(filepath, update = False)
            self.file_changed = True

        # Extract the attributes of the element selected
        elt = self.wrapper
        attr = {}
        attr.update(elt.attributes)

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
        self.model_table_Measure.clear()
        self.model_table_Spectrometer.clear()

        self.model_table_Measure.setHorizontalHeaderLabels(["Parameter", "Value", "Units"])
        self.model_table_Spectrometer.setHorizontalHeaderLabels(["Parameter", "Value", "Units"])

        if "FILEPROP.Name" in attr.keys():
            name_item = qtg.QStandardItem("Name")
            font = name_item.font()
            font.setBold(True)
            name_item.setFont(font)
            self.model_table_Measure.appendRow([name_item, qtg.QStandardItem(attr["FILEPROP.Name"]), qtg.QStandardItem("")])
         
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
    def update_parameters_from_table_view(self):
        """
        Update the parameters based on the entered values in the table view.

        Returns
        -------
        None
        """
        measure_params = self.read_table_view(self.tableView_Measure)
        spectrometer_params = self.read_table_view(self.tableView_Spectrometer)

        params = {}

        for k, v in measure_params.items():
            if k!="Name":
                new_key = "MEASURE."+"_".join(k.split(" "))
                if v[1] != "" or new_key == "MEASURE.Sampling_Matrix_Size_(Nx,Ny,Nz)":
                    new_key = new_key + f"_({v[1]})"
                params[new_key] = v[0]
            else:
                params["FILEPROP.Name"] = v[0]
        
        for k, v in spectrometer_params.items():
            new_key = "SPECTROMETER."+"_".join(k.split(" "))
            if v[1] != "":
                    new_key = new_key + f"_({v[1]})"
            params[new_key] = v[0]
        
        # Select only the attributes that have been changed for the data
        elt = self.wrapper
        attr = {}
        attr.update(elt.attributes)
        data_attr = False

        if self.treeview_selected != "Data": # Start by retrieving the parameters of the data before modification
            path = self.treeview_selected.split("/")[1:]
            for e in path:
                if isinstance(elt.data[e], h5py._hl.group.Group) or isinstance(elt.data[e], wrapper.Wrapper):
                    elt = elt.data[e]
                    attr.update(elt.attributes)
                else:
                    if e in elt.data_attributes:
                        attr.update(elt.data_attributes[e])
                        data_attr = True

        params_update = {}
        for k, v in attr.items():
            if not "FILEPROP" in k or "Name" in k:
                if k != "ID":
                    try:
                        if params[k] != v:
                            params_update[k] = v
                    except KeyError:
                        print("Error with key", k)
        
        # print(params_update)
        
        # # Update the attributes of the data
        # if data_attr:
        #     elt.update_property_data(e, params_update)
        # else:
        #     elt.update_property(params_update)

    @qtc.Slot()
    def update_treeview(self):     
        """
        Update the tree view with the current data.

        Returns
        -------
        None
        """
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
                qtw.QMessageBox.warning(self, "Warning", f"Not implemented for type: {type(wrp.data[element])}")
                
        # Create a model with 3 columns
        self.model = qtg.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Sample", "Date"])
        
        # Add first item
        name, date, sample = "Root", "", ""
        if self.filepath is not None: name = os.path.basename(self.filepath)
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

        # Initiates the table view properties
        self.tableView_Measure.setAcceptDrops(True)
        self.tableView_Measure.setDragEnabled(False)  # Optional: Prevent dragging from TreeView
        self.tableView_Measure.setDragDropMode(qtw.QAbstractItemView.DropOnly)
        self.tableView_Measure.dragEnterEvent = self.table_view_dragEnterEvent
        self.tableView_Measure.dragMoveEvent = self.table_view_dragMoveEvent
        self.tableView_Measure.dropEvent = self.table_view_dropEvent

        self.tableView_Spectrometer.setAcceptDrops(True)
        self.tableView_Spectrometer.setDragEnabled(False)  # Optional: Prevent dragging from TreeView
        self.tableView_Spectrometer.setDragDropMode(qtw.QAbstractItemView.DropOnly)
        self.tableView_Spectrometer.dragEnterEvent = self.table_view_dragEnterEvent
        self.tableView_Spectrometer.dragMoveEvent = self.table_view_dragMoveEvent
        self.tableView_Spectrometer.dropEvent = self.table_view_dropEvent

    @qtc.Slot()
    def initialize_table_view(self):
        """
        Initialize the table view with the necessary settings.

        Returns
        -------
        None
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
        Handle the drag enter event for the table view.

        Parameters
        ----------
        event : QDragEnterEvent
            The drag enter event.

        Returns
        -------
        None
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def table_view_dragMoveEvent(self, event: qtg.QDragMoveEvent):
        """
        Handle the drag move event for the table view.

        Parameters
        ----------
        event : QDragMoveEvent
            The drag move event.

        Returns
        -------
        None
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def table_view_dropEvent(self, event: qtg.QDropEvent):
        """
        Handle the drop event for the table view.

        Parameters
        ----------
        event : QDropEvent
            The drop event.

        Returns
        -------
        None
        """
        if event.mimeData().hasUrls():
            urls = [url.toLocalFile() for url in event.mimeData().urls()]
            if len(urls) == 1:
                url = urls[0]
                extension = os.path.splitext(url)[1]
                if extension == ".csv":
                    self.table_view_handle_drop(url)
                else:    
                    qtw.QMessageBox.warning(self, "Warning", "Only .csv property files can be used")
            else:
                qtw.QMessageBox.warning(self, "Warning", "Only one property file can be dropped at a time")
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def table_view_handle_drop(self, file_path):
        """
        Handle the drop action for the table view.

        Parameters
        ----------
        event : QDropEvent
            The drop event.

        Returns
        -------
        None
        """
        self.update_parameters(file_path)
        self.textBrowser_Log.append(f"Properties of <b>{self.treeview_selected}</b> have been updated")

    @qtc.Slot()
    def treeView_dragEnterEvent(self, event: qtg.QDragEnterEvent):
        """
        Handle the drag enter event for the tree view.

        Parameters
        ----------
        event : QDragEnterEvent
            The drag enter event.

        Returns
        -------
        None
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def treeView_dragMoveEvent(self, event: qtg.QDragMoveEvent):
        """
        Handle the drag move event for the tree view.

        Parameters
        ----------
        event : QDragMoveEvent
            The drag move event.

        Returns
        -------
        None
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
        Handle the drop event for the tree view.

        Parameters
        ----------
        event : QDropEvent
            The drop event.

        Returns
        -------
        None
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
        """
        Handle the drop action for the tree view.

        Parameters
        ----------
        event : QDropEvent
            The drop event.

        Returns
        -------
        None
        """
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
            try:
                self.add_data(filepath = filepath, parent_path = parent_path)
            except:
                qtw.QMessageBox.warning(self, "Warning", "The file could not be added to the wrapper")