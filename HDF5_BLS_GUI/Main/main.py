import sys
import os
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import numpy as np
import h5py
import pyperclip
import re
from inspect import getmembers, isfunction

from Main.UI.main_window_ui import Ui_w_Main
from DataStructure.main import DataStructure
from ComboboxChoose.main import ComboboxChoose
from ParameterWindow.main import ParameterWindow

current_dir = os.path.abspath(os.path.dirname(__file__))
relative_path_libs = os.path.join(current_dir, "..", "..", "..")
absolute_path_libs = os.path.abspath(relative_path_libs)
sys.path.append(absolute_path_libs)

from HDF5_BLS.load_formats.errors import LoadError_creator, LoadError_parameters
from HDF5_BLS import wrapper, load_data, conversion_PSD
import conversion_ui, treat_ui

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
        file_changed : bool
            Whether the wrapper has had changes or not since last save.
    """

    wrapper = None
    current_hover_index = None
    treeview_selected = None
    filepath = None
    file_changed = False

    def __init__(self):
        def initialize_buttons(self):
            self.b_NewHDF5.clicked.connect(self.new_hdf5)
            self.b_OpenHDF5.clicked.connect(self.open_hdf5)
            self.b_Save.clicked.connect(self.save_hdf5)
            self.b_AddData.clicked.connect(self.add_data)
            self.b_RemoveData.clicked.connect(self.remove_data)
            self.b_ExportCodeLine.clicked.connect(self.export_code_line)
            self.b_ConvertCSV.clicked.connect(self.convert_csv)
            self.b_Close.clicked.connect(self.close_plus)

        def initialize_menu(self):
            self.a_NewHDF5.triggered.connect(self.new_hdf5)
            self.a_OpenHDF5.triggered.connect(self.open_hdf5)
            self.a_Save.triggered.connect(self.save_hdf5)
            self.a_SaveFileAs.triggered.connect(lambda: self.save_hdf5(saveas=True))
            self.a_AddData.triggered.connect(self.add_data)
            self.a_ConvertCSV.triggered.connect(self.convert_csv)

        def initialize_timer(self):
            self.hover_timer = qtc.QTimer(self) 
            self.hover_timer.setSingleShot(True)
            self.hover_timer.timeout.connect(self.expand_on_hover)  # Connect to the expand function

        def initialize_tableview(self):
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

            # Connect signals to the slot
            self.model_table_Measure.itemChanged.connect(self.update_parameters_from_table_view)
            self.model_table_Spectrometer.itemChanged.connect(self.update_parameters_from_table_view)
            
            # Sets the selection mode of the table views
            self.tableView_Measure.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
            self.tableView_Measure.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
            self.tableView_Spectrometer.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
            self.tableView_Spectrometer.setSelectionMode(qtw.QAbstractItemView.SingleSelection)

        def initialize_treeview(self):
            self.treeView.setAcceptDrops(True)
            self.treeView.setDragEnabled(False)  # Optional: Prevent dragging from TreeView
            self.treeView.setDragDropMode(qtw.QAbstractItemView.DropOnly)

            # Sets the selection mode of the tree view
            self.treeView.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
            self.treeView.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
            self.treeView.setStyleSheet("""
                QTreeView::item:selected {
                    background-color: lightblue;
                    color: black;
                }
            """)

            # Sets the events of the treeview
            self.treeView.dragEnterEvent = self.treeView_dragEnterEvent
            self.treeView.dragMoveEvent = self.treeView_dragMoveEvent
            self.treeView.dropEvent = self.treeView_dropEvent

            # Set context menu policy for the tree view
            self.treeView.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
            self.treeView.customContextMenuRequested.connect(self.show_treeview_context_menu)

        super().__init__()
        self.setupUi(self)
    
        # Set the buttons to functions
        initialize_buttons(self)

        # Set the menu to functions
        initialize_menu(self)

        # Set up the timer (used to develop elements in the treeview when dragging items into it)
        initialize_timer(self)

        # Initiates the tree view properties
        initialize_treeview(self)

        # Initiates the table view where the properties of the measure and spectrometer are displayed
        initialize_tableview(self)

        self.wrapper = wrapper.Wrapper()
        self.update_treeview()

        # Initiates the log
        self.textBrowser_Log.setText("Welcome to a new HDF5_BLS GUI session")

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
        def create_group_data(group_dim, data, n_dim):
            if len(group_dim) == 0:
                return wrapper.Wrapper(data={"Raw_data": data},
                                        attributes = {"FILEPROP.Name": "Data_0"})
            elif len(group_dim) == 1:
                dic = {}
                for i in range(group_dim[0]): 
                    dic["Data_"+str(i)] = wrapper.Wrapper(data={"Raw_data": data[i]},
                                                          attributes = {"FILEPROP.Name": "Data_"+str(i)})
                return  wrapper.Wrapper(data = dic)
            else:
                dic = {}
                for i in range(group_dim[0]): 
                    dic["Data_"+str(i)] = create_group_data(group_dim[1:], data[i], n_dim+1)
                return wrapper.Wrapper(data = dic,
                                      attributes = {"FILEPROP.Name": "Dimension_"+str(n_dim)})

        # Get filepath            
        if filepath is None: filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")[0]
        if filepath is None: return

        # Create a new wrapper if the parent path is the root
        if parent_path in ["Root", "Data"]:
            parent_path = None
            self.wrapper = wrapper.Wrapper()

        # Makes sure to add the data to a group, even if it is dragged under a dataset
        if not self.wrapper.type_path(parent_path) == wrapper.Wrapper:
            parent_path = "/".join(parent_path.split("/")[:-1])


        # Creating the dictionnary with the data and the attributes and ...
        try: # First we try adding the data based on the file extension
            dic = load_data.load_general(filepath)
        except ValueError: # If it does not work, it might be that the file extension is not supported, in that case display a warning window
            qtw.QMessageBox.warning(self, "Warning", "The file extension is not supported.")
            return
        except LoadError_creator as e: # It can also be that there are different ways to load the data, in that case display a dialog box to choose the type of structure to load
            creator_list = e.creators 
            dialog = ComboboxChoose(text = "Choose the type of structure to load", list_choices = creator_list, parent = self)
            if dialog.exec_() == qtw.QDialog.Accepted:
                temp =dialog.get_selected_structure()
                try:# After choosing the type of structure, we try to load the data again by precising the structure
                    dic = load_data.load_general(filepath, creator = temp)
                except LoadError_parameters as e: # If it does not work, this means that the user needs to indicate the parameters to load the data, so we load a window to do so
                    parameters = e.parameters
                    dialog = ParameterWindow(text = f"Please indicate the value of the following parameters to load the data:",
                                             list_parameters = parameters, 
                                             parent = self,
                                             root_path=os.path.dirname(filepath))
                    if dialog.exec_() == qtw.QDialog.Accepted:
                        parameters = dialog.get_selected_structure()
                        dialog.close()
                    dic = load_data.load_general(filepath, temp, parameters)
                    # try:
                    #     dic = load_data.load_general(filepath, temp, parameters)
                    # except Exception as e:
                    #     qtw.QMessageBox.warning(self, "Error while loading the data", str(e))
                except Exception as e:
                    qtw.QMessageBox.warning(self, "Error other than parameter and creator", str(e))
            else: return # If the user cancels the dialog box, we return
        except Exception as e:
            qtw.QMessageBox.warning(self, "Error other than creator", str(e))

        # Adding the data to the wrapper
        print(dic)
        self.wrapper.add_data_dictionnary(dic, parent_group = parent_path, name = os.path.basename(filepath).split(".")[0])

        # if len(dic["Data"].shape) == 1: 
        #     self.wrapper.add_data_group_to_wrapper_from_filepath(filepath, parent_path)   
        # else:# If the dimensionality of the data is larger than 1, we ask the user how to store it 
        #     dialog = DataStructure(self, dic["Data"].shape)
        #     if dialog.exec_() == qtw.QDialog.Accepted:
        #         selected_structure = dialog.get_selected_structure()
        #         dialog.close()

        #         # Extract dimensions of the group and the arrays and split them into lists
        #         group_match = re.search(r"\(([\d+x]+)\) groups", selected_structure)
        #         group_dim = list(map(int, group_match.group(1).split('x'))) if group_match else []
                
        #         parent = self.wrapper
        #         if not parent_path is None:
        #             for e in parent_path.split("/")[1:]:
        #                 if isinstance(parent.data[e], wrapper.Wrapper): 
        #                     parent = parent.data[e]
                
        #         i0 = 0
        #         while f"Data_{i0}" in parent.data.keys(): i0 += 1

        #         parent.data[f"Data_{i0}"] = create_group_data(group_dim = group_dim[1:], data = data, n_dim = 1)
        #         name = os.path.basename(filepath).split(".")[0]
        #         parent.data[f"Data_{i0}"].attributes = {"ID": f"Data_{i0}", "FILEPROP.Name":name}
        
        self.treeview_selected = "Data"

        self.update_treeview()
        self.update_parameters()
        self.expand_treeview_path(parent_path)

        # Logging the added data
        path_names = []
        if not parent_path is None:
            temp = self.wrapper
            for e in parent_path.split("/")[1:]:
                temp = temp.data[e]
                if "FILEPROP.Name" in temp.attributes: path_names.append(temp.attributes["FILEPROP.Name"])
                else: path_names.append(e)
        else: path_names.append("Root")
        path_names = "/".join(path_names)

        self.textBrowser_Log.append(f"<i>{filepath}</i> added to <b>{path_names}</b> ({parent_path})")
        self.file_changed = True
    
    def add_group(self):
        """
        Add a group to the current HDF5 file.

        Returns
        -------
        None
        """
        if self.treeview_selected != "Data":
            path = self.treeview_selected.split("/")[1:]
            if self.wrapper.type_path(self.treeview_selected) != wrapper.Wrapper:
                path = path[:-1]
            elt = self.wrapper
            for e in path: elt = elt.data[e]
            ks = []
            for e in elt.data.keys(): 
                if "Data" in e: ks.append(e)
            elt.data["Data_" + str(len(ks))] = wrapper.Wrapper(data = {},
                                                               attributes={"FILEPROP.Name": "New group"})
        else:
            ks = []
            for e in self.wrapper.data.keys(): 
                if "Data" in e: ks.append(e)
            self.wrapper.data["Data_" + str(len(ks))] = wrapper.Wrapper(data = {}, 
                                                                        attributes={"ID": f"Data_{len(ks)}", "FILEPROP.Name": "New group"})

        self.update_treeview()
        self.expand_treeview_path(self.treeview_selected)

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
        Exports the properties of the wrapper to a CSV file.

        Returns
        -------
        None
        """
        if not self.treeview_selected is None:
            filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "CSV Files (*.csv)")[0]
            if filepath:
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
            The path to expand in the tree view, in the form of "Data/Data_i/Data_j".

        Returns
        -------
        None
        """
        # Start from the root item and expand it
        current_index = self.treeView.model().index(0, 0)  # Assuming the first row is the root
        self.treeView.setExpanded(current_index, True)

        # Traverse the path and expand
        if not path is None:
            path_parts = path.split("/")
            elt = self.wrapper

            for part in path_parts[1:]:  # Skip the root part
                elt = elt.data[part]
                name = elt.attributes["FILEPROP.Name"] if "FILEPROP.Name" in elt.attributes else part
                for row in range(self.treeView.model().rowCount(current_index)):
                    child_index = self.treeView.model().index(row, 0, current_index)
                    if child_index.data() == name:
                        current_index = child_index
                        self.treeView.setExpanded(current_index, True)  # Expand the parent
    
    def export_code_line(self):
        """
        Export the selected code line to a Python script that can be used to access the data.

        Returns
        -------
        None
        """
        text = "from HDF5_BLS import wrapper\n"
        text += "import h5py as h5\n\n"
        path = self.treeview_selected.split('/')[1:]
        joined_path = "', '".join(path)
        text += f"path = ['{joined_path}']\n" 
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

        self.textBrowser_Log.append(f"Python code to access the data of <b>{self.treeview_selected}</b> has been copied to the clipboard")

    def get_PSD(self):
        """
        Get the Power Spectrum Density of the selected data.

        Returns
        -------
        None
        """
        elt = self.wrapper
        for e in self.treeview_selected.split("/")[1:]: elt = elt.data[e]
        type = self.wrapper.get_attributes_path(self.treeview_selected)['SPECTROMETER.Type']
        type = type.replace(" ", "_")
        type = type.replace("-", "_")
            
        # Check if the conversion can be performed
        function_name = f"check_conversion_{type}"
        functions = [func for func in getmembers(conversion_PSD, isfunction)]
        not_found = True
        for (name, func) in functions:
            if name == function_name:
                if func(self.wrapper, self.treeview_selected):
                    conversion = True
                    not_found = False
                else:
                    conversion = False
                    not_found = False
        
        if not_found:
            qtw.QMessageBox.warning(self, "Warning", "The type of spectrometer is not recognized")
            return
            
        # If conversion can be performed, perform it
        if conversion:
            qtw.QMessageBox.information(self, "Not implemented", "Conversion can be performed")
        # If not, then execute the function from conversion_ui associated with the type of the data
        else:
            function_name = f"conversion_{type}"
            functions = [func for func in getmembers(conversion_ui, isfunction)]
            for (name, func) in functions:
                if name == function_name:
                    func(self, self.wrapper, self.treeview_selected)
        
        self.file_changed = True
        self.update_treeview()
        self.expand_treeview_path(self.treeview_selected)

    def new_hdf5(self):
        """
        Create a new HDF5 file.

        Returns
        -------
        None
        """
        if self.file_changed:
            reply = qtw.QMessageBox.question(self, "Unsaved changes", "Do you want to save the changes?", qtw.QMessageBox.Yes | qtw.QMessageBox.No)
            if reply == qtw.QMessageBox.Yes: self.save_hdf5()
            
        if self.wrapper is not None: self.wrapper.clear()
        self.filepath = None
        self.file_changed = False

        # Update treeview
        self.update_treeview()
        self.textBrowser_Log.append("New HDF5 file created")
    
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
            if reply == qtw.QMessageBox.Yes: self.save_hdf5()
            
        
        self.filepath = filepath if filepath is not None else qtw.QFileDialog.getOpenFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
        self.wrapper = wrapper.load_hdf5_file(self.filepath)
        
        # Update treeview
        self.update_treeview()

        # Update parameters with the parameters of the file
        self.treeview_selected = "Data"
        self.update_parameters()

        self.textBrowser_Log.append(f"<i>{self.filepath}</i> opened")
        self.filepath = self.filepath
        self.file_changed = False
    
    def perform_treatment(self):
        """
        Treats all the PSD of the selected data.
        """
        elt = self.wrapper
        for e in self.treeview_selected.split("/")[1:]: elt = elt.data[e]
        type = self.wrapper.get_attributes_path(self.treeview_selected)['SPECTROMETER.Type']
        type = type.replace(" ", "_")
        type = type.replace("-", "_")
            
        # Runs the dedicated treatment function from the treat_ui module
        function_name = f"treat_{type}"
        functions = [func for func in getmembers(treat_ui, isfunction)]
        
        for (name, func) in functions:
            if name == function_name:
                func(self, self.wrapper, self.treeview_selected)

                self.update_treeview()
                self.expand_treeview_path(self.treeview_selected)
                return

        qtw.QMessageBox.warning(self, "Warning", "The type of spectrometer is not recognized")

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

    def show_treeview_context_menu(self, position):
        """
        Show the context menu when right-clicking on an element in the tree view.

        Parameters
        ----------
        position : QPoint
            The position where the context menu should be displayed.

        Returns
        -------
        None
        """
        indexes = self.treeView.selectedIndexes()
        if indexes:
            menu = qtw.QMenu()
            add_action = menu.addAction("Add Data")
            remove_action = menu.addAction("Remove Data")
            menu.addSeparator()
            add_group_action = menu.addAction("Add Group")
            menu.addSeparator()
            get_PSD = menu.addAction("Get Power Spectrum Density")
            perform_treatment = menu.addAction("Treat all Power Spectrum Density")
            menu.addSeparator()
            copy_code = menu.addAction("Copy Python code to access data")
            menu.addSeparator()
            convert_action = menu.addAction("Convert attribtues to CSV")

            action = menu.exec_(self.treeView.viewport().mapToGlobal(position))

            if action == add_action:
                self.add_data()
            elif action == remove_action:
                self.remove_data()
            elif action == add_group_action:
                self.add_group()
            elif action == get_PSD:
                self.get_PSD()
            elif action == perform_treatment:
                self.perform_treatment()
            elif action == copy_code:
                self.export_code_line()
            elif action == convert_action:
                self.convert_csv()

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
            self.treeview_selected = path
            self.update_parameters()
            
    @qtc.Slot()
    def update_parameters(self, filepath=None, file_changed = False):
        """
        Update the parameters based on the selected tree view element.

        Parameters
        ----------
        filepath : str, optional                         
            The path to the CSV file containing the properties to update. If None, the properties of the selected element are updated based on the reference CSV parameter file.

        Returns
        -------
        None
        """
        # Update the wrapper attributes to have all the attributes of the specified version
        if filepath is None: self.wrapper.import_properties_data(f'spreadsheets/attributes_v{wrapper.BLS_HDF5_Version}.csv', update = False)
        else:
            elt = self.wrapper
            if self.treeview_selected != "Data":
                path = self.treeview_selected.split("/")[1:]
                for e in path[:-1]:  elt = elt.data[e]
                update = qtw.QMessageBox.question(self, "Update properties", "Do you want to update the properties of the wrapper with the properties stored in the file?")
                update = True if update == qtw.QMessageBox.Yes else False
                if isinstance(elt.data[path[-1]], (h5py._hl.group.Group, wrapper.Wrapper)): 
                    elt.data[path[-1]].import_properties_data(filepath, update = update)
                else:
                    elt.import_properties_data_attributes(path[-1], filepath, update = update)
            else: 
                update = qtw.QMessageBox.question(self, "Update properties", "Do you want to update the properties of the wrapper with the properties stored in the file?")
                update = True if update == qtw.QMessageBox.Yes else False
                self.wrapper.import_properties_data(filepath, update = update)

        # Extract the attributes of the element selected
        attr = self.wrapper.get_attributes_path(self.treeview_selected)

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
                if name[-1][0] == "(" and name[-1][-1] == ")": unit = name.pop(-1)[1:-1]
                else: unit = ""
                if cat == "MEASURE":
                    self.model_table_Measure.appendRow([qtg.QStandardItem(" ".join(name)), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
                elif cat == "SPECTROMETER":
                    self.model_table_Spectrometer.appendRow([qtg.QStandardItem(" ".join(name)), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
            except:
                pass
        
        self.tableView_Measure.setModel(self.model_table_Measure)    
        self.tableView_Spectrometer.setModel(self.model_table_Spectrometer)

        self.file_changed = file_changed

        self.textBrowser_Log.append(f"Parameters of <b>{self.treeview_selected}</b> have been updated")

    @qtc.Slot()
    def update_parameters_from_table_view(self):
        """
        Update the parameters based on the entered values in the table view.

        Returns
        -------
        None
        """
        def compare_dictionnaries(dict1, dict2):
            attr = {}
            for k, v in dict1.items():
                if k in dict2.keys():
                    if dict2[k] != v:
                        attr[k] = v
            return attr

        def create_parameter_dictionnary_from_table_view(self):
            measure_params = self.read_table_view(self.tableView_Measure)
            spectrometer_params = self.read_table_view(self.tableView_Spectrometer)

            attr = {}
            for k, v in measure_params.items():
                if k == "Name": new_key = "FILEPROP.Name"
                elif ")" in k: new_key = "MEASURE." + "_".join(k.split(" ")) + "_()"
                else: new_key = "MEASURE." + "_".join(k.split(" "))

                if v[1] != "":
                    if new_key.endswith("_()"):  new_key = new_key[:-2] + f"({v[1]})"
                    else: new_key = new_key + f"_({v[1]})"
                attr[new_key] = v[0]

            for k, v in spectrometer_params.items():
                new_key = "SPECTROMETER." + "_".join(k.split(" "))
                if v[1] != "": new_key = new_key + f"_({v[1]})"
                attr[new_key] = v[0]
            
            return attr

        # Get the parameters of the table view and of the wrapper
        attr_table = create_parameter_dictionnary_from_table_view(self)
        attr_wrapper = self.wrapper.get_attributes_path(self.treeview_selected)

        # Compare the two dictionaries
        attr_changed = compare_dictionnaries(attr_table, attr_wrapper)

        # Update the wrapper attributes to have all the attributes of the specified version
        if attr_changed:
            elt = self.wrapper
            for e in self.treeview_selected.split("/")[1:]: elt = elt.data[e]
            if not isinstance(elt, (h5py._hl.group.Group, wrapper.Wrapper)): 
                for e in self.treeview_selected.split("/")[1:-1]: elt = elt.data[e]
            elt.update_property(attr_changed)
        
        self.update_parameters(file_changed=True)
        self.update_treeview()
        self.expand_treeview_path("/".join(self.treeview_selected.split("/")[:-1]))

        self.textBrowser_Log.append(f"Parameters of <b>{self.treeview_selected}</b> have been updated")

    @qtc.Slot()
    def update_treeview(self):     
        """
        Update the tree view with the current wrapper.

        Returns
        -------
        None
        """
        def add_child(wrp, element, parent, path):
            item_path = f"{path}/{element}".replace("//", "/")
            if isinstance(wrp.data[element], (np.ndarray, h5py._hl.dataset.Dataset)):
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
                    for e in wrp.data.keys(): 
                        add_child(wrp, e, loc, item_path) 

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
        Updates the parameters of the selected element when a .csv file is dropped on the table view.

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
            if len(urls) > 1: qtw.QMessageBox.warning(self, "Warning", "Only one property file can be dropped at a time")
            elif len(urls) == 1:
                url = urls[0]
                if os.path.splitext(url)[1] == ".csv": self.update_parameters(filepath = url, file_changed = True) # Verify that the file is a .csv file
                else: qtw.QMessageBox.warning(self, "Warning", "Only .csv property files can be used")
            event.accept()
        else: event.ignore()

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
            
            filepaths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()  # Convert URL to file path
                filepaths.append(file_path)

            parent_path = parent_item.data(qtc.Qt.UserRole) if parent_item else "Root"
            self.treeview_handle_drops(filepaths, parent_path)

            event.accept()
        else:
            event.ignore()
        
    @qtc.Slot()
    def treeview_handle_drops(self, filepaths, parent_path):
        """
        Handle the drop action for the tree view.

        Parameters
        ----------
        filepaths : list
            List of file paths that are to be added to the wrapper.
        parent_path : str
            The parent path of the added data. If None, the data will be added to the root of the HDF5 file.

        Returns
        -------
        None
        """
        temp = [os.path.splitext(filepath)[1] for filepath in filepaths]
        extensions = []
        for e in temp:
            if not e in extensions: extensions.append(e)
        
        paths = [os.path.splitext(filepath)[0] for filepath in filepaths]

        if len(extensions) == 1:
            extension = extensions[0]
            if extension in [".hdf5", ".h5"]:
                if parent_path == "Root" and len(filepaths) == 1:
                    self.open_hdf5(filepaths[0])
                else:
                    self.open_hdf5(filepaths[0])
                    for filepath in filepaths[1:]:
                        self.wrapper.add_hdf5_to_wrapper(filepath, parent_path)
            else:
                for filepath in filepaths:
                    self.add_data(filepath = filepath, parent_path = parent_path)
        
        else:
            qtw.QMessageBox.info(self, "Not implemented", "The GUI only supports addition of multiple files of the same type.")
