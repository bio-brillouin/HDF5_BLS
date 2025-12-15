from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import QAbstractItemDelegate, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QSpinBox, QStyle, QStyledItemDelegate, QTreeView, QVBoxLayout, QWidget, QDialogButtonBox
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from configparser import ConfigParser

from MessageBox_multiple_choice.main import MessageBoxMultipleChoice

import sys
import json
import inspect
from functools import partial
from HDF5_BLS.wrapper import Wrapper, HDF5_group, HDF5_dataset
from HDF5_BLS_treat import Treat, Models
import numpy as np
from pathlib import Path

class ParameterDelegate(QStyledItemDelegate):
    commitData = Signal(QWidget)
    closeEditor = Signal(QWidget, QAbstractItemDelegate.EndEditHint)

    def __init__(self, parent=None, graph_callback=None):
        super().__init__(parent)
        self.graph_callback = graph_callback  # Function to call when graph picking is needed

    def createEditor(self, parent, option, index):
        editor_type = index.data(Qt.UserRole + 1)
        choices = index.data(Qt.UserRole + 2)
        item = index.model().itemFromIndex(index)
        if editor_type == "position_graph":
            label = QLabel(parent)
            label.setText("click on graph")
            label.setStyleSheet("color: white;")  # <-- Add this line
            if self.graph_callback:
                self.graph_callback(index, label)
            return label
        elif editor_type in ("type_combo", "center_combo", "model_combo") and choices:
            combo = QComboBox(parent)
            combo.addItems(choices)
            return combo
        elif editor_type == "bool":
            item.setData("", Qt.DisplayRole)  # Clear text display for checkbox
            checkbox = QCheckBox(parent)
            checkbox.setChecked(choices)
            return checkbox
        else:
            return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        editor_type = index.data(Qt.UserRole + 1)
        if editor_type == "position_graph":
            editor.setText("click on graph")
        elif editor_type in ("type_combo", "center_combo", "model_combo"):
            value = index.model().data(index, Qt.EditRole)
            i = editor.findText(value)
            if i >= 0:
                editor.setCurrentIndex(i)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        editor_type = index.data(Qt.UserRole + 1)
        if editor_type == "position_graph":
            # The graph callback should update the model when the graph is clicked
            pass
        elif editor_type in ("type_combo", "center_combo", "model_combo"):
            model.setData(index, editor.currentText(), Qt.EditRole)
        else:
            super().setModelData(editor, model, index)

    def paint(self, painter, option, index):
        editor_type = index.data(Qt.UserRole + 1)
        if editor_type == "position_graph":
            option.text = index.model().data(index, Qt.DisplayRole) if index.model().data(index, Qt.DisplayRole) != "click on graph" else ""
            QApplication.style().drawControl(QStyle.CE_ItemViewItem, option, painter)
        else:
            super().paint(painter, option, index)

class CustomTreeView(QTreeView):
    def __init__(self, *args, on_edit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_edit = on_edit

    def edit(self, index, trigger, event):
        if self._on_edit:
            self._on_edit(index)
        return super().edit(index, trigger, event)

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

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent = None, width = 5, height = 4, dpi = 100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class DataProcessingWindow_Analyse(QDialog):
    def __init__(self, wrapper_instance: Wrapper, elements:list, processing_object, parent=None, *kwargs):
        super().__init__(parent)

        self.gui_root = str(Path(__file__).resolve().parent.parent.parent)

        # Load config file
        self.config = ConfigParser()
        self.config.read(f"{self.gui_root}/src/DataProcessing/config_Main.ini")

        # Set window title and geometry
        self.setWindowTitle("Data Processing Window")
        self.setGeometry(self.config["Geometry"].getint("x"),
                         self.config["Geometry"].getint("y"),
                         self.config["Geometry"].getint("width"),
                         self.config["Geometry"].getint("height"))

        # Store the wrapper instance and the chosen elements to process
        self.wrp = wrapper_instance
        self.elements = elements

        # Initialize the first element to display
        self.current_element_index = 0
        self.current_element = self.wrp[self.elements[self.current_element_index]]
        self.processing_object = processing_object
        self.abscissa_name = ""

        # Initialize the left frame (graph, selection of curves)
        self._initialize_left_frame()

        # Initialize the right frame (graph, selection of curves)
        self._initialize_right_frame()

        # Initialize the button box
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Set the layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.left_widget, 0, 0)
        self.layout.addWidget(self.right_widget, 0, 1)
        self.layout.addWidget(self.buttonBox, 1, 0, 1, 2)
        self.setLayout(self.layout)

        # Set window modality
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Plot the first element in default configuration (average of all axis minus last one)
        self.plot_spectrum()

    def _initialize_left_frame(self):
        """Initializes the left frame (graph, selection of curves)
        """
        # Create the buttons to choose wether to plot single curves or the average of all the curves
        self.b_previous_element = QPushButton(icon = QIcon(f"{self.gui_root}/assets/img/left_arrow.svg"), toolTip="Previous element")
        self.b_previous_element.clicked.connect(self.previous_element)
        self.b_previous_element.setEnabled(False)
        self.b_plot_single = QPushButton("Plot single curves")
        self.b_plot_single.clicked.connect(self.plot_single)
        if len(self.current_element.shape) == 1:
            self.b_plot_single.setEnabled(False)
        self.b_plot_average = QPushButton("Plot average of all curves")
        self.b_plot_average.setEnabled(False)
        self.b_plot_average.clicked.connect(self.plot_average)
        self.b_next_element = QPushButton(icon = QIcon(f"{self.gui_root}/assets/img/right_arrow.svg"), toolTip="Next element")
        self.b_next_element.clicked.connect(self.next_element)
        if len(self.elements) == 1:
            self.b_next_element.setEnabled(False)

        # Create the layout for the buttons
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.b_previous_element)
        self.buttons_layout.addWidget(self.b_plot_single)
        self.buttons_layout.addWidget(self.b_plot_average)
        self.buttons_layout.addWidget(self.b_next_element)

        # Create the spinboxes to select the dimensions to plot in case of single curves and add them to a layout
        self.dimension_layout = QHBoxLayout()
        self.l_dimensions = QLabel("Plotting spectrum index:")
        self.dimension_layout.addWidget(self.l_dimensions)
        self.dimension_spinboxes = []
        for i in range(len(self.current_element.shape)-1):
            self.dimension_spinboxes.append(QSpinBox())
            self.dimension_spinboxes[-1].setRange(0, self.current_element.shape[i]-1)
            self.dimension_spinboxes[-1].setValue(0)
            self.dimension_spinboxes[-1].setSingleStep(1)
            self.dimension_spinboxes[-1].setFixedWidth(50)
            self.dimension_spinboxes[-1].setToolTip(f"Dimension {i+1}")
            self.dimension_spinboxes[-1].setEnabled(False)
            self.dimension_spinboxes[-1].valueChanged.connect(self.plot_single)
            self.dimension_layout.addWidget(self.dimension_spinboxes[-1])

        # Create the graph
        self.graph_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.graph_toolbar = NavigationToolbar(self.graph_canvas, self)

        # Initialize the points and windows plotted
        self.points_plotted = None
        self.windows_plotted = None

        # Initialize a storing array for the x axis
        self.x_axis = None
        self.y_axis = None

        # Set the layout
        self.left_widget = QWidget()
        left_frame = QVBoxLayout(self.left_widget)
        left_frame.addLayout(self.buttons_layout)
        left_frame.addLayout(self.dimension_layout)
        left_frame.addWidget(self.graph_toolbar)
        left_frame.addWidget(self.graph_canvas)
        self.left_widget.setLayout(left_frame)

    def _initialize_right_frame(self):
        """Initializes the right frame (graph, selection of curves)
        """
        self.l_titleAlgorithm = QLabel("Blank algorithm", alignment=Qt.AlignCenter)

        self.b_algo_graph = QPushButton("Display algorithm graph")
        self.b_algo_graph.clicked.connect(self.display_algo_graph)
        self.b_algo_graph.setEnabled(False)
        self.b_open_algo = QPushButton("Open algorithm")
        self.b_open_algo.clicked.connect(self.open_algo)
        self.b_create_new_algo = QPushButton("Create new algorithm")
        self.b_create_new_algo.clicked.connect(self.new_algo)
        self.b_save_algo = QPushButton("Save algorithm")
        self.b_save_algo.setEnabled(False)
        self.b_save_algo.clicked.connect(self.save_algo)

        # Create the treeview to display the algorithm
        self.algorithm_treeview = CustomTreeView(on_edit=self.on_treeview_edit)
        self.algorithm_treeview.setSelectionMode(QTreeView.SingleSelection)

        # Connect the menu to the treeview
        self.algorithm_treeview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.algorithm_treeview.customContextMenuRequested.connect(self.treeview_context_menu)
        
        # Make the value column enter edit mode on single click
        self.algorithm_treeview.setEditTriggers(QTreeView.EditTrigger.SelectedClicked | QTreeView.EditTrigger.CurrentChanged)
        self.parameter_delegate = ParameterDelegate(self, graph_callback=self.start_graph_pick)
        self.algorithm_treeview.setItemDelegateForColumn(1, self.parameter_delegate)
        
        # Create the model displayed in the treeview
        self.algorithm_model = TreeviewItemModel()

        # Set the model of the treeview
        self.algorithm_treeview.setModel(self.algorithm_model)
        # Connect model dataChanged signal to handler (must be after setModel)
        self.algorithm_model.dataChanged.connect(self.on_treeview_changed)

        # Connect selection change to custom handler
        selection_model = self.algorithm_treeview.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.on_element_selected)
        
        # Set two columns for the treeview with names "function" and "parameters"
        self.algorithm_model.setHorizontalHeaderLabels(["Parameters", "Values"])

        # Set the layout
        self.right_widget = QWidget()
        right_layout = QGridLayout(self.right_widget)
        right_layout.addWidget(self.l_titleAlgorithm, 0, 0, 1, 2)
        right_layout.addWidget(self.b_algo_graph, 1, 0, 1, 2)
        right_layout.addWidget(self.b_open_algo, 2, 0, 1, 1)
        right_layout.addWidget(self.b_create_new_algo, 2, 1, 1, 1)
        right_layout.addWidget(self.algorithm_treeview, 3, 0, 1, 2)
        right_layout.addWidget(self.b_save_algo, 4, 0, 1, 2)
        self.right_widget.setLayout(right_layout)

    # Button behaviour
    
    def display_algo_graph(self):
        """Displays the graph of the selected algorithm.
        """
        QMessageBox.information(self, "Not implemented", "To do")

    def next_element(self):
        """Go to the previous element in the list of elements.
        """
        if self.current_element_index == len(self.elements)-2:
            self.b_next_element.setEnabled(False)
        self.b_previous_element.setEnabled(True)
        self.current_element_index += 1
        self.current_element = self.wrp[self.elements[self.current_element_index]]
        if self.b_plot_average.isEnabled():
            self.plot_single()
        else:
            self.plot_average()

    def new_algo(self):
        """Creates a new algorithm.
        """
        QMessageBox.information(self, "Not implemented", "To do")

    def open_algo(self):
        """Opens an algorithm.
        """
        filepath = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json)")[0]
        if filepath:
            # Clear the algorithm treeview
            self.algorithm_model.clear()
            self.algorithm_model.setRowCount(0)
            self.algorithm_model.setColumnCount(2)
            self.algorithm_model.setHorizontalHeaderLabels(["Parameters", "Values"])

            # Activate the buttons
            self.b_algo_graph.setEnabled(True)
            self.b_save_algo.setEnabled(True)

            # Open the algorithm in the backend object
            self.processing_object.silent_open_algorithm(filepath)

            # Update the title of the algorithm
            name_algo = self.processing_object._algorithm["name"]
            self.l_titleAlgorithm.setText(f"{name_algo}")

            # Fill the treeview with the functions of the algorithm
            for nb, f in enumerate(self.processing_object._algorithm["functions"]):
                # Create a new row for the function
                function = QStandardItem(f["function"])
                function.setData(f["function"], Qt.UserRole)
                function.setFlags(function.flags() & ~Qt.ItemIsEditable)

                # Set the tooltip with line breaks
                description = f.get("description", "")
                words = description.split(" ")
                formatted_description = ""
                current_length = 0
                for word in words:
                    if "\n" in word:
                        formatted_description += word
                        current_length = 0
                    elif current_length + len(word) + 1 > 100:
                        formatted_description += "\n" + word
                        current_length = len(word)
                    else:
                        formatted_description += " " + word
                        current_length += len(word) + 1
                function.setToolTip(formatted_description.strip())

                # Adds all the parameters and values as children of the function
                for k, v in f["parameters"].items():
                    parameter, value = self.add_parameter(nb, k, v)
                    function.appendRow([parameter, value])

                # Add the function to the model
                self.algorithm_model.appendRow([function])
        else:
            return

    def previous_element(self):
        """Go to the previous element in the list of elements.
        """
        if self.current_element_index == 1:
            self.b_previous_element.setEnabled(False)
        self.b_next_element.setEnabled(True)
        self.current_element_index -= 1
        self.current_element = self.wrp[self.elements[self.current_element_index]]
        if self.b_plot_average.isEnabled():
            self.plot_single()
        else:
            self.plot_average()
    
    def save_algo(self):
        """Saves the algorithm.
        """
        # Get filename to save the JSON algorithm at
        filepath = QFileDialog.getSaveFileName(self, "Open File", "", "JSON Files (*.json)")[0]
        
        # Ask the user wether to save parameter values with the algorithm or not
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Question)
        dialog.setWindowTitle('Save parameters')
        dialog.setText('Do you want to save the values given to the parameters in the JSON file storing the algorithm?')
        dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
        buttonY = dialog.button(QMessageBox.Yes)
        buttonY.setText('Save parameters')
        buttonN = dialog.button(QMessageBox.No)
        buttonN.setText("Don't save parameters")
        dialog.exec_()
        
        # The user wants to add the data to the opened file
        if dialog.clickedButton() == buttonY: 
            save_parameters = True

        # The user wants to create a new file
        elif dialog.clickedButton() == buttonN: 
            save_parameters = False

        self.processing_object.silent_save_algorithm(filepath = filepath, save_parameters = save_parameters)

    # Function interaction
    
    def add_before(self):
        """Add a function before the selected function.
        """
        # Ask the user to choose a function
        functions = [function[0] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        executables = [function[1] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        choice, state = MessageBoxMultipleChoice.get_choice(text = "Choose a function to add before", list_choice = functions, parent = self)
        if state == "cancel": return

        # Get the selected index
        selected_index = self.algorithm_treeview.selectionModel().currentIndex()

        # Get its parent and row
        parent_index = selected_index.parent()
        row = selected_index.row()

        # Get the algorithm step to add
        function = executables[functions.index(choice)]
        function() 
        algo_step = self.processing_object._algorithm["functions"].pop()

        # Add the algorithm step to the algorithm at the right position
        self.processing_object._algorithm["functions"].insert(row, algo_step)

        # Add the function to the model
        function = QStandardItem(algo_step["function"])
        function.setData(algo_step["function"], Qt.UserRole)
        function.setFlags(function.flags() & ~Qt.ItemIsEditable)

        # Set the tooltip with line breaks
        description = algo_step["description"]
        words = description.split(" ")
        formatted_description = ""
        current_length = 0
        for word in words:
            if "\n" in word:
                formatted_description += word
                current_length = 0
            elif current_length + len(word) + 1 > 100:
                formatted_description += "\n" + word
                current_length = len(word)
            else:
                formatted_description += " " + word
                current_length += len(word) + 1
        function.setToolTip(formatted_description.strip())

        # Adds all the parameters and values as children of the function
        for k, v in algo_step["parameters"].items():
            parameter, value = self.add_parameter(row, k, v)
            function.appendRow([parameter, value])

        # Add the function to the model
        self.algorithm_model.insertRow(row, function)

        # Select the new function and expand it
        self.algorithm_treeview.setCurrentIndex(function.index())
        self.algorithm_treeview.expand(function.index())

    def add_after(self):
        """Add a function after the selected function.
        """
        # Ask the user to choose a function
        functions = [function[0] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        executables = [function[1] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        choice, state = MessageBoxMultipleChoice.get_choice(text = "Choose a function to add before", list_choice = functions, parent = self)
        if state == "cancel": return

        # Get the selected index
        selected_index = self.algorithm_treeview.selectionModel().currentIndex()

        # Get its parent and row
        parent_index = selected_index.parent()
        row = selected_index.row() + 1

        # Get the algorithm step to add
        function = executables[functions.index(choice)]
        function() 
        algo_step = self.processing_object._algorithm["functions"].pop()

        # Add the algorithm step to the algorithm at the right position
        self.processing_object._algorithm["functions"].insert(row, algo_step)

        # Add the function to the model
        function = QStandardItem(algo_step["function"])
        function.setData(algo_step["function"], Qt.UserRole)
        function.setFlags(function.flags() & ~Qt.ItemIsEditable)

        # Set the tooltip with line breaks
        description = algo_step["description"]
        words = description.split(" ")
        formatted_description = ""
        current_length = 0
        for word in words:
            if "\n" in word:
                formatted_description += word
                current_length = 0
            elif current_length + len(word) + 1 > 100:
                formatted_description += "\n" + word
                current_length = len(word)
            else:
                formatted_description += " " + word
                current_length += len(word) + 1
        function.setToolTip(formatted_description.strip())

        # Adds all the parameters and values as children of the function
        for k, v in algo_step["parameters"].items():
            parameter, value = self.add_parameter(row, k, v)
            function.appendRow([parameter, value])

        # Add the function to the model
        self.algorithm_model.insertRow(row, function)

        # Select the new function and expand it
        self.algorithm_treeview.setCurrentIndex(function.index())
        self.algorithm_treeview.expand(function.index())

    def delete(self):
        """Delete the selected function.
        """
        # Get the selected index
        selected_index = self.algorithm_treeview.selectionModel().currentIndex()

        # Get its parent and row
        parent_index = selected_index.parent()
        row = selected_index.row()

        # Remove the step from the algorithm
        self.processing_object.silent_remove_step(step = row)

        # Remove the step from the model
        self.algorithm_model.removeRow(row, parent_index)


    def load_algorithm(self, name_attribute_algorithm : str = None):
        """Load the algorithm from the wrapper.

        Parameters
        ----------
        name_attribute_algorithm : str, optional
            The name of the attribute that contains the algorithm to load. If None, no algorithm is loaded.
        """
        if name_attribute_algorithm is None:
            return
        
        else:
            if name_attribute_algorithm in self.wrp.get_attributes(path=self.elements[self.current_element_index]).keys():
                # Get the algorithm and sets it to the processing object
                str_algorithm = self.wrp.get_attributes(path=self.elements[self.current_element_index])[name_attribute_algorithm]
                self.processing_object.silent_open_algorithm(filepath = None, algorithm_str = str_algorithm)

                
                # Update the title of the algorithm
                name_algo = self.processing_object._algorithm["name"]
                self.l_titleAlgorithm.setText(f"{name_algo}")

                # Fill the treeview with the functions of the algorithm
                for nb, f in enumerate(self.processing_object._algorithm["functions"]):
                    # Create a new row for the function
                    function = QStandardItem(f["function"])
                    function.setData(f["function"], Qt.UserRole)
                    function.setFlags(function.flags() & ~Qt.ItemIsEditable)

                    # Set the tooltip with line breaks
                    description = f.get("description", "")
                    words = description.split(" ")
                    formatted_description = ""
                    current_length = 0
                    for word in words:
                        if "\n" in word:
                            formatted_description += word
                            current_length = 0
                        elif current_length + len(word) + 1 > 100:
                            formatted_description += "\n" + word
                            current_length = len(word)
                        else:
                            formatted_description += " " + word
                            current_length += len(word) + 1
                    function.setToolTip(formatted_description.strip())

                    # Adds all the parameters and values as children of the function
                    for k, v in f["parameters"].items():
                        parameter, value = self.add_parameter(nb, k, v)
                        function.appendRow([parameter, value])

                    # Add the function to the model
                    self.algorithm_model.appendRow([function])
            self.b_save_algo.setEnabled(True)

    # Treeview interaction

    def add_parameter(self, function_nb, parameter_key, parameter_value):
        """Add a parameter to the treeview.

        Parameters
        ----------
        function_nb : int
            The number of the function.
        parameter_key : str
            The key of the parameter.
        parameter_value : str
            The default value of the parameter.

        Returns
        -------
        QStandardItem
            The parameter item.
        QStandardItem
            The value item.
        """
        parameter = QStandardItem(parameter_key)
        parameter.setData(f"{function_nb} - {parameter_key}", Qt.UserRole)
        # Make parameter name (column 0) non-editable
        parameter.setFlags(parameter.flags() & ~Qt.ItemIsEditable)
        if type(parameter_value) is float:
            value = QStandardItem(f"{parameter_value:.3f}")
        else:
            value = QStandardItem(str(parameter_value))
        if parameter_key.startswith("position"):
            value.setData("position_graph", Qt.UserRole + 1)
        elif parameter_key.startswith("type"):
            value.setData("type_combo", Qt.UserRole + 1)
            value.setData(["Elastic", "Stokes", "Anti-Stokes"], Qt.UserRole + 2)
        elif parameter_key.startswith("center"):
            value.setData("center_combo", Qt.UserRole + 1)
            value.setData(["Elastic", "Inelastic"], Qt.UserRole + 2)
        else:
            value.setData("default", Qt.UserRole + 1)
        return parameter, value

    def on_treeview_changed(self, topLeft, bottomRight, roles=None):
        """Called when the data in the treeview is changed.
        """
        function_nb = topLeft.parent().row()
        if function_nb == -1: return
        name_parameter = list(self.processing_object._algorithm["functions"][function_nb]["parameters"].keys())[topLeft.row()]
        
        new_value = topLeft.model().data(topLeft)

        if new_value == "click on graph":
            return
        
        # Try converting the new value to a float
        try:
            new_value = float(new_value)
        except:
            pass

        self.processing_object._algorithm["functions"][function_nb]["parameters"][name_parameter] = new_value
        self.processing_object.silent_run_algorithm(step=function_nb)
        
        self.plot_points()

    def on_treeview_edit(self, index, text = "click on graph"):
        editor_type = index.data(Qt.UserRole + 1)
        if editor_type == "position_graph":
            self.algorithm_model.setData(index, "click on graph", Qt.EditRole)

    def on_element_selected(self, selected, deselected):
        """Called when the selection in the treeview changes.
        """
        # Get the selected function index
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 0: return

        if selected_indexes[0].parent().row() == -1:
            function_index = selected_indexes[0].row()
            # Minimize all elements of the treeview except the selected one which is expanded
            self.algorithm_treeview.collapseAll()
            self.algorithm_treeview.expand(selected.indexes()[0])
        else:
            function_index = selected_indexes[0].parent().row()

        # Run the algorithm until the selected step
        algo_before_run = self.processing_object._algorithm.copy()
        try:
            self.processing_object.silent_run_algorithm(step=function_index)
        except:
            self.processing_object._algorithm = algo_before_run

        # Update the points and windows of the graph
        self.plot_points()
    
    # Context menu on the treeview

    def treeview_context_menu(self, position: QPoint):
        """ Show the context menu when right-clicking on an element in the tree view.

        Parameters
        ----------
        position : QPoint
            The position where the context menu should be displayed.
        """
        # Get the selected indexes
        indexes = self.algorithm_treeview.selectedIndexes()

        if indexes[0]:
            if indexes[0].parent().row() == -1:
                # Initialize the menu
                menu = QMenu()
                menu_actions = {}
                associated_action = {}

                # Adds the actions enabling the addition and deletion of functions
                menu_actions["add_before"] = menu.addAction("Add function before")
                associated_action["add_before"] = self.add_before

                menu_actions["add_after"] = menu.addAction("Add function after")
                associated_action["add_after"] = self.add_after

                menu_actions["delete"] = menu.addAction("Delete function")
                associated_action["delete"] = self.delete

                # Execute the menu
                action = menu.exec_(self.algorithm_treeview.viewport().mapToGlobal(position))
                for act in menu_actions.keys():
                    if action == menu_actions[act] and act in associated_action.keys():
                        associated_action[act]()

    # Graph interaction
    
    def start_graph_pick(self, index, label):
        self.graph_pick_index = index
        self.graph_pick_label = label
        self.graph_pick_delegate = self.parameter_delegate  # Save the delegate reference
        self.graph_pick_editor = label
        self.graph_pick_cid = self.graph_canvas.mpl_connect("button_press_event", self.on_graph_clicked)

    def on_graph_clicked(self, event):
        """Updates the corresponding value in the treeview of the clicked point in the graph.

        Parameters
        ----------
        event : _type_
            _description_
        """
        if hasattr(self, "graph_pick_index") and event.xdata is not None:
            value = f"{event.xdata:.3f}"
            model = self.graph_pick_index.model()
            model.setData(self.graph_pick_index, value, Qt.EditRole)
            # Emit commitData and closeEditor to close the editor and update the view
            if hasattr(self, "graph_pick_delegate") and hasattr(self, "graph_pick_editor"):
                self.graph_pick_delegate.commitData.emit(self.graph_pick_editor)
                self.graph_pick_delegate.closeEditor.emit(self.graph_pick_editor, QAbstractItemDelegate.NoHint)
            self.plot_points()
            # Remove the callback so it only triggers once
            self.graph_canvas.mpl_disconnect(self.graph_pick_cid)
            del self.graph_pick_index
            del self.graph_pick_label
            del self.graph_pick_delegate
            del self.graph_pick_editor
            del self.graph_pick_cid
            # Optionally, force the treeview to update/redraw
            self.algorithm_treeview.viewport().update()
    
    # Plotting functions

    def plot_average(self):
        """Plot the average of all the curves.
        """
        self.b_plot_average.setEnabled(False)
        self.b_plot_single.setEnabled(True)
        self.processing_object.y = np.mean(self.current_element, 
                                           axis=tuple(range(len(self.current_element.shape)-1)))
        for spinbox in self.dimension_spinboxes:
            spinbox.setEnabled(False)
        self.plot_spectrum()
    
    def plot_single(self):
        """Plot the average of all the curves.
        """
        self.b_plot_average.setEnabled(True)
        self.b_plot_single.setEnabled(False)
        y_selected = self.current_element
        for spinbox in self.dimension_spinboxes:
            spinbox.setEnabled(True)
            y_selected = y_selected[int(spinbox.value())]
        self.processing_object.y = y_selected
        self.plot_spectrum()

    def plot_spectrum(self, force_clear = False):
        """Plot the selected spectrum.
        """
        if not force_clear:
            if self.x_axis is None or self.y_axis is None:
                pass
            else:
                try:
                    if np.all(self.x_axis == self.processing_object.x) and np.all(self.y_axis == self.processing_object.y):
                        return
                except:
                    if np.all(self.x_axis == self.processing_object.frequency_sample) and np.all(self.y_axis == self.processing_object.PSD_sample):
                        return
        
        # Clear the graph
        self.graph_canvas.axes.clear()

        # Get the selected spectrum
        try:
            self.x_axis = self.processing_object.x
            self.y_axis = self.processing_object.y
        except:
            self.x_axis = self.processing_object.frequency_sample
            self.y_axis = self.processing_object.PSD_sample
        self.graph_canvas.axes.plot(self.x_axis, self.y_axis)
        self.graph_canvas.axes.set_xlabel(self.abscissa_name)
        self.graph_canvas.axes.set_ylabel("Amplitude")

        self.graph_canvas.axes.figure.tight_layout()
        self.graph_canvas.axes.figure.canvas.draw()

    def plot_points(self):
        """Plot the points stored in the processing object.
        """
        # Calls plot_spectrum which will clear the graph if needed
        self.plot_spectrum()

        # Set the list of colors to use for the points
        colors = self.config["Color_lines"]

        # Resets the list of points and windows plotted
        if self.points_plotted is None:
            self.points_plotted = []
            self.windows_plotted = []
        else:
            for line in self.points_plotted:
                try: line.remove()
                except: self.plot_spectrum(force_clear = True)
            for window in self.windows_plotted:
                try: window.remove()
                except: self.plot_spectrum(force_clear = True)
            self.points_plotted = []
            self.windows_plotted = []
        
        # Plot the points and windows
        points = self.processing_object.points
        windows = self.processing_object.windows
        for p, w in zip(points, windows):
            # Plot the point and the window
            nature_peak = p[0].split("_")[0]
            color = colors[nature_peak] if nature_peak in colors.keys() else "#000000ff"
            point = float(p[1])
            window = [float(w[0]), float(w[1])]
            self.points_plotted.append(self.graph_canvas.axes.axvline(point, color=color, linestyle='--'))
            self.windows_plotted.append(self.graph_canvas.axes.axvspan(window[0], window[1], color=color, alpha=0.5))
        self.graph_canvas.axes.figure.canvas.draw()

    # Button behaviour for window buttons

    def accept(self):
        super().accept()

    def reject(self):
        self.processing_object = None
        super().reject()

    # Static method to get the results of the window

    @staticmethod
    def get_results_PSD(wrapper_instance, elements, processing_object, parent=None):
        """Runs the GUI and returns the data processing object.

        Parameters
        ----------
        wrapper_instance : HDF5_BLS.Wrapper
            The wrapper instance to use
        elements : list of str
            The list of elements to process
        processing_object : Child of HDF5_BLS_analyse.Analyse_general
            The object to extract the PSD from the raw data
        parent : QMainWindow, optional
            Parent of the window, by default None

        Returns
        -------
        child of HDF5_BLS_analyse.Analyse_general
            The object that contains the results of the data processing
        list of str
            The list of elements that were processed
        """
        app = QApplication.instance() or QApplication(sys.argv)
        # Initialize the first element to display
        current_element = wrapper_instance[elements[0]]
        processing_object = processing_object(x = np.arange(current_element.shape[-1]), 
                                              y = np.mean(current_element, axis=tuple(range(len(current_element.shape)-1))))
        dialog = DataProcessingWindow_Analyse(wrapper_instance, elements, processing_object, parent)
        dialog.load_algorithm("Process_PSD")
        dialog.exec_()
        return dialog.processing_object, dialog.elements
    
class DataProcessingWindow_Treat(QDialog):
    def __init__(self, wrapper_instance: Wrapper, elements:list, processing_object, parent=None, *kwargs):
        super().__init__(parent)

        self.gui_root = str(Path(__file__).resolve().parent.parent.parent)

        # Load config file
        self.config = ConfigParser()
        self.config.read(f"{self.gui_root}/src/DataProcessing/config_Main.ini")

        # Set window title and geometry
        self.setWindowTitle("Data Processing Window")
        self.setGeometry(self.config["Geometry"].getint("x"),
                         self.config["Geometry"].getint("y"),
                         self.config["Geometry"].getint("width"),
                         self.config["Geometry"].getint("height"))

        # Store the wrapper instance and the chosen elements to process
        self.wrp = wrapper_instance
        self.elements = elements

        # Initialize the first element to display
        self.current_element_index = 0
        self.current_element = self.wrp[self.elements[self.current_element_index]]
        self.processing_object = processing_object
        self.abscissa_name = ""

        # Initialize the left frame (graph, selection of curves)
        self._initialize_left_frame()

        # Initialize the right frame (graph, selection of curves)
        self._initialize_right_frame()

        # Initialize the button box
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Set the layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.left_widget, 0, 0)
        self.layout.addWidget(self.right_widget, 0, 1)
        self.layout.addWidget(self.buttonBox, 1, 0, 1, 2)
        self.setLayout(self.layout)

        # Set window modality
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Plot the first element in default configuration (average of all axis minus last one)
        self.plot_spectrum()

    def _initialize_left_frame(self):
        """Initializes the left frame (graph, selection of curves)
        """
        # Create the buttons to choose wether to plot single curves or the average of all the curves
        self.b_previous_element = QPushButton(icon = QIcon(f"{self.gui_root}/assets/img/left_arrow.svg"), toolTip="Previous element")
        self.b_previous_element.clicked.connect(self.previous_element)
        self.b_previous_element.setEnabled(False)
        self.b_plot_single = QPushButton("Plot single curves")
        self.b_plot_single.clicked.connect(self.plot_single)
        if len(self.current_element.shape) == 1:
            self.b_plot_single.setEnabled(False)
        self.b_plot_average = QPushButton("Plot average of all curves")
        self.b_plot_average.setEnabled(False)
        self.b_plot_average.clicked.connect(self.plot_average)
        self.b_next_element = QPushButton(icon = QIcon(f"{self.gui_root}/assets/img/right_arrow.svg"), toolTip="Next element")
        self.b_next_element.clicked.connect(self.next_element)
        if len(self.elements) == 1:
            self.b_next_element.setEnabled(False)

        # Create the layout for the buttons
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.b_previous_element)
        self.buttons_layout.addWidget(self.b_plot_single)
        self.buttons_layout.addWidget(self.b_plot_average)
        self.buttons_layout.addWidget(self.b_next_element)

        # Create the spinboxes to select the dimensions to plot in case of single curves and add them to a layout
        self.dimension_layout = QHBoxLayout()
        self.l_dimensions = QLabel("Plotting spectrum index:")
        self.dimension_layout.addWidget(self.l_dimensions)
        self.dimension_spinboxes = []
        for i in range(len(self.current_element.shape)-1):
            self.dimension_spinboxes.append(QSpinBox())
            self.dimension_spinboxes[-1].setRange(0, self.current_element.shape[i]-1)
            self.dimension_spinboxes[-1].setValue(0)
            self.dimension_spinboxes[-1].setSingleStep(1)
            self.dimension_spinboxes[-1].setFixedWidth(50)
            self.dimension_spinboxes[-1].setToolTip(f"Dimension {i+1}")
            self.dimension_spinboxes[-1].setEnabled(False)
            self.dimension_spinboxes[-1].valueChanged.connect(self.plot_single)
            self.dimension_layout.addWidget(self.dimension_spinboxes[-1])

        # Create the graph
        self.graph_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.graph_toolbar = NavigationToolbar(self.graph_canvas, self)

        # Initialize the points and windows plotted
        self.points_plotted = None
        self.windows_plotted = None
        self.peaks_plotted = None

        # Initialize a storing array for the x axis
        self.x_axis = None
        self.y_axis = None

        # Set the layout
        self.left_widget = QWidget()
        left_frame = QVBoxLayout(self.left_widget)
        left_frame.addLayout(self.buttons_layout)
        left_frame.addLayout(self.dimension_layout)
        left_frame.addWidget(self.graph_toolbar)
        left_frame.addWidget(self.graph_canvas)
        self.left_widget.setLayout(left_frame)

    def _initialize_right_frame(self):
        """Initializes the right frame (graph, selection of curves)
        """
        self.l_titleAlgorithm = QLabel("Blank algorithm", alignment=Qt.AlignCenter)

        self.b_algo_graph = QPushButton("Display algorithm graph")
        self.b_algo_graph.clicked.connect(self.display_algo_graph)
        self.b_algo_graph.setEnabled(False)
        self.b_open_algo = QPushButton("Open algorithm")
        self.b_open_algo.clicked.connect(self.open_algo)
        self.b_create_new_algo = QPushButton("Create new algorithm")
        self.b_create_new_algo.clicked.connect(self.new_algo)
        self.b_save_algo = QPushButton("Save algorithm")
        self.b_save_algo.setEnabled(False)
        self.b_save_algo.clicked.connect(self.save_algo)

        # Create the treeview to display the algorithm
        self.algorithm_treeview = CustomTreeView(on_edit=self.on_treeview_edit)
        self.algorithm_treeview.setSelectionMode(QTreeView.SingleSelection)

        # Connect the menu to the treeview
        self.algorithm_treeview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.algorithm_treeview.customContextMenuRequested.connect(self.treeview_context_menu)
        
        # Make the value column enter edit mode on single click
        self.algorithm_treeview.setEditTriggers(QTreeView.EditTrigger.SelectedClicked | QTreeView.EditTrigger.CurrentChanged)
        self.parameter_delegate = ParameterDelegate(self, graph_callback=self.start_graph_pick)
        self.algorithm_treeview.setItemDelegateForColumn(1, self.parameter_delegate)
        
        # Create the model displayed in the treeview
        self.algorithm_model = TreeviewItemModel()

        # Set the model of the treeview
        self.algorithm_treeview.setModel(self.algorithm_model)
        # Connect model dataChanged signal to handler (must be after setModel)
        self.algorithm_model.dataChanged.connect(self.on_treeview_changed)

        # Connect selection change to custom handler
        selection_model = self.algorithm_treeview.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.on_element_selected)
        
        # Set two columns for the treeview with names "function" and "parameters"
        self.algorithm_model.setHorizontalHeaderLabels(["Parameters", "Values"])

        # Set the layout
        self.right_widget = QWidget()
        right_layout = QGridLayout(self.right_widget)
        right_layout.addWidget(self.l_titleAlgorithm, 0, 0, 1, 2)
        right_layout.addWidget(self.b_algo_graph, 1, 0, 1, 2)
        right_layout.addWidget(self.b_open_algo, 2, 0, 1, 1)
        right_layout.addWidget(self.b_create_new_algo, 2, 1, 1, 1)
        right_layout.addWidget(self.algorithm_treeview, 3, 0, 1, 2)
        right_layout.addWidget(self.b_save_algo, 4, 0, 1, 2)
        self.right_widget.setLayout(right_layout)

    # Button behaviour
    
    def display_algo_graph(self):
        """Displays the graph of the selected algorithm.
        """
        QMessageBox.information(self, "Not implemented", "To do")

    def next_element(self):
        """Go to the previous element in the list of elements.
        """
        if self.current_element_index == len(self.elements)-2:
            self.b_next_element.setEnabled(False)
        self.b_previous_element.setEnabled(True)
        self.current_element_index += 1
        self.current_element = self.wrp[self.elements[self.current_element_index]]
        if self.b_plot_average.isEnabled():
            self.plot_single()
        else:
            self.plot_average()

    def new_algo(self):
        """Creates a new algorithm.
        """
        QMessageBox.information(self, "Not implemented", "To do")

    def open_algo(self):
        """Opens an algorithm.
        """
        filepath = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json)")[0]
        if filepath:
            # Clear the algorithm treeview
            self.algorithm_model.clear()
            self.algorithm_model.setRowCount(0)
            self.algorithm_model.setColumnCount(2)
            self.algorithm_model.setHorizontalHeaderLabels(["Parameters", "Values"])

            # Activate the buttons
            self.b_algo_graph.setEnabled(True)
            self.b_save_algo.setEnabled(True)

            # Open the algorithm in the backend object
            self.processing_object.silent_open_algorithm(filepath)

            # Update the title of the algorithm
            name_algo = self.processing_object._algorithm["name"]
            self.l_titleAlgorithm.setText(f"{name_algo}")

            # Fill the treeview with the functions of the algorithm
            for nb, f in enumerate(self.processing_object._algorithm["functions"]):
                # Create a new row for the function
                function = QStandardItem(f["function"])
                function.setData(f["function"], Qt.UserRole)
                function.setFlags(function.flags() & ~Qt.ItemIsEditable)

                # Set the tooltip with line breaks
                description = f.get("description", "")
                words = description.split(" ")
                formatted_description = ""
                current_length = 0
                for word in words:
                    if "\n" in word:
                        formatted_description += word
                        current_length = 0
                    elif current_length + len(word) + 1 > 100:
                        formatted_description += "\n" + word
                        current_length = len(word)
                    else:
                        formatted_description += " " + word
                        current_length += len(word) + 1
                function.setToolTip(formatted_description.strip())

                # Adds all the parameters and values as children of the function
                for k, v in f["parameters"].items():
                    parameter, value = self.add_parameter(nb, k, v)
                    function.appendRow([parameter, value])

                # Add the function to the model
                self.algorithm_model.appendRow([function])
        else:
            return

    def previous_element(self):
        """Go to the previous element in the list of elements.
        """
        if self.current_element_index == 1:
            self.b_previous_element.setEnabled(False)
        self.b_next_element.setEnabled(True)
        self.current_element_index -= 1
        self.current_element = self.wrp[self.elements[self.current_element_index]]
        if self.b_plot_average.isEnabled():
            self.plot_single()
        else:
            self.plot_average()
    
    def save_algo(self):
        """Saves the algorithm.
        """
        # Get filename to save the JSON algorithm at
        filepath = QFileDialog.getSaveFileName(self, "Open File", "", "JSON Files (*.json)")[0]
        
        # Ask the user wether to save parameter values with the algorithm or not
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Question)
        dialog.setWindowTitle('Save parameters')
        dialog.setText('Do you want to save the values given to the parameters in the JSON file storing the algorithm?')
        dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
        buttonY = dialog.button(QMessageBox.Yes)
        buttonY.setText('Save parameters')
        buttonN = dialog.button(QMessageBox.No)
        buttonN.setText("Don't save parameters")
        dialog.exec_()
        
        # The user wants to add the data to the opened file
        if dialog.clickedButton() == buttonY: 
            save_parameters = True

        # The user wants to create a new file
        elif dialog.clickedButton() == buttonN: 
            save_parameters = False

        self.processing_object.silent_save_algorithm(filepath = filepath, save_parameters = save_parameters)

    # Function interaction
    
    def add_before(self):
        """Add a function before the selected function.
        """
        # Ask the user to choose a function
        functions = [function[0] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        executables = [function[1] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        choice, state = MessageBoxMultipleChoice.get_choice(text = "Choose a function to add before", list_choice = functions, parent = self)
        if state == "cancel": return

        # Get the selected index
        selected_index = self.algorithm_treeview.selectionModel().currentIndex()

        # Get its parent and row
        parent_index = selected_index.parent()
        row = selected_index.row()

        # Get the algorithm step to add
        function = executables[functions.index(choice)]
        function() 
        algo_step = self.processing_object._algorithm["functions"].pop()

        # Add the algorithm step to the algorithm at the right position
        self.processing_object._algorithm["functions"].insert(row, algo_step)

        # Add the function to the model
        function = QStandardItem(algo_step["function"])
        function.setData(algo_step["function"], Qt.UserRole)
        function.setFlags(function.flags() & ~Qt.ItemIsEditable)

        # Set the tooltip with line breaks
        description = algo_step["description"]
        words = description.split(" ")
        formatted_description = ""
        current_length = 0
        for word in words:
            if "\n" in word:
                formatted_description += word
                current_length = 0
            elif current_length + len(word) + 1 > 100:
                formatted_description += "\n" + word
                current_length = len(word)
            else:
                formatted_description += " " + word
                current_length += len(word) + 1
        function.setToolTip(formatted_description.strip())

        # Adds all the parameters and values as children of the function
        for k, v in algo_step["parameters"].items():
            parameter, value = self.add_parameter(row, k, v)
            function.appendRow([parameter, value])

        # Add the function to the model
        self.algorithm_model.insertRow(row, function)

        # Select the new function and expand it
        self.algorithm_treeview.setCurrentIndex(function.index())
        self.algorithm_treeview.expand(function.index())

    def add_after(self):
        """Add a function after the selected function.
        """
        # Ask the user to choose a function
        functions = [function[0] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        executables = [function[1] for function in inspect.getmembers(self.processing_object, inspect.isfunction)]
        choice, state = MessageBoxMultipleChoice.get_choice(text = "Choose a function to add before", list_choice = functions, parent = self)
        if state == "cancel": return

        # Get the selected index
        selected_index = self.algorithm_treeview.selectionModel().currentIndex()

        # Get its parent and row
        parent_index = selected_index.parent()
        row = selected_index.row() + 1

        # Get the algorithm step to add
        function = executables[functions.index(choice)]
        function() 
        algo_step = self.processing_object._algorithm["functions"].pop()

        # Add the algorithm step to the algorithm at the right position
        self.processing_object._algorithm["functions"].insert(row, algo_step)

        # Add the function to the model
        function = QStandardItem(algo_step["function"])
        function.setData(algo_step["function"], Qt.UserRole)
        function.setFlags(function.flags() & ~Qt.ItemIsEditable)

        # Set the tooltip with line breaks
        description = algo_step["description"]
        words = description.split(" ")
        formatted_description = ""
        current_length = 0
        for word in words:
            if "\n" in word:
                formatted_description += word
                current_length = 0
            elif current_length + len(word) + 1 > 100:
                formatted_description += "\n" + word
                current_length = len(word)
            else:
                formatted_description += " " + word
                current_length += len(word) + 1
        function.setToolTip(formatted_description.strip())

        # Adds all the parameters and values as children of the function
        for k, v in algo_step["parameters"].items():
            parameter, value = self.add_parameter(row, k, v)
            function.appendRow([parameter, value])

        # Add the function to the model
        self.algorithm_model.insertRow(row, function)

        # Select the new function and expand it
        self.algorithm_treeview.setCurrentIndex(function.index())
        self.algorithm_treeview.expand(function.index())

    def delete(self):
        """Delete the selected function.
        """
        # Get the selected index
        selected_index = self.algorithm_treeview.selectionModel().currentIndex()

        # Get its parent and row
        parent_index = selected_index.parent()
        row = selected_index.row()

        # Remove the step from the algorithm
        self.processing_object.silent_remove_step(step = row)

        # Remove the step from the model
        self.algorithm_model.removeRow(row, parent_index)

    def load_algorithm(self, name_attribute_algorithm : str = None):
        """Load the algorithm from the wrapper.

        Parameters
        ----------
        name_attribute_algorithm : str, optional
            The name of the attribute that contains the algorithm to load. If None, no algorithm is loaded.
        """
        if name_attribute_algorithm is None:
            return
        
        else:
            if name_attribute_algorithm in self.wrp.get_attributes(path=self.elements[self.current_element_index]).keys():
                # Get the algorithm and sets it to the processing object
                str_algorithm = self.wrp.get_attributes(path=self.elements[self.current_element_index])[name_attribute_algorithm]
                self.processing_object.silent_open_algorithm(filepath = None, algorithm_str = str_algorithm)

                
                # Update the title of the algorithm
                name_algo = self.processing_object._algorithm["name"]
                self.l_titleAlgorithm.setText(f"{name_algo}")

                # Fill the treeview with the functions of the algorithm
                for nb, f in enumerate(self.processing_object._algorithm["functions"]):
                    # Create a new row for the function
                    function = QStandardItem(f["function"])
                    function.setData(f["function"], Qt.UserRole)
                    function.setFlags(function.flags() & ~Qt.ItemIsEditable)
                    empty = QStandardItem("")
                    empty.setFlags(empty.flags() & ~Qt.ItemIsEditable)

                    # Set the tooltip with line breaks
                    description = f.get("description", "")
                    words = description.split(" ")
                    formatted_description = ""
                    current_length = 0
                    for word in words:
                        if "\n" in word:
                            formatted_description += word
                            current_length = 0
                        elif current_length + len(word) + 1 > 100:
                            formatted_description += "\n" + word
                            current_length = len(word)
                        else:
                            formatted_description += " " + word
                            current_length += len(word) + 1
                    function.setToolTip(formatted_description.strip())

                    # Adds all the parameters and values as children of the function
                    for k, v in f["parameters"].items():
                        parameter, value = self.add_parameter(function_nb = nb, 
                                                              parameter_key = k, 
                                                              parameter_value = v)
                        function.appendRow([parameter, value])

                    # Add the function to the model
                    self.algorithm_model.appendRow([function, empty])
            self.b_save_algo.setEnabled(True)

    # Treeview interaction

    def add_parameter(self, function_nb, parameter_key, parameter_value):
        """Add a parameter to the treeview.

        Parameters
        ----------
        function_nb : int
            The number of the function.
        parameter_key : str
            The key of the parameter.
        parameter_value : str
            The default value of the parameter.

        Returns
        -------
        QStandardItem
            The parameter item.
        QStandardItem
            The value item.
        """
        # Get the name of the function
        function_name = self.processing_object._algorithm["functions"][function_nb]["function"]
        # Create the parameter and value items
        parameter = QStandardItem(parameter_key)
        parameter.setData(f"{function_nb} - {parameter_key}", Qt.UserRole)
        # Make parameter name (column 0) non-editable
        parameter.setFlags(parameter.flags() & ~Qt.ItemIsEditable)
        if type(parameter_value) is bool:
            value = QStandardItem("  "+str(parameter_value))
            value.setData("bool", Qt.UserRole + 1)
            value.setData(parameter_value, Qt.UserRole + 2)
        else:
            if type(parameter_value) is float:
                value = QStandardItem(f"{parameter_value:.3f}")
            else:
                value = QStandardItem(str(parameter_value))
            if parameter_key.startswith("position"):
                value.setData("position_graph", Qt.UserRole + 1)
            elif parameter_key.startswith("type"):
                value.setData("type_combo", Qt.UserRole + 1)
                value.setData(["Elastic", "Stokes", "Anti-Stokes"], Qt.UserRole + 2)
            elif parameter_key.startswith("center"):
                value.setData("center_combo", Qt.UserRole + 1)
                value.setData(["Elastic", "Inelastic"], Qt.UserRole + 2)
            elif function_name  == "define_model" and parameter_key.startswith("model"):
                models = Models()
                vals = [key for key in models.models.keys() if not "elastic" in key]

                value.setData("model_combo", Qt.UserRole + 1)
                value.setData(vals, Qt.UserRole + 2)
            else:
                value.setData("default", Qt.UserRole + 1)
        return parameter, value

    def on_treeview_changed(self, topLeft, bottomRight, roles=None):
        """Called when the data in the treeview is changed.
        """
        function_nb = topLeft.parent().row()
        if function_nb == -1: return
        name_parameter = list(self.processing_object._algorithm["functions"][function_nb]["parameters"].keys())[topLeft.row()]

        new_value = topLeft.model().data(topLeft)

        if new_value == "click on graph":
            return
        
        # Try converting the new value to a float
        try:
            new_value = float(new_value)
        except:
            pass

        self.processing_object._algorithm["functions"][function_nb]["parameters"][name_parameter] = new_value
        self.processing_object.silent_run_algorithm(step=function_nb)
        
        self.plot_points()

    def on_treeview_edit(self, index, text = "click on graph"):
        editor_type = index.data(Qt.UserRole + 1)
        if editor_type == "position_graph":
            self.algorithm_model.setData(index, "click on graph", Qt.EditRole)

    def on_element_selected(self, selected, deselected):
        """Called when the selection in the treeview changes.
        """
        # Get the selected function index
        selected_indexes = selected.indexes()
        if len(selected_indexes) == 0: return

        if selected_indexes[0].parent().row() == -1:
            function_index = selected_indexes[0].row()
            # Minimize all elements of the treeview except the selected one which is expanded
            self.algorithm_treeview.collapseAll()
            self.algorithm_treeview.expand(selected.indexes()[0])
        else:
            function_index = selected_indexes[0].parent().row()

        # Run the algorithm until the selected step
        algo_before_run = self.processing_object._algorithm.copy()
        try:
            self.processing_object.silent_run_algorithm(step=function_index)
        except:
            print("Error while running the algorithm, restoring previous state.")
            del self.processing_object._algorithm
            self.processing_object._algorithm = algo_before_run

        # Update the points and windows of the graph
        self.plot_points()
    
    # Context menu on the treeview

    def treeview_context_menu(self, position: QPoint):
        """ Show the context menu when right-clicking on an element in the tree view.

        Parameters
        ----------
        position : QPoint
            The position where the context menu should be displayed.
        """
        # Get the selected indexes
        indexes = self.algorithm_treeview.selectedIndexes()

        if indexes[0]:
            if indexes[0].parent().row() == -1:
                # Initialize the menu
                menu = QMenu()
                menu_actions = {}
                associated_action = {}

                # Adds the actions enabling the addition and deletion of functions
                menu_actions["add_before"] = menu.addAction("Add function before")
                associated_action["add_before"] = self.add_before

                menu_actions["add_after"] = menu.addAction("Add function after")
                associated_action["add_after"] = self.add_after

                menu_actions["delete"] = menu.addAction("Delete function")
                associated_action["delete"] = self.delete

                # Execute the menu
                action = menu.exec_(self.algorithm_treeview.viewport().mapToGlobal(position))
                for act in menu_actions.keys():
                    if action == menu_actions[act] and act in associated_action.keys():
                        associated_action[act]()

    # Graph interaction
    
    def start_graph_pick(self, index, label):
        self.graph_pick_index = index
        self.graph_pick_label = label
        self.graph_pick_delegate = self.parameter_delegate  # Save the delegate reference
        self.graph_pick_editor = label
        self.graph_pick_cid = self.graph_canvas.mpl_connect("button_press_event", self.on_graph_clicked)

    def on_graph_clicked(self, event):
        """Updates the corresponding value in the treeview of the clicked point in the graph.

        Parameters
        ----------
        event : _type_
            _description_
        """
        if hasattr(self, "graph_pick_index") and event.xdata is not None:
            value = f"{event.xdata:.3f}"
            model = self.graph_pick_index.model()
            model.setData(self.graph_pick_index, value, Qt.EditRole)
            # Emit commitData and closeEditor to close the editor and update the view
            if hasattr(self, "graph_pick_delegate") and hasattr(self, "graph_pick_editor"):
                self.graph_pick_delegate.commitData.emit(self.graph_pick_editor)
                self.graph_pick_delegate.closeEditor.emit(self.graph_pick_editor, QAbstractItemDelegate.NoHint)
            self.plot_points()
            # Remove the callback so it only triggers once
            self.graph_canvas.mpl_disconnect(self.graph_pick_cid)
            del self.graph_pick_index
            del self.graph_pick_label
            del self.graph_pick_delegate
            del self.graph_pick_editor
            del self.graph_pick_cid
            # Optionally, force the treeview to update/redraw
            self.algorithm_treeview.viewport().update()
    
    # Plotting functions

    def plot_average(self):
        """Plot the average of all the curves.
        """
        self.b_plot_average.setEnabled(False)
        self.b_plot_single.setEnabled(True)
        self.processing_object.y = np.mean(self.current_element, 
                                           axis=tuple(range(len(self.current_element.shape)-1)))
        for spinbox in self.dimension_spinboxes:
            spinbox.setEnabled(False)
        self.plot_spectrum()
    
    def plot_single(self):
        """Plot the average of all the curves.
        """
        self.b_plot_average.setEnabled(True)
        self.b_plot_single.setEnabled(False)
        y_selected = self.current_element
        for spinbox in self.dimension_spinboxes:
            spinbox.setEnabled(True)
            y_selected = y_selected[int(spinbox.value())]
        self.processing_object.y = y_selected
        self.plot_spectrum()

    def plot_spectrum(self, force_clear = False):
        """Plot the selected spectrum.
        """
        if not force_clear:
            if self.x_axis is None or self.y_axis is None:
                pass
            else:
                try:
                    if np.all(self.x_axis == self.processing_object.x) and np.all(self.y_axis == self.processing_object.y):
                        return
                except:
                    if np.all(self.x_axis == self.processing_object.frequency_sample) and np.all(self.y_axis == self.processing_object.PSD_sample):
                        return
        
        # Clear the graph
        self.graph_canvas.axes.clear()

        # Get the selected spectrum
        try:
            self.x_axis = self.processing_object.x
            self.y_axis = self.processing_object.y
        except:
            self.x_axis = self.processing_object.frequency_sample
            self.y_axis = self.processing_object.PSD_sample
        self.graph_canvas.axes.plot(self.x_axis, self.y_axis)
        self.graph_canvas.axes.set_xlabel(self.abscissa_name)
        self.graph_canvas.axes.set_ylabel("Amplitude")

        self.graph_canvas.axes.figure.tight_layout()
        self.graph_canvas.axes.figure.canvas.draw()

    def plot_points(self):
        """Plot the points stored in the processing object.
        """
        # Calls plot_spectrum which will clear the graph if needed
        self.plot_spectrum()

        # Set the list of colors to use for the points
        colors = self.config["Color_lines"]

        # Resets the list of points and windows plotted
        if self.points_plotted is None:
            self.points_plotted = []
            self.windows_plotted = []
            self.peaks_plotted = []
        else:
            for line in self.points_plotted:
                try: line.remove()
                except: self.plot_spectrum(force_clear = True)
            for window in self.windows_plotted:
                try: window.remove()
                except: self.plot_spectrum(force_clear = True)
            for peak in self.peaks_plotted:
                try: peak.remove()
                except: self.plot_spectrum(force_clear = True)
            self.points_plotted = []
            self.windows_plotted = []
            self.peaks_plotted = []
        
        # Plot the points and windows
        points = self.processing_object.points
        if len(self.processing_object.windows) == len(self.processing_object.width_estimator):
            width_estimator = self.processing_object.width_estimator
            window = self.processing_object.windows
            for p, w, we in zip(points, window, width_estimator):
                # Plot the point and the window
                nature_peak = p[0].split("_")[0]
                color = colors[nature_peak] if nature_peak in colors.keys() else "#000000ff"
                point = float(p[1])
                window = [float(w[0]), float(w[1])]
                wid_est = [point - float(we)/2, point + float(we)/2]
                
                psd_loc = self.processing_object.PSD_sample[np.where((self.processing_object.frequency_sample >= window[0]) & (self.processing_object.frequency_sample <= window[1]))]
                pos_med = (max(psd_loc)-min(self.processing_object.PSD_sample))/2 + min(self.processing_object.PSD_sample)

                self.points_plotted.append(self.graph_canvas.axes.axvline(point, color=color, linestyle='--'))
                self.windows_plotted.append(self.graph_canvas.axes.plot([wid_est[0], wid_est[1]], [pos_med, pos_med], color=color, alpha=0.5))
        else:
            windows = self.processing_object.windows
            for p, w in zip(points, windows):
                # Plot the point and the window
                nature_peak = p[0].split("_")[0]
                color = colors[nature_peak] if nature_peak in colors.keys() else "#000000ff"
                point = float(p[1])
                window = [float(w[0]), float(w[1])]
                self.points_plotted.append(self.graph_canvas.axes.axvline(point, color=color, linestyle='--'))
                self.windows_plotted.append(self.graph_canvas.axes.axvspan(window[0], window[1], color=color, alpha=0.5))
        
        # Plot the peaks
        if len(self.processing_object.shift_sample):
            QMessageBox.information(self, "Shift", f"Shift: {len(self.processing_object.shift_sample)} - 1st value: {self.processing_object.shift_sample[0]}")

        self.graph_canvas.axes.figure.canvas.draw()

    # Button behaviour for window buttons

    def accept(self):
        super().accept()

    def reject(self):
        self.processing_object = None
        super().reject()

    # Static method to get the results of the window
    @staticmethod
    def get_results_Treat(wrapper_instance, element_psd, element_frequency, parent=None):
        """Runs the GUI and returns the data processing object.

        Parameters
        ----------
        wrapper_instance : HDF5_BLS.Wrapper
            The wrapper instance to use
        elements : list of str
            The list of elements to process
        parent : QMainWindow, optional
            Parent of the window, by default None

        Returns
        -------
        child of HDF5_BLS_analyse.Analyse_general
            The object that contains the results of the data processing
        list of str
            The list of elements that were processed
        """
        app = QApplication.instance() or QApplication(sys.argv)
        processing_object = Treat(wrapper_instance[element_frequency], wrapper_instance[element_psd])
        dialog = DataProcessingWindow_Treat(wrapper_instance, [element_psd], processing_object, parent)
        dialog.load_algorithm("Process")
        dialog.exec_()
        return dialog.processing_object, dialog.elements
    


if __name__ == "__main__":
    config = ConfigParser()
    config.read("./src/DataProcessing/config_Main.ini")

    colors = config["Color_lines"]
    print(colors["Stokes"])