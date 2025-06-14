import sys
import os
from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import h5py
import pyperclip
import json
from inspect import getmembers, isfunction
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Main.UI.main_window_ui import Ui_w_Main
from ComboboxChoose.main import ComboboxChoose
from ParameterWindow.main import ParameterWindow
from ProgressBar.main import ProgressBar
from TreatWindow.main import TreatWindow
from _customWidgets import CheckableComboBox

current_dir = os.path.abspath(os.path.dirname(__file__))
relative_path_libs = os.path.join(current_dir, "..", "..", "..")
absolute_path_libs = os.path.abspath(relative_path_libs)
sys.path.append(absolute_path_libs)

from HDF5_BLS.load_formats.errors import LoadError_creator, LoadError_parameters
from HDF5_BLS import wrapper, load_data, conversion_PSD
from HDF5_BLS.WrapperError import WrapperError_Save, WrapperError_Overwrite, WrapperError_ArgumentType
import conversion_ui, treat_ui

class MyStandardItemModel(qtg.QStandardItemModel):
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
    treeview_selected = "Brillouin"
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
            self.b_Close.clicked.connect(self.closeEvent)

        def initialize_menu(self):
            # File menu
            self.a_NewHDF5.triggered.connect(self.new_hdf5)
            self.a_OpenHDF5.triggered.connect(self.open_hdf5)
            self.a_Save.triggered.connect(self.save_hdf5)
            self.a_SaveFileAs.triggered.connect(lambda: self.save_hdf5(saveas=True))
            self.a_AddData.triggered.connect(self.add_data)
            self.a_ConvertCSV.triggered.connect(self.convert_csv)

            # Action menu
            self.a_RenameElement.triggered.connect(self.rename_element) 
            self.a_RepackHDF5.triggered.connect(self.repack)
            self.a_ExportPython.triggered.connect(self.export_code_line)
            self.a_Apply_Treatment.triggered.connect(self.get_treatment)
            self.a_Get_PSD.triggered.connect(self.get_PSD)
            self.a_ExportImage.triggered.connect(self.export_image)

        def initialize_timer(self):
            self.hover_timer = qtc.QTimer(self) 
            self.hover_timer.setSingleShot(True)
            self.hover_timer.timeout.connect(self.expand_on_hover)  # Connect to the expand function

        def initialize_tableview(self):   
            # Creates a model with 3 columns and sets it to the tableview.
            self.model_table_Measure = qtg.QStandardItemModel()
            self.model_table_Measure.setHorizontalHeaderLabels(["Parameter", "Value"])
            self.model_table_Spectrometer = qtg.QStandardItemModel()
            self.model_table_Spectrometer.setHorizontalHeaderLabels(["Parameter", "Value"])
            self.model_table_Other = qtg.QStandardItemModel()
            self.model_table_Other.setHorizontalHeaderLabels(["Parameter", "Value"])
            self.tableView_Measure.setModel(self.model_table_Measure)    
            self.tableView_Spectrometer.setModel(self.model_table_Spectrometer)
            self.tableView_Other.setModel(self.model_table_Other)

            # Connect signals to the slot
            self.model_table_Measure.itemChanged.connect(self.update_parameters_from_table_view)
            self.model_table_Spectrometer.itemChanged.connect(self.update_parameters_from_table_view)
            
            # Sets the selection mode of the table views
            self.tableView_Measure.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
            self.tableView_Measure.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
            self.tableView_Spectrometer.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
            self.tableView_Spectrometer.setSelectionMode(qtw.QAbstractItemView.SingleSelection)

            # Adds a CheckableCombobox to the f_SelectionPlots frame
            self.cb_SelectionPlots = CheckableComboBox()
            self.cb_SelectionPlots.addItems(["Amplitude", "Amplitude Variance", "Shift", "Shift Variance", "Linewidth", "Linewidth Variance", "BLT", "BLT Variance"])
            self.cb_SelectionPlots.setObjectName(u"cb_SelectionPlots")
            self.horizontalLayout.addWidget(self.cb_SelectionPlots)

            # Connect parameter button
            self.b_Parameters.clicked.connect(self.paramters_visualize)

            # Deactivate the combobox and the plots
            self.cb_Treatment.setEnabled(False)
            self.cb_SelectionPlots.setEnabled(False)

            # Connect the comboboxes to the "update_graph" function
            self.cb_Treatment.currentIndexChanged.connect(self.update_graph)
            self.cb_SelectionPlots.selectionChanged.connect(self.update_graph)

            # Create a Matplotlib figure and canvas
            self.figure = Figure(figsize=(3,4))
            self.canvas = FigureCanvas(self.figure)

            # Add the canvas to the frame
            self.layout_visualize_plots = qtw.QVBoxLayout(self.f_VisualizePlots)
            self.layout_visualize_plots.addWidget(self.canvas)

            # Select Measure Tab by default
            self.tabWidget_Visualize.setCurrentIndex(0)

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
            self.treeView.expanded.connect(self.adjust_treeview_columns)

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

        self.wrapper = wrapper.Wrapper(filepath = None)
        self.filepath = self.wrapper.filepath
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
            if len(self.wrapper.get_children_elements()) > 0:
                self.b_RemoveData.setEnabled(True)
                self.b_ConvertCSV.setEnabled(True)

    def activate_menu(self):
        """
        Activate menu items based on the current state of the application.

        Returns
        -------
        None
        """
        if len(self.wrapper.get_children_elements()) > 0:
            self.a_RepackHDF5.setEnabled(True)
            self.a_RenameElement.setEnabled(True)
            self.a_ExportPython.setEnabled(True)
            self.a_Get_PSD.setEnabled(True)
            self.a_Apply_Treatment.setEnabled(True) 
            self.a_ExportImage.setEnabled(True) 

    def add_data(self, event=None, filepath=None, parent_path=None):
        """
        Add data to the current HDF5 file.

        Parameters
        ----------
        event : qtc.QEvent, optional
            The event that triggered the function call. Default is None.
        filepath : str or list, optional
            The path to the file to add or the list of paths of the files to add. If None, a file dialog will open to select a file. Default is None.
        parent_path : str, optional
            The parent path of the added data. If None, the data will be added to the root of the HDF5 file. Default is None.
        
        Returns
        -------
        None
        """
        def add_to_root():
            dialog = qtw.QMessageBox.question(self, "Precisions", "Do you want to add the data to the opened file (Yes) or create a new one (No)?", qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
            if dialog == qtw.QMessageBox.No: # The user wants to create a new file
                try: # If the file hasn't been saved, an error is raised
                    self.wrapper.close()
                    self.wrapper = wrapper.Wrapper()
                except WrapperError_Save:
                    if not self.handle_error_save(): return # If the user decides to cancel his action at this point, the function ends
                self.wrapper = wrapper.Wrapper()
            elif dialog == qtw.QMessageBox.Cancel:
                return

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

        def create_structure(dic, parent_path):
            for key in dic.keys():
                if "." in key:
                    pass
                else:
                    self.wrapper.create_group(key, parent_group=parent_path)
                    create_structure(dic[key], f"{parent_path}/{key}")

        def get_dictionnary(file, creator = None, parameters = None):
            # First we try adding the data based on the file extension
            try: 
                dic = load_data.load_general(file)
            # If it does not work, it might be that the file extension is not supported, in that case display a warning window
            except ValueError: 
                qtw.QMessageBox.warning(self, "Warning", "The file extension is not supported.")
                return
            
            # It can also be that there are different ways to load the data, in that case display a dialog box to choose the type of structure to load
            except LoadError_creator as e: 
                creator_list = e.creators 
                dialog = ComboboxChoose(text = "Choose the type of structure to load", list_choices = creator_list, parent = self)
                # If the user cancels the dialog box, we return
                if dialog.exec_() == qtw.QDialog.Rejected:
                    return
                else:
                    creator = dialog.get_selected_structure()
                    # After choosing the type of structure, we try to load the data again by precising the structure
                    try:
                        dic = load_data.load_general(file, creator = creator)
                    
                    # If it does not work, this means that the user needs to indicate the parameters to load the data, so we load a window to do so
                    except LoadError_parameters as e: 
                        parameters = e.parameters
                        dialog = ParameterWindow(text = f"Please indicate the value of the following parameters to load the data:",
                                                list_parameters = parameters, 
                                                parent = self,
                                                root_path=os.path.dirname(file))
                        if dialog.exec_() == qtw.QDialog.Accepted:
                            parameters = dialog.get_selected_structure()
                            dialog.close()
                        else:
                            dialog.close()
                            return
                        dic = load_data.load_general(file, creator, parameters)
                    
                    # If it still doesn't work, then there was a mistake while opening the file so print an error
                    except Exception as e:
                        qtw.QMessageBox.warning(self, "Error while adding the file: ", str(e))
                        return
            
            # If it doesn't work, there was a mistake while opening the file so print an error
            except Exception as e:
                qtw.QMessageBox.warning(self, "Error while adding the file: ", str(e))
                return
            return creator, parameters, dic

        def get_extensions(filepath, extensions = []):
            for f in filepath:
                ext = os.path.splitext(f)[1]
                if ext == "":
                    files = os.listdir(f)
                    if ".DS_Store" in files: files.remove(".DS_Store")
                    get_extensions([f"{f}/{file}" for file in files], extensions)
                else:
                    if ext not in extensions:
                        extensions.append(ext)
            return extensions

        def get_children_files_by_extension(filepath, extension, file = [], path_from_parent = [], parent = ""):
            files = os.listdir(filepath)
            if ".DS_Store" in files: files.remove(".DS_Store")
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext == extension:
                    file.append(os.path.join(filepath, f))
                    path_from_parent.append(parent)
                elif ext == "":
                    if ".DS_Store" in files: files.remove(".DS_Store")
                    if parent != "":
                        file, path_from_parent = get_children_files_by_extension(os.path.join(filepath, f), 
                                                                                extension, 
                                                                                file = file, 
                                                                                path_from_parent= path_from_parent,
                                                                                parent = f"{parent}/{f}")
                    else:
                        file, path_from_parent = get_children_files_by_extension(os.path.join(filepath, f), 
                                                                                extension, 
                                                                                file = file, 
                                                                                path_from_parent= path_from_parent,
                                                                                parent = f)
            return file, path_from_parent

        def update_progress():
            nonlocal i
            if i < len(filepath):
                file, path_parent = filepath[i], path_from_parent[i]
                dic = load_data.load_general(file, creator=creator, parameters=parameters)
                name_group = os.path.basename(file).split(".")[0]
                name_group = name_group.replace("  ", " ")
                if path_parent == "":
                    self.wrapper.add_dictionnary(dic, 
                                                 parent_group=parent_path, 
                                                 name_group=name_group)
                else:
                    self.wrapper.add_dictionnary(dic, 
                                                 parent_group=f"{parent_path}/{path_parent}",
                                                 name_group = name_group)
                self.textBrowser_Log.append(f"<i>{file}</i> added to <b>{parent_path}</b>")
                i += 1
                progress.update_progress(i / len(filepath) * 100, f"Adding {file} to {path_parent}")
            else:
                timer.stop()
                progress.close()

        # Get filepath            
        if filepath is None: 
            filepath = qtw.QFileDialog.getOpenFileNames(self, "Open File", "", "All Files (*)")[0]
            if filepath is None: return
        if type(filepath) == str :  
            filepath = [filepath]

        # Set parent path to the selected element if it is None
        if parent_path is None: 
            parent_path = self.treeview_selected

        # Create a new wrapper if the file is not empty and the parent path is the root
        if parent_path == "Brillouin" and len(self.wrapper.get_children_elements()) > 0:
            add_to_root()

        # Makes sure to add the data to a group, even if it is dragged under a dataset
        if self.wrapper.get_type(parent_path) != h5py._hl.group.Group:
            parent_path = "/".join(parent_path.split("/")[:-1])

        # If we have dragged an entire directory, add each element of the directory with the same structure (directory <=> groups)
        dir_present = False
        for f in filepath:
            if os.path.splitext(f)[1] == "":
                dir_present = True
        if dir_present:
            response = qtw.QMessageBox.question(self, "Warning", "You are trying to add a directory. Do you want to add all the files in the directory with the same structure?", qtw.QMessageBox.Yes | qtw.QMessageBox.No)
            if response == qtw.QMessageBox.Yes:
                extensions = get_extensions(filepath)
                dialog = ComboboxChoose(text = "Choose the file you want to load by their extension", list_choices = extensions, parent = self)
                if dialog.exec_() == qtw.QDialog.Accepted:
                    extension = dialog.get_selected_structure()
                    files, path_from_parent = [], []
                    for file in filepath:
                        temp_file, temp_path_from_parent = get_children_files_by_extension(file, extension)
                        files += temp_file
                        path_from_parent += temp_path_from_parent
                    # Create file structure in the HDF5 file
                    for path_parent in path_from_parent:
                        if path_parent == "": continue
                        path_split = path_parent.split("/")
                        temp_path = ""
                        for p in path_split:
                            if temp_path == "": 
                                if p not in self.wrapper.get_children_elements(parent_path):
                                    self.wrapper.create_group(p, parent_group = parent_path)
                                temp_path = p
                            else: 
                                if p not in self.wrapper.get_children_elements(parent_path+"/"+temp_path):
                                    self.wrapper.create_group(p, parent_group = parent_path+"/"+temp_path)
                                temp_path = f"{temp_path}/{p}"
                    filepath = files
                else:
                    return
        else:
            path_from_parent = ["" for i in filepath]
        
        # Creating the dictionnary with the data and the attributes starting with the addition of a single file
        file = filepath.pop(0)
        path_parent = path_from_parent.pop(0)
        creator, parameters, dic = get_dictionnary(file, creator = None, parameters = None)
        name_group = os.path.basename(file).split(".")[0]
        name_group = name_group.replace("  ", " ")
        if path_parent == "":
            self.wrapper.add_dictionnary(dic, 
                                        parent_group = parent_path, 
                                        name_group = name_group)
        else:
            self.wrapper.add_dictionnary(dic, 
                                        parent_group = parent_path+"/"+path_parent, 
                                        name_group = name_group)
        
        # Logging the added data
        self.textBrowser_Log.append(f"<i>{file}</i> added to <b>{parent_path}</b>")

        # Using the creator and parameters used to load the first data to load the rest of the data. During loading, a progress window is opened allowing to see the progress of the loading
        timer = qtc.QTimer(self)
        i = 0
        progress = ProgressBar(f"Adding {len(filepath)} files to the HDF5 file", self)
        progress.show()
        timer.timeout.connect(update_progress)
        timer.start(10)  # Update every 10 ms
        while timer.isActive(): # Wait for the timer to finish
            qtw.QApplication.processEvents()

        # Updating the treeview
        if path_parent == "":
            self.treeview_selected = f"{parent_path}/{name_group}"
        else:
            self.treeview_selected = f"{parent_path}/{path_parent}/{name_group}"

        self.update_treeview()
        self.update_parameters()
        self.expand_treeview_path(self.treeview_selected)
    
    def add_group(self):
        """
        Add a group to the current HDF5 file.

        Returns
        -------
        None
        """
        self.wrapper.create_group(name = "New group", 
                                  parent_group = self.treeview_selected)
        self.treeview_selected = f"{self.treeview_selected}/New group"
        self.textBrowser_Log.append(f"<i>New group</i> added to <b>{self.treeview_selected}</b>")
        self.update_treeview()
        self.expand_treeview_path(self.treeview_selected)

    def adjust_treeview_columns(self, index=None):
        """
        Adjusts the width of all columns in the treeView to fit their contents.
        """
        header = self.treeView.header()
        for col in range(self.treeView.model().columnCount()):
            self.treeView.resizeColumnToContents(col)

    def closeEvent(self):
        """
        Close the window and exit the application.

        Returns
        -------
        None
        """
        # Handle the error if the wrapper is not saved
        if self.wrapper.save:
            self.handle_error_save()

        # Repack the wrapper if it exists
        # if os.path.isfile(self.filepath):
        #     self.wrapper.repack()
        
        # Delete the temporary file if it exists
        self.wrapper.close(delete_temp_file = True)
        try:
            self.close()
        except:
            pass

    def convert_csv(self):
        """
        Exports the properties of the wrapper to a CSV file.

        Returns
        -------
        None
        """
        filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "CSV Files (*.csv)")[0]
        if filepath:
            self.wrapper.save_properties_csv(filepath, path = self.treeview_selected)

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
            for part in path.split("/"):
                for row in range(self.treeView.model().rowCount(current_index)):
                    child_index = self.treeView.model().index(row, 0, current_index)
                    if child_index.data() == part:
                        current_index = child_index
                        self.treeView.setExpanded(current_index, True)  # Expand the parent
    
    def export_code_line(self):
        """
        Export the selected code line to a Python script that can be used to access the data.

        Returns
        -------
        None
        """
        if self.wrapper.get_type(path = self.treeview_selected) is h5py._hl.group.Group:
            qtw.QMessageBox.warning(self, "Warning", "The selected path is not a dataset. Please select a dataset.")
            return

        text = "import h5py as h5\nimport numpy as np\n\n"
        text += f'with h5.File("{self.filepath}", "r") as f:\n'
        text += f'\tdata = np.array(f["{self.treeview_selected}"])\n'
        
        pyperclip.copy(text)

        qtw.QMessageBox.information(self, "Copied to clipboard", f"Code to access the data copied to clipboard")

        self.textBrowser_Log.append(f"Python code to access the data of <b>{self.treeview_selected}</b> has been copied to the clipboard")

    def export_HDF5_group(self):
        """
        Export the selected group as a HDF5 file.

        Returns
        -------
        None
        """
        filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
        if filepath:
            self.wrapper.export_group(self.treeview_selected, filepath)

    def export_image(self):
        """
        Export the selected dataset as an image.

        Returns
        -------
        None
        """
        def return_names_2D_datasets_children(path, names = []):
            for e in self.wrapper.get_children_elements(path = path):
                if self.wrapper.get_type(path = f"{path}/{e}") == h5py._hl.dataset.Dataset:
                    data = self.wrapper[f"{path}/{e}"]

                    # Reshape the element to avoid singleton dimensions
                    new_shape = []
                    for s in data.shape:
                        if s > 1: new_shape.append(s)
                    data = data.reshape(new_shape)

                    # If the dataset is 2D and the name is not already in the list of names, add it to the list
                    if len(data.shape) == 2:
                        if not e in names:
                            names.append(e)
                else:
                    names = return_names_2D_datasets_children(path = f"{path}/{e}", names = names)

            return names

        def save_images_group_recursively(filepath, path, name, save_hierarchy = True, fmt = ".tiff"):
            """Saves all the 2D datasets present under the given path in the HDF5 file as images 

            Parameters
            ----------
            filepath : str
                The path to the directory where to save the images
            path : str
                The path to the group in the HDF5 file
            name : str
                The name of the dataset to store
            save_hierarchy : bool, optional
                Wether to store the file hierarchically or not. If False, the name of the image will be the name of the whole path in the HDF5 file. If true, directories corresponding to the groups of the HDF5 file are created, and the image names are just the name of the elements in the HDF5 file, by default True.
            """
            for e in self.wrapper.get_children_elements(path = path):
                if self.wrapper.get_type(path = f"{path}/{e}") == h5py._hl.dataset.Dataset and e == name:
                    if save_hierarchy:
                        self.wrapper.export_image(f"{path}/{e}", filepath+"/"+e+fmt)
                    else:
                        self.wrapper.export_image(f"{path}/{e}", filepath+"/"+path.replace("/", " - ")+" - "+e+fmt)
                elif self.wrapper.get_type(path = f"{path}/{e}") == h5py._hl.group.Group:
                    if self.wrapper.get_type(path = f"{path}/{e}", return_Brillouin_type= True) == "Treatment" or not save_hierarchy:
                        save_images_group_recursively(filepath, path+"/"+e, name, save_hierarchy, fmt = fmt)
                    else:
                        if not os.path.isdir(filepath+"/"+e):
                            os.makedirs(filepath+"/"+e)
                        save_images_group_recursively(filepath+"/"+e, path+"/"+e, name, save_hierarchy, fmt = fmt)

        hierarchy = False
        # If a dataset has been selected, ask the user for a filename to save the image at
        if self.wrapper.get_type(self.treeview_selected) == h5py._hl.dataset.Dataset:
            # Asks the user for the format of the image
            formats = [".tiff", ".png", ".jpg", ".jpeg", ".bmp", ".gif"]
            dialog = ComboboxChoose(text = "Choose the format in which to store the images", list_choices = formats, parent = self)
            # If the user cancels the dialog box, we return
            if dialog.exec_() == qtw.QDialog.Rejected:
                return
            else:
                fmt = dialog.get_selected_structure()
            
            # Asks the user for the filepath to save the image at
            filepath = qtw.QFileDialog.getSaveFileName(self, "Save File", "", f"Image (*{fmt})")[0]
            if filepath:
                self.wrapper.export_image(self.treeview_selected, filepath)
        # If a group has been selected, ask the user wether to store all the images of the group in the same file or recreate the hierarchy
        else:
            response = qtw.QMessageBox.question(self, "Warning", "Do you want to export every image of the selected group at the same location (Yes) or recreate the hierarchy (No)?", qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
            if response == qtw.QMessageBox.Yes: hierarchy = False
            elif response == qtw.QMessageBox.No: hierarchy = True
            else: return
        
        # Get the potential candidates for export
        candidates = return_names_2D_datasets_children(path = self.treeview_selected)

        # Ask the user which name has to be exported
        if len(candidates) == 0: 
            qtw.QMessageBox.warning(self, "Warning", "No 2D dataset found in the selected group")
        else:
            dialog = ComboboxChoose(text = "Choose the name of the datasets you wish to export as images", list_choices = candidates, parent = self)
            # If the user cancels the dialog box, we return
            if dialog.exec_() == qtw.QDialog.Rejected:
                return
            else:
                name = dialog.get_selected_structure()

        # Asks the user for a file to export the images
        filepath = qtw.QFileDialog.getExistingDirectory(self, "Select Directory", self.filepath)
        if not filepath: return 

        # Asks the user for the format of the image
        formats = [".tiff", ".png", ".jpg", ".jpeg", ".bmp", ".gif"]
        dialog = ComboboxChoose(text = "Choose the format in which to store the images", list_choices = formats, parent = self)
        # If the user cancels the dialog box, we return
        if dialog.exec_() == qtw.QDialog.Rejected:
            return
        else:
            fmt = dialog.get_selected_structure()
        
        
        # Export the images. If hierarchy is set to True, start by creating a directory with name the name of the selected group
        if hierarchy: 
            # Save recursively the images 
            save_images_group_recursively(filepath, self.treeview_selected, name, save_hierarchy=True, fmt = fmt)
        else:
            # Save recursively the images 
            save_images_group_recursively(filepath, self.treeview_selected, name, save_hierarchy=False, fmt = fmt)

    def export_numpy_array(self):
        """
        Export the selected dataset as a numpy array.

        Returns
        -------
        None
        """
        filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "Numpy Array (*.npy)")[0]
        if filepath:
            self.wrapper.export_dataset(self.treeview_selected, filepath)

    def get_PSD(self):
        """
        Get the Power Spectrum Density of the selected data. If the process to extract the PSD is already stored in the attributes of the selected group, it is opened.

        Returns
        -------
        None
        """
        try:
            type = self.wrapper.get_attributes(self.treeview_selected)['SPECTROMETER.Type']
            type = type.replace(" ", "_")
            type = type.replace("-", "_")
        except KeyError:
            qtw.QMessageBox.warning(self, "Warning", "The selected data does not have a spectrometer type.")
            return

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
        
        self.update_treeview()
        self.expand_treeview_path(self.treeview_selected)

    def get_treatment(self):
        """
        Treats all the PSD of the selected data.
        """
        # Verifies that in the Measure group selected, a PSD is stored
        parent = self.treeview_selected
        while self.wrapper.get_type(path = parent, return_Brillouin_type = True) != "Measure":
            parent = "/".join(parent.split("/")[:-1])
        no_PSD = True
        for e in self.wrapper.get_children_elements(path = parent):
            if self.wrapper.get_type(path = f"{parent}/{e}", return_Brillouin_type = True) == "PSD":
                no_PSD = False
        if no_PSD:
            qtw.QMessageBox.warning(self, "Warning", "No PSD has been stored in the selected group")
        
        # Opens the treatment GUI
        treatment = TreatWindow(self)
        treatment.exec_()

    def handle_error_save(self):
        """Function that handles the error when trying to close the wrapper without saving it.

        Returns
        -------
        bool
            True if the user saved the wrapper or decided to discard it, False if the user cancelled the action.
        """
        dialog = qtw.QMessageBox.question(self,"Unsaved changes", "The file has not been saved yet. Do you want to save it?", qtw.QMessageBox.Yes | qtw.QMessageBox.No |qtw.QMessageBox.Cancel)
        if dialog == qtw.QMessageBox.Yes:
            self.save_hdf5()
            self.wrapper.close()
        elif dialog == qtw.QMessageBox.No:
            self.wrapper.save = False
            self.wrapper.close()
        elif dialog == qtw.QMessageBox.Cancel:
            return False
        return True

    def merge_group_dataset(self):
        """
        Merge all the datasets of a group into a single dataset

        Returns
        -------
        None
        """
        def get_all_brillouin_types(path, brillouin_types = []):
            for e in self.wrapper.get_children_elements(path = path):
                if self.wrapper.get_type(path = f"{path}/{e}") == h5py._hl.group.Group:
                    get_all_brillouin_types(path = f"{path}/{e}", brillouin_types = brillouin_types)
                else:
                    tpe = self.wrapper.get_type(path = f"{path}/{e}", return_Brillouin_type = True)
                    if tpe not in brillouin_types:
                        brillouin_types.append(tpe)
            return brillouin_types

        def get_all_datasets(path, type_dset = None, datasets = []):
            for e in self.wrapper.get_children_elements(path = path):
                if self.wrapper.get_type(path = f"{path}/{e}") == h5py._hl.dataset.Dataset:
                    if self.wrapper.get_type(path = f"{path}/{e}", return_Brillouin_type = True) == type_dset:
                        datasets.append(f"{path}/{e}")
                else:
                    datasets = get_all_datasets(path = f"{path}/{e}", type_dset = type_dset, datasets = datasets)
            return datasets

        # Extract the types of all the datasets under the selected group
        brillouin_types = get_all_brillouin_types(self.treeview_selected)

        # Asks the user for the type to merge the datasets into
        dialog = ComboboxChoose(text = "Choose the type to merge the datasets into", list_choices = brillouin_types, parent = self)
        if dialog.exec_() == qtw.QDialog.Accepted:
            brillouin_type = dialog.get_selected_structure()
        else:
            return
        
        # Extract a list of all the datasets under the selected groups with the correct type.
        datasets = get_all_datasets(self.treeview_selected, type_dset = brillouin_type)

        self.wrapper.combine_datasets(datasets = datasets, parent_group = self.treeview_selected, name = brillouin_type, overwrite = True)
        self.update_treeview()
        self.expand_treeview_path(self.treeview_selected)

    def new_hdf5(self):
        """
        Create a new HDF5 file.

        Returns
        -------
        None
        """
        if self.wrapper.save:
            self.handle_error_save()
        
        self.wrapper = wrapper.Wrapper()
        self.filepath = None
            
        # Update treeview
        self.update_treeview()

        # Update parameters with the parameters of the file
        self.treeview_selected = "Brillouin"
        self.update_parameters()

        self.textBrowser_Log.append(f"A new file has been created")
    
    def open_hdf5(self, event = None, filepath=None):
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
        if filepath is None:
            filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "", "HDF5 Files (*.h5)")[0]
            if filepath is None: return
            else: self.filepath = filepath
        else:
            self.filepath = filepath 

        if self.wrapper.save:
            self.handle_error_save()
        
        self.wrapper = wrapper.Wrapper(filepath)
            
        # Update treeview
        self.update_treeview()

        # Update parameters with the parameters of the file
        self.treeview_selected = "Brillouin"
        self.update_parameters()

        self.textBrowser_Log.append(f"<i>{self.filepath}</i> opened")
    
    def paramters_visualize(self):
        """
        Opens the GUI to visualize the parameters of the selected data.
        """
        qtw.QMessageBox.information(self, "Not implemented", "To do")

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
        """Removes the selected element from the HDF5 file.
        """
        confirm = qtw.QMessageBox.question(self, "Remove element", f"Do you want to remove {self.treeview_selected} from the HDF5 file? This action cannot be undone.")
        if confirm == qtw.QMessageBox.Yes:
            self.wrapper.delete_element(path = self.treeview_selected)
            self.textBrowser_Log.append(f"<i>{self.treeview_selected}</i> removed from the HDF5 file")
            self.treeview_selected = "/".join(self.treeview_selected.split("/")[:-1])
            self.update_treeview()
            self.expand_treeview_path(self.treeview_selected)

    def rename_element(self):
        """
        Renames the selected element in the HDF5 file.

        Returns
        -------
        None
        """
        new_name = qtw.QInputDialog.getText(self, "Rename element", "Enter the new name:")[0]
        if new_name:
            self.wrapper.change_name(path = self.treeview_selected, name = new_name)
            self.treeview_selected = new_name
            self.update_treeview()
            self.expand_treeview_path(self.treeview_selected)

    def repack(self):
        """
        Repacks the wrapper to minimize its size.

        Returns
        -------
        None
        """
        self.wrapper.repack()

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
        self.filepath = qtw.QFileDialog.getSaveFileName(self, "Save File", "", "HDF5 Files (*.h5)")[0]
        if self.filepath:
            # We first try to save the file, if the file already exists, then the user is asked if he wants to overwrite it by the system (not done by this code)
            try:
                self.wrapper.save_as_hdf5(self.filepath)
            # If the user continues despite the system error message, we overwrite the file
            except WrapperError_Overwrite:
                self.wrapper.save_as_hdf5(self.filepath, overwrite = True)
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
        def sub_menu_Brillouin_type():
            def add_abscissa():
                qtw.QMessageBox.information(self, "Not implemented", "To do")

            def apply_change(value):
                self.wrapper.change_brillouin_type(path=self.treeview_selected, brillouin_type=value)
                self.update_treeview()
                self.expand_treeview_path("/".join(self.treeview_selected.split("/")[:-1]))

            edit_Brillouin_type.clear()
            actions = []

            if self.wrapper.get_type(path=self.treeview_selected) == h5py._hl.group.Group:
                calibration = qtg.QAction("Calibration Spectrum", self)
                calibration.triggered.connect(lambda: apply_change(value="Calibration_spectrum"))
                actions.append(calibration)
                impulse_response = qtg.QAction("Impulse Response", self)
                impulse_response.triggered.connect(lambda: apply_change(value="Impulse_response"))
                actions.append(impulse_response)
                measure = qtg.QAction("Measure", self)
                measure.triggered.connect(lambda: apply_change(value="Measure"))
                actions.append(measure)
                root = qtg.QAction("Root", self)
                root.triggered.connect(lambda: apply_change(value="Root"))
                actions.append(root)
                treatment = qtg.QAction("Treatment", self)
                treatment.triggered.connect(lambda: apply_change(value="Treatment"))
                actions.append(treatment)
            else:
                abscissa = qtg.QAction("Abscissa", self)
                abscissa.triggered.connect(add_abscissa)
                actions.append(abscissa)
                frequency = qtg.QAction("Frequency", self)
                frequency.triggered.connect(lambda: apply_change(value="Frequency"))
                actions.append(frequency)
                linewidth = qtg.QAction("Linewidth", self)
                linewidth.triggered.connect(lambda: apply_change(value="Linewidth"))
                actions.append(linewidth)
                other = qtg.QAction("Other", self)
                other.triggered.connect(lambda: apply_change(value="Other"))
                actions.append(other)
                psd = qtg.QAction("PSD", self)
                psd.triggered.connect(lambda: apply_change(value="PSD"))
                actions.append(psd)
                raw = qtg.QAction("Raw Data", self)
                raw.triggered.connect(lambda: apply_change(value="Raw_data"))
                actions.append(raw)
                shift = qtg.QAction("Shift", self)
                shift.triggered.connect(lambda: apply_change(value="Shift"))
                actions.append(shift)
                linewidth_std = qtg.QAction("Linewidth Standard Deviation", self)
                linewidth_std.triggered.connect(lambda: apply_change(value="Linewidth_std"))
                actions.append(linewidth_std)
                shift_std = qtg.QAction("Shift Standard Deviation", self)
                shift_std.triggered.connect(lambda: apply_change(value="Shift_std"))
                actions.append(shift_std)
            
            for action in actions:
                edit_Brillouin_type.addAction(action)    
        
        def sub_menu_export():
            def export_algorithm(str_algorithm):
                # Convert string algorithm into dictionnary
                try:
                    algorithm = json.loads(str_algorithm)
                except:
                    qtw.QMessageBox.warning(self, "Warning", "The algorithm is not valid.")
                    return

                filepath = qtw.QFileDialog.getSaveFileName(self, "Open File", "", "JSON Files (*.json)")[0]
                if filepath:
                    with open(filepath, 'w') as f:
                        json.dump(algorithm, f, indent=4)

            export.clear()
            actions = []

            export_Python = qtg.QAction("Generate Python code to access data", self)
            export_Python.triggered.connect(self.export_code_line)
            actions.append(export_Python)
            export_CSV = qtg.QAction("Export attributes to CSV", self)
            export_CSV.triggered.connect(self.convert_csv)
            actions.append(export_CSV)

            if self.wrapper.get_type(path=self.treeview_selected) == h5py._hl.group.Group:
                export_HDF5 = qtg.QAction("Export group as HDF5 file", self)
                export_HDF5.triggered.connect(self.export_HDF5_group)
                actions.append(export_HDF5)
                export_image = qtg.QAction("Export image", self)
                export_image.triggered.connect(self.export_image)
                actions.append(export_image)
                if "Process_PSD" in self.wrapper.get_attributes(path=self.treeview_selected).keys():
                    export_PSD = qtg.QAction("Export PSD algorithm", self)
                    export_PSD.triggered.connect(lambda: export_algorithm(self.wrapper.get_attributes(path=self.treeview_selected)["Process_PSD"]))
                    actions.append(export_PSD)
            else:
                export_HDF5 = qtg.QAction("Export dataset as numpy array", self)
                export_HDF5.triggered.connect(self.export_numpy_array)
                actions.append(export_HDF5)
                if len(self.wrapper[self.treeview_selected].shape) == 2:
                    export_image = qtg.QAction("Export image", self)
                    export_image.triggered.connect(self.export_image)
                    actions.append(export_image)

                if "Process_PSD" in self.wrapper.get_attributes(path="/".join(self.treeview_selected.split("/")[:-1])).keys():
                    export_PSD = qtg.QAction("Export PSD algorithm", self)
                    export_PSD.triggered.connect(lambda: export_algorithm(self.wrapper.get_attributes(path="/".join(self.treeview_selected.split("/")[:-1]))["Process_PSD"]))
                    actions.append(export_PSD)

            for action in actions:
                export.addAction(action)   

        indexes = self.treeView.selectedIndexes()
        if indexes:
            menu = qtw.QMenu()
            add_action = menu.addAction("Add Data")
            remove_action = menu.addAction("Remove Data")
            menu.addSeparator()
            add_group_action = menu.addAction("Add Group")
            edit_Brillouin_type = menu.addMenu("Edit Type")
            if self.wrapper.get_type(path=self.treeview_selected, return_Brillouin_type = True) == "Root":
                merge_group = menu.addAction("Merge Group into Dataset")
            menu.addSeparator()
            get_PSD = menu.addAction("Get Power Spectrum Density")
            perform_treatment = menu.addAction("Treat all Power Spectrum Density")
            menu.addSeparator()
            export = menu.addMenu("Export")
            menu.addSeparator()
            expand = menu.addAction("Expand all children")

            edit_Brillouin_type.aboutToShow.connect(sub_menu_Brillouin_type)
            export.aboutToShow.connect(sub_menu_export)
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
                self.get_treatment()
            elif action == expand:
                for e in self.wrapper.get_children_elements(path = self.treeview_selected):
                    self.expand_treeview_path(f"{self.treeview_selected}/{e}")
            elif self.wrapper.get_type(path=self.treeview_selected, return_Brillouin_type = True) == "Root" and action == merge_group:
                self.merge_group_dataset()

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
            if len(urls) > 1: 
                qtw.QMessageBox.warning(self, "Warning", "Only one property file can be dropped at a time")
            elif len(urls) == 1:
                url = urls[0]
                if os.path.splitext(url)[1] in [".csv", ".xlsx",".xls"]: 
                    if len(self.wrapper.get_children_elements(self.treeview_selected))>1:
                        response = qtw.QMessageBox.information(self, "Warning", "Do you want to update the properties of each element of the selected group or dataset?", qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
                        if response == qtw.QMessageBox.Yes:
                            self.update_parameters(filepath = url, delete_child_attributes = True) # Verify that the file is a .csv file
                        elif response == qtw.QMessageBox.Cancel:
                            return
                        else:
                            self.update_parameters(filepath = url) # Verify that the file is a .csv file
                    else:
                        self.update_parameters(filepath = url, delete_child_attributes = True) # Verify that the file is a .csv file
                else: 
                    qtw.QMessageBox.warning(self, "Warning", "Only .csv, .xlsx or .xls property files can be used")
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
        elif event.mimeData().hasFormat("application/x-brillouin-path"):
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
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            index = self.treeView.indexAt(event.pos())
            if index.isValid():
                if self.current_hover_index != index:  # If a new item is hovered
                    self.hover_timer.stop()  # Stop any previous timers
                    self.current_hover_index = index  # Update the current item
                    item = self.model.itemFromIndex(index)
                    if item.hasChildren():
                        self.hover_timer.start(500)  # Start a 0.5-second timer
            event.accept()
        elif event.mimeData().hasFormat("application/x-brillouin-path"):
            event.accept()
        else:
            event.ignore()

    @qtc.Slot()
    def treeView_dropEvent(self, event: qtg.QDropEvent):
        """
        Handle the drop event for the tree view.
        """
        self.hover_timer.stop()
        self.current_hover_index = None

        # Get the target item and path
        index = self.treeView.indexAt(event.pos())
        target_item = self.model.itemFromIndex(index) if index.isValid() else None
        target_path = target_item.data(qtc.Qt.UserRole) if target_item else "Brillouin"

        if event.mimeData().hasUrls():
            # External file drop
            filepaths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.treeview_handle_drops_files(filepaths, target_path)
            event.accept()

        elif event.mimeData().hasFormat("application/x-brillouin-path"):
            # Internal tree drag-drop
            dragged_path = str(event.mimeData().data("application/x-brillouin-path"), encoding='utf-8')
            self.wrapper.move(path = dragged_path, new_path = target_path)
            self.treeview_selected = target_path+"/"+dragged_path.split("/")[-1]
            self.update_treeview()
            self.update_parameters()
            self.expand_treeview_path(self.treeview_selected)
            event.accept()

        else:
            event.ignore()
    
    @qtc.Slot()
    def treeview_element_changed(self, topLeft, bottomRight, roles):
        """
        Handle the event when a tree view element is changed.

        Parameters
        ----------
        topLeft : QModelIndex
            The top-left index of the changed data in the model.
        bottomRight : QModelIndex
            The bottom-right index of the changed data in the model.
        roles : list
            The roles that triggered the change.

        Returns
        -------
        None
        """
        # Ensure we're detecting edits, not just selection changes
        if qtc.Qt.EditRole in roles:
            column = topLeft.column()
            new_value = topLeft.data(qtc.Qt.EditRole)

            # Handle changes based on the column
            if column == 0:  # Name column
                self.wrapper.change_name(path=self.treeview_selected, name=new_value)
                self.treeview_selected = "/".join(self.treeview_selected.split("/")[:-1])+"/"+new_value
            elif column == 1:  # Sample column
                try:
                    self.wrapper.update_property(name = "MEASURE.Sample", value = new_value, path=self.treeview_selected)
                except WrapperError_ArgumentType as e:
                    apply_all = qtw.QMessageBox.question(self, "Apply to all sub-groups?", f"Do you want to apply this change to all the sub-elements of the selected group?", qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
                    if apply_all == qtw.QMessageBox.Yes:
                        self.wrapper.update_property(name = "MEASURE.Sample", value = new_value, path=self.treeview_selected, apply_to_all = True)
                    elif apply_all == qtw.QMessageBox.Cancel:
                        return
                    else:
                        self.wrapper.update_property(name = "MEASURE.Sample", value = new_value, path=self.treeview_selected, apply_to_all=False)
            elif column == 2:  # Date column
                try:
                    self.wrapper.update_property(name = "MEASURE.Date_of_measure", value = new_value, path=self.treeview_selected)
                except WrapperError_ArgumentType as e:
                    apply_all = qtw.QMessageBox.question(self, "Apply to all sub-groups?", f"Do you want to apply this change to all the sub-elements of the selected group?", qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
                    if apply_all == qtw.QMessageBox.Yes:
                        self.wrapper.update_property(name = "MEASURE.Date_of_measure", value = new_value, path=self.treeview_selected, apply_to_all = True)
                    elif apply_all == qtw.QMessageBox.Cancel:
                        return
                    else:
                        self.wrapper.update_property(name = "MEASURE.Date_of_measure", value = new_value, path=self.treeview_selected, apply_to_all=False)

            self.update_treeview()
            self.expand_treeview_path(self.treeview_selected)
            self.update_parameters()

    @qtc.Slot()
    def treeview_handle_drops_files(self, filepaths, parent_path):
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
        # Start by making sure that file having only one kind of extension are added.
        temp = [os.path.splitext(filepath)[1] for filepath in filepaths]
        extensions = []
        for e in temp:
            if not e in extensions: extensions.append(e)
        # If more than one extension is found in the file, raise a warning and return
        if len(extensions) > 1:
            qtw.QMessageBox.warning(self, "Warning", "Files with different extensions were selected. Please select any number of only one file type.")
            return

        # If only one extension is found we add the files
        elif len(extensions) == 1:
            # If we are dealing with HDF5 files, we first clarify if we want to add the data to the opened file or create a new one
            if extensions[0] in [".hdf5", ".h5"]:
                # If the opened file is empty, we open the selected HDF5 file
                if len(self.wrapper.get_children_elements()) == 0:
                    if len(filepaths) == 1:
                        self.open_hdf5(filepath = filepaths[0])
                    else:
                        self.wrapper.add_hdf5(filepath = filepaths[0], parent_group = self.treeview_selected)
                else:
                    dialog = qtw.QMessageBox.question(self, "Precisions", "Do you want to add the data to the opened file (Yes) or create a new one (No)?", qtw.QMessageBox.Yes | qtw.QMessageBox.No | qtw.QMessageBox.Cancel)
                    if dialog == qtw.QMessageBox.No: # The user wants to create a new file
                        try: # If the file hasn't been saved, an error is raised
                            self.wrapper.close()
                        except WrapperError_Save:
                            if not self.handle_error_save(): 
                                return # If the user decides to cancel his action at this point, the function ends
                        self.wrapper = wrapper.Wrapper(filepaths[0])
                        self.treeview_selected = "Brillouin"
                    elif dialog == qtw.QMessageBox.Cancel:
                        return
                for filepath in filepaths[1:]:
                    self.wrapper.add_hdf5(filepath = filepath, parent_group = self.treeview_selected)
                self.update_treeview()
                self.update_parameters()
                self.expand_treeview_path(self.treeview_selected)
            else:
                self.add_data(filepath = filepaths, parent_path = parent_path)

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
    def update_graph(self):
        """Update the graph based on the selected treatment and selected plots.

        Returns
        -------
        None
        """
        def plot(treatment, element, cols, lines):
            def plot_2D(image, max_col, max_line, pos, title):
                ax = self.figure.add_subplot(max_line, max_col, pos)
                ax.imshow(image)
                ax.text(0.01, 0.99, title, transform=ax.transAxes, fontsize=6, fontname='Arial', color='white', verticalalignment='top', horizontalalignment='left')
                ax.set_xticks([])
                ax.set_yticks([])
            
            # Get the correspondance between the type of elements to plot and the indexes in cols and lines
            plots_correspondance = ["Shift", "Linewidth", "BLT", "Amplitude", "Shift Variance", "Linewidth Variance", "BLT Variance", "Amplitude Variance"]
            indexes_correspondance = [[0,0],[1,0],[2,0],[3,0],[0,1],[1,1],[2,1],[3,1]]

            # Get the position of the plot
            index = indexes_correspondance[plots_correspondance.index(element)]
            col = cols[index[0]]
            line = lines[index[1]]
 
            # Extract the maximum column and line and deduce the position of the subplot
            max_col, max_line = 0, 0
            for c in cols:
                if c is not None and c > max_col: max_col = c
            for l in lines: 
                if l is not None and l > max_line: max_line = l

            pos = max_col*(line-1) + col

            # Extract the element to plot
            parent_path = self.treeview_selected + "/" + treatment
            childs = self.wrapper.get_children_elements(parent_path)

            # Adjust the value selected in the combobox to the Brillouin type of the element
            if " Variance" in element: 
                element = element.replace(" Variance", "_std")
            elif "Loss Tangent" in element:
                element = element.replace("Loss Tangent", "BLT")

            # Goes through the children elements of the selected group and plot the one with the correct type
            for child in childs:
                if self.wrapper.get_type(path=f"{parent_path}/{child}", return_Brillouin_type=True) == element:
                    # Extract the element
                    elt = self.wrapper[f"{parent_path}/{child}"]

                    # Reshape the element to avoid singleton dimensions
                    new_shape = []
                    for s in elt.shape:
                        if s > 1: new_shape.append(s)
                    elt = elt.reshape(new_shape)

                    # Store the name of the element
                    title = child

                    # Plot the element depending on its shape
                    if len(elt.shape) == 2:
                        plot_2D(elt, max_col, max_line, pos, title)
                    else:
                        qtw.QMessageBox.warning(self, "Warning", "Only 2D plots are supported for now")
                    self.canvas.draw()
                    break

        # Clear the canvas
        self.figure.clear()

        # Get the existing treatment at the selected path and sets it to the self.cb_Treatment combobox
        treatment = self.cb_Treatment.currentText()
        selected_plots = self.cb_SelectionPlots.currentData()

        # Get the number of plots ond their position from the selected plots.
        col_Shift, col_Linewidth, col_Amplitude, col_BLT = 0,0,0,0
        line_Plain, line_Variance = 0, 0
        for k in selected_plots:
            if "Shift" in k: col_Shift = 1
            elif "Linewidth" in k: col_Linewidth = 1
            elif "BLT" in k: col_BLT = 1
            elif "Amplitude" in k: col_Amplitude = 1

            if "Variance" in k: line_Variance = 1
            else: line_Plain = 1

        nb_lines = line_Plain + line_Variance
        nb_cols = col_Shift + col_Linewidth + col_Amplitude + col_BLT

        # Assign columns and lines in the subplots to the 8 possible plots
        count = 0
        cols, lines = [], []
        for col in [col_Shift, col_Linewidth, col_BLT, col_Amplitude]:
            if col == 1: 
                count+=1
                cols.append(count)
            else: cols.append(None)
        count = 0
        for line in line_Plain, line_Variance:
            if line == 1: 
                count+=1
                lines.append(count)
            else: lines.append(None)

        # Plot the selected plots
        for e in selected_plots:
            plot(treatment, e, cols, lines)

    @qtc.Slot()
    def update_parameters(self, filepath=None, delete_child_attributes = False):
        """
        Update the parameters based on the selected tree view element.

        Parameters
        ----------
        filepath : str, optional                         
            The path to the CSV file containing the properties to update. If None, the properties of the selected element are updated based on the reference CSV parameter file.
        delete_child_attributes : bool, optional
            If True, all the attributes of the children elements with same name as the ones to be updated are deleted. Default is False.

        Returns
        -------
        None
        """
        def update_graph():
            def activate_all(state = False):
                self.b_Parameters.setEnabled(state)
                self.cb_Treatment.setEnabled(state)
                self.cb_SelectionPlots.setEnabled(state)
                self.tab_Visualize.setEnabled(state)

            # Clear the canvas
            self.figure.clear()

            # Verify that the selected element can have a treatment group
            parent_path = self.treeview_selected

            # If the parent is the root, no treatment can be observed as by default measures are stored in groups under the root
            if parent_path == "Brillouin": 
                activate_all(state = False)
                return
            
            # If the parent is a group, check it is either a treatment or a measure group
            if self.wrapper.get_type(path=parent_path) == h5py._hl.group.Group:
                if self.wrapper.get_type(path=parent_path, return_Brillouin_type = True) == "Measure": 
                    pass
                elif self.wrapper.get_type(path=parent_path, return_Brillouin_type = True) == "Treatment": 
                    pass
                else: 
                    activate_all(state = False)
                    return
                
            # Treatments are stored in groups under measure groups, therefore we make sure the parent group is a measure group
            while self.wrapper.get_type(path=parent_path, return_Brillouin_type = True) != "Measure":
                parent_path = "/".join(parent_path.split("/")[:-1])

            # And then we can extract the different treatments that have been stored in the parent group
            treatments = self.wrapper.get_children_elements(parent_path, Brillouin_type="Treatment")
            self.cb_Treatment.clear()

            # If no treatment exist, disable the combobox and the plots
            if len(treatments) == 0:
                activate_all(state = False)
                return

            # Activate the combobox and the plots
            activate_all(state = True)

            # Add the treatments to the combobox
            self.cb_Treatment.addItems(treatments)

            # Update the graph
            self.update_graph()

        # If no filepath was given, take the file corresponding to the specified version of the library, make sure no overwrite is allowed.
        if filepath is None: 
            import_file = False
            filepath = "/".join(os.path.abspath(__file__).split("/")[:-3]) + f"/spreadsheets/attributes_v{wrapper.HDF5_BLS_Version}.xlsx"
            overwrite = False
        # If the filepath is given, ask the user if they want to update the properties of the wrapper
        else:
            import_file = True
            overwrite = qtw.QMessageBox.question(self, "Update properties", "Do you want to overwrite the properties of the wrapper with the properties stored in the file?")
            overwrite = True if overwrite == qtw.QMessageBox.Yes else False

        # Update the attributes of the file with the properties from the file
        if self.wrapper.get_type(self.treeview_selected) != h5py._hl.group.Group:
            path = "/".join(self.treeview_selected.split("/")[:-1])
        else: 
            path = self.treeview_selected
        self.wrapper.import_properties_data(filepath = filepath, path = path, overwrite = overwrite, delete_child_attributes = delete_child_attributes)

        # Extract the attributes of the element selected
        attr = self.wrapper.get_attributes(self.treeview_selected)

        # Update the tables associated to the measure and spectrometer
        self.model_table_Measure.clear()
        self.model_table_Spectrometer.clear()
        self.model_table_Other.clear()
        self.model_table_Measure.setHorizontalHeaderLabels(["Parameter", "Value", "Units"])
        self.model_table_Spectrometer.setHorizontalHeaderLabels(["Parameter", "Value", "Units"])
        self.model_table_Other.setHorizontalHeaderLabels(["Parameter", "Value", "Units"])

        for k, v in attr.items():
            try:
                if "." in k:
                    cat, name = k.split(".")
                    name = name.split("_")
                    if name[-1][0] == "(" and name[-1][-1] == ")": unit = name.pop(-1)[1:-1]
                    else: unit = ""
                    if cat == "MEASURE":
                        self.model_table_Measure.appendRow([qtg.QStandardItem(" ".join(name)), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
                    elif cat == "SPECTROMETER":
                        self.model_table_Spectrometer.appendRow([qtg.QStandardItem(" ".join(name)), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
                    else:
                        if len(v)>100: v = v[:100]+"..."
                        self.model_table_Other.appendRow([qtg.QStandardItem(" ".join(k.split("_"))), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
                else:
                    if len(v)>100: v = v[:100]+"..."
                    self.model_table_Other.appendRow([qtg.QStandardItem(" ".join(k.split("_"))), qtg.QStandardItem(v), qtg.QStandardItem(unit)])
            except:
                pass
        
        self.tableView_Measure.setModel(self.model_table_Measure)    
        self.tableView_Spectrometer.setModel(self.model_table_Spectrometer)
        self.tableView_Other.setModel(self.model_table_Other)

        self.textBrowser_Log.append(f"Parameters of <b>{self.treeview_selected}</b> have been updated")

        update_graph()

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
                else: 
                    attr[k] = v
            return attr

        def create_parameter_dictionnary_from_table_view(self):
            measure_params = self.read_table_view(self.tableView_Measure)
            spectrometer_params = self.read_table_view(self.tableView_Spectrometer)

            attr = {}
            for k, v in measure_params.items():
                if ")" in k: new_key = "MEASURE." + "_".join(k.split(" ")) + "_()"
                else: new_key = "MEASURE." + "_".join(k.split(" "))

                if v[1] != "":
                    if new_key.endswith("_()"):  new_key =  f"{new_key[:-3]}_({v[1]})"
                    else: new_key =  f"{new_key}_({v[1]})"
                attr[new_key] = v[0]

            for k, v in spectrometer_params.items():
                new_key = "SPECTROMETER." + "_".join(k.split(" "))
                if v[1] != "": 
                    new_key =  f"{new_key}_({v[1]})"
                attr[new_key] = v[0]
            
            return attr

        # Get the parameters of the table view and of the wrapper
        attr_table = create_parameter_dictionnary_from_table_view(self)
        attr_wrapper = self.wrapper.get_attributes(path=self.treeview_selected)

        # Compare the two dictionaries
        attr_changed = compare_dictionnaries(attr_table, attr_wrapper)

        # Update the wrapper attributes to have all the attributes of the specified version
        for k, v in attr_changed.items():
            if self.wrapper.get_type(path=self.treeview_selected) == h5py._hl.group.Group:
                path = self.treeview_selected
            else: 
                path = "/".join(self.treeview_selected.split("/")[:-1])
            self.wrapper.update_property(name = k, value = v, path = path)
        
        self.update_parameters()
        self.update_treeview()
        self.expand_treeview_path(self.treeview_selected)

        self.textBrowser_Log.append(f"Parameters of <b>{self.treeview_selected}</b> have been updated")

    @qtc.Slot()
    def update_treeview(self):     
        """
        Update the tree view with the current wrapper.
        """
        def add_child(element, parent, path):
            item_path = f"{path}/{element}"
            attributes = self.wrapper.get_attributes(path = item_path)
            name, date, sample = element, '', ''
            if "MEASURE.Date_of_measure" in attributes.keys(): date = attributes["MEASURE.Date_of_measure"]
            if "MEASURE.Sample" in attributes.keys(): sample = attributes["MEASURE.Sample"]
            if "Brillouin_type" in attributes.keys(): brillouin_type = attributes["Brillouin_type"]
            item = qtg.QStandardItem(name)
            item.setData(item_path, qtc.Qt.UserRole)
            set_icon_brillouin_type(item, brillouin_type) # Set an icon for the item

            if self.wrapper.get_type(path=item_path) == h5py._hl.group.Group:
                for e in self.wrapper.get_children_elements(path = item_path):
                    add_child(e, item, item_path)
            parent.appendRow([item, qtg.QStandardItem(sample), qtg.QStandardItem(date)])

        def set_icon_brillouin_type(item, brillouin_type):
            directory = "/".join(current_dir.split("/")[:-1]) + "/icon"
            if "Abscissa" in brillouin_type: 
                item.setIcon(qtg.QIcon(f"{directory}/Abscissa.png"))
            if brillouin_type == "Amplitude":
                item.setIcon(qtg.QIcon(f"{directory}/Amplitude.png"))
            if brillouin_type == "Amplitude_std": 
                item.setIcon(qtg.QIcon(f"{directory}/Amplitude_error.png"))
            if brillouin_type == "BLT":
                item.setIcon(qtg.QIcon(f"{directory}/BLT.png"))
            if brillouin_type == "BLT_std": 
                item.setIcon(qtg.QIcon(f"{directory}/BLT_error.png"))
            elif brillouin_type == "Frequency": 
                item.setIcon(qtg.QIcon(f"{directory}/Frequency.png"))
            elif brillouin_type == "Linewidth_std": 
                item.setIcon(qtg.QIcon(f"{directory}/Gamma_error.png"))
            elif brillouin_type == "Linewidth": 
                item.setIcon(qtg.QIcon(f"{directory}/Gamma.png")) 
            elif brillouin_type == "PSD": 
                item.setIcon(qtg.QIcon(f"{directory}/PSD.png"))    
            elif brillouin_type == "Raw_data": 
                item.setIcon(qtg.QIcon(f"{directory}/Raw_data.png")) 
            elif brillouin_type == "Shift_std": 
                item.setIcon(qtg.QIcon(f"{directory}/Nu_error.png"))  
            elif brillouin_type == "Shift": 
                item.setIcon(qtg.QIcon(f"{directory}/Nu.png"))  

            elif brillouin_type == "Calibration_spectrum": 
                item.setIcon(qtg.QIcon(f"{directory}/Calibration.png"))  
            elif brillouin_type == "Impulse_response": 
                item.setIcon(qtg.QIcon(f"{directory}/Impulse_response.png"))  
            elif brillouin_type == "Measure": 
                item.setIcon(qtg.QIcon(f"{directory}/Measure.png"))   
            elif brillouin_type == "Root": 
                item.setIcon(qtg.QIcon(f"{directory}/Root.png"))   
            elif brillouin_type == "Treatment": 
                item.setIcon(qtg.QIcon(f"{directory}/Treatment.png"))  
        
        # Retrieve the current column widths from the existing model
        column_widths = []
        if self.treeView.model() is not None:
            for column in range(self.treeView.model().columnCount()):
                column_widths.append(self.treeView.columnWidth(column))

        # Create a model with 3 columns
        self.model = MyStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Name", "Sample", "Date"])

        # Add first item
        name, date, sample = "Brillouin", "", ""
        if "MEASURE.Sample" in self.wrapper.get_attributes().keys(): sample = self.wrapper.get_attributes()["MEASURE.Sample"]
        if "MEASURE.Date_of_measure" in self.wrapper.get_attributes().keys(): date = self.wrapper.get_attributes()["MEASURE.Date_of_measure"]
        item = qtg.QStandardItem(name)
        item.setData("Brillouin", qtc.Qt.UserRole)
    
        # Add all other elements recursively
        for e in self.wrapper.get_children_elements(): 
            add_child(e, item, "Brillouin") 
        self.model.appendRow([item, qtg.QStandardItem(sample), qtg.QStandardItem(date)])

        # Set the model to the TreeView
        self.treeView.setModel(self.model)

        # Adjust column widths to fit the largest size encountered
        try:
            for column in range(self.treeView.model().columnCount()):
                self.treeView.setColumnWidth(column, column_widths[column])
        except:
            pass

        # When a data is changed in the treeview, the function treeview_element_changed is called
        self.model.dataChanged.connect(self.treeview_element_changed)

        # Collapse all items for visibility
        self.treeView.collapseAll()

        # Optional: Adjust column widths
        self.treeView.header().setStretchLastSection(False)
        self.treeView.header().setDefaultSectionSize(100)

        # Binds selected elements to the function treeview_element_selected
        self.treeView.selectionModel().selectionChanged.connect(self.treeview_element_selected)

        # Sets all dragged objects to the treeview to call self.add_data(filepath) where the filepath is the path of the dragged object
        self.treeView.setAcceptDrops(True)
        self.treeView.setDragEnabled(True)  # Optional: Allows dragging from TreeView
        self.treeView.setDragDropMode(qtw.QAbstractItemView.DragDrop)

        # Bind drag-and-drop event handlers
        self.treeView.dragEnterEvent = self.treeView_dragEnterEvent
        self.treeView.dragMoveEvent = self.treeView_dragMoveEvent
        self.treeView.dropEvent = self.treeView_dropEvent

        # Activate buttons
        self.activate_buttons()
        self.activate_menu()

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
