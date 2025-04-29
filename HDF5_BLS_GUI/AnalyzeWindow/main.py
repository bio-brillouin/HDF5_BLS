from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from inspect import getmembers, isfunction, signature, isclass, Parameter
import numpy as np

from AnalyzeWindow.UI.analyze_window_ui import Ui_Dialog
from ComboboxChoose.main import ComboboxChoose

from HDF5_BLS import wrapper, analyze
import numpy as np
import json
import graphviz

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class AnalyzeWindow(qtw.QDialog, Ui_Dialog):
    """"
    This class defines the GUI of the AnalyzeWindow. It is meant to interface the analyze module

    Methods
    -------
    __init__(self, parent, wrapper)
        Initialize the GUI to be a child of the parent. Initialize also the wrapper.
    """

    parameters = {}
    data = None
    parameter_return = {} # Stores the parameters that will be returned to the conversion_ui module.
    treatment = ""

    graph_canvas = None
    graph_toolbar = None
    graph_layout = None

    def __init__(self, parent, x, y):
        def initialize_graph(self):
            # Initializes the graph
            self.graph_canvas = MplCanvas(self, width=5, height=4, dpi=100)
            self.graph_toolbar = NavigationToolbar(self.graph_canvas, self)

            # Set the layout
            self.graph_layout = qtw.QVBoxLayout()
            self.graph_layout.addWidget(self.graph_toolbar)
            self.graph_layout.addWidget(self.graph_canvas)

            # Set the frame
            self.frame_graph.setLayout(self.graph_layout)

        super().__init__(parent)
        self.setupUi(self)

        # Initializes the graph
        initialize_graph(self)

        # Inititalizes the function index to 0
        self.algorithm_function_index = 0

class AnalyzeWindow_VIPA(AnalyzeWindow):
    def __init__(self, parent, x, y, str_algorithm = None):
        def initialize_buttons(self):
            # Ensure f_Dimension has a layout
            if not self.f_Dimension.layout():
                self.f_Dimension.setLayout(qtw.QHBoxLayout())
            # Adding the spinboxes to select the spectrum given the dimensions
            self.b_Sum.clicked.connect(self.change_plot_mode)
            self.spinbox_dimension = {}
            for i, s in enumerate(self.analyzer.y.shape[:-1]):
                label = qtw.QLabel(f"D{i} (<{s})")
                spinbox = qtw.QSpinBox()
                spinbox.setRange(0, s - 1)
                self.spinbox_dimension[i] = spinbox
                spinbox.valueChanged.connect(lambda : self.update_graph(single=True))

                layout = qtw.QHBoxLayout()
                layout.addWidget(label)
                layout.addWidget(spinbox)

                self.f_Dimension.layout().addLayout(layout)
            # Adding the button to display a selected algorithm and setting it to disabled by default
            self.b_GraphAlgorithm.clicked.connect(self.create_graph_algorithm)
            self.b_GraphAlgorithm.setEnabled(False)
            # Adding the button to open or create a new algorithm
            self.b_OpenAlgorithm.clicked.connect(self.open_algorithm)
            # Adding the button to create a new algorithm
            self.b_NewAlgorithm.clicked.connect(self.new_algorithm)
            # Adding the button to save the algorithm
            self.b_SaveAlgorithm.clicked.connect(self.save_algorithm)
            self.b_SaveAlgorithm.setEnabled(False) 
            # Adding the button to run all the algorithm
            self.b_RunAll.clicked.connect(self.run_all)
            self.b_RunAll.setEnabled(False)

        super().__init__(parent, x, y)

        self.analyzer = analyze.Analyze_VIPA(x = x, y = y)

        # Set the title of the window
        self.setWindowTitle("Analyze Window")

        # Initialize the buttons
        self.plot_mode = "average"
        self.algorithm_path = None
        initialize_buttons(self)

        # Update the graph
        self.change_plot_mode()

        # Set the algorithm if it is given
        if str_algorithm is not None:
            self.analyzer._algorithm = json.loads(str_algorithm)
            self.algorithm_function_index = 0
            self.update_graph(average=True)
            self.update_treeview()
    
    def add_function(self, step = None):
        """
        Adds a function to the algorithm from the available functions of the class of the analyzer attribute.
        """
        # Extract the available function names from the Analyze_VIPA class
        functions = [name for name, func in getmembers(self.analyzer, isfunction) if not name.startswith("_")]

        # Create a combobox to select the function
        choice = ComboboxChoose(text = "Choose the function to add", list_choices = functions, parent = self)
        if choice.exec_() == qtw.QDialog.Accepted:
            function_name = choice.get_selected_structure()
        else:
            return
        
        # We execute the function that has been selected in the combobox
        func = self.analyzer.__getattribute__(function_name)
        func()

        # If a step was specified, we move the last function in the algorithm to the specified step
        if not step is None:
            self.analyzer._move_step(len(self.analyzer._algorithm["functions"])-1, step)
            
        # Update the graph and the treeview
        self.b_GraphAlgorithm.setEnabled(True)
        self.update_graph(average=True)
        self.update_treeview()
        self.t_Functions.setCurrentIndex(self.t_Functions.model().index(self.algorithm_function_index+1, 0))
        self.t_Functions.setExpanded(self.t_Functions.model().index(self.algorithm_function_index+1, 0), True)

    def change_plot_mode(self):
        """
        Changes the plot mode of the graph from single to average.
        """
        if self.plot_mode == "single":
            self.plot_mode = "average"
            self.b_Sum.setText("Plot average spectra")
            for k in self.spinbox_dimension.keys():
                self.spinbox_dimension[k].setEnabled(True)
            self.update_graph(single = True)
        else:
            self.plot_mode = "single"
            self.b_Sum.setText("Plot single spectrum")
            for k in self.spinbox_dimension.keys():
                self.spinbox_dimension[k].setEnabled(False)
            self.update_graph(average = True)

    def create_graph_algorithm(self):
        """
        Visualizes the algorithm selected in the combobox.
        """
        # Create a graphviz object and sets up the basic properties of the elements
        dot = graphviz.Digraph(comment = self.analyzer._algorithm.get("name", "Algorithm Graph"))
        dot.attr('node', shape='note', style='filled', fillcolor='lightblue')
        dot.attr('graph', fontname='Helvetica, Arial, Sans')
        dot.attr('node', fontname='Helvetica, Arial, Sans')
        dot.attr('edge', fontname='Helvetica, Arial, Sans')

        # Sets the maximum width of the elements in inches (here to have a width of max 10cm)
        max_width_inches = 10 / 2.54

        # Extracts the description of the algorithm and replaces line breaks by <br/> to display them using HTML-like labels
        description = self.analyzer._algorithm["description"]
        description = description.replace("\n", "<br/>")

        # Wraps the description to have less than 100 characters per line
        if len(description) > 100:
            words = description.split(" ")
            new_description = ""
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 > 100:
                    new_description += word + "</i><br/><i>"
                    current_length = 0
                else:
                    new_description += word + " "
                    current_length += len(word) + 1
        else:
            new_description = description

        # Creates the first node with the name of the algorithm, its version, author and description
        label = f"<b>{self.analyzer._algorithm["name"]}</b> - {self.analyzer._algorithm["version"]}<br/>{self.analyzer._algorithm["author"]}<br/><br/><i>{new_description}</i>"
        dot.node(f"presentation", label=f"<{label}>", width=str(max_width_inches), fixedsize='false', fillcolor = "#ff8ccb", shape = "rect")

        for i, function_data in enumerate(self.analyzer._algorithm.get("functions", [])):
            function_name = function_data["function"]
            description = function_data.get("description", "")
            parameters = function_data.get("parameters", {})

            param_str = ""
            for key, value in parameters.items():
                param_value_str = ""
                if isinstance(value, list):
                    if len(value) > 5:
                        param_value_str = f"[{value[0]}, {value[1]}, {value[2]}, {value[3]}, ... {value[-1]}]"
                    elif len(value)>0 and len(value) <= 5:
                        param_value_str = "["
                        for v in value:
                            param_value_str += f"{v}, "
                        param_value_str = param_value_str[:-2] + "]"
                    else:
                        param_value_str = "[]"
                else:
                    param_value_str = str(value)
                param_str += f"{key}: {param_value_str}<br/>" # Add <br/> for each parameter

            # Add line breaks to the description at the last space before every 100 characters
            description = description.replace("\n", "<br/>")
            if len(description) > 100:
                words = description.split(" ")
                new_description = ""
                current_length = 0
                for word in words:
                    if "<br/>" in word:
                        new_description += word + " "
                        current_length = 0
                    elif current_length + len(word) + 1 > 100:
                        new_description += word + "</i><br/><i>"
                        current_length = 0
                    else:
                        new_description += word + " "
                        current_length += len(word) + 1
            else:
                new_description = description

            label = f"<b>{function_name}</b><br/><br/><i>{new_description}</i><br/><br/>{param_str.rstrip('<br/>')}"
            dot.node(f"step_{i}", label=f"<{label}>", width=str(max_width_inches), fixedsize='false') # Use HTML-like labels

            if i > 0:
                dot.edge(f"step_{i-1}", f"step_{i}")
        
        dot.edge("presentation", "step_0")

        dot.render("graphical_algorithm", view=True, cleanup=True)

    def get_results(self):
        """Returns the result of the analysis (here the x-axis of the data).

        Returns
        -------
        array
            The frequency axis of the data.
        """
        return self.analyzer._return_string_algorithm(), self.analyzer.x

    def new_algorithm(self):
        """
        Creates a new algorithm.
        """ 
        qtw.QMessageBox.information(self, "To do", "Not implemented yet")

    def on_treeview_item_clicked(self, item):
        """
        Slot to handle treeview item clicks.
        Displays the index of the clicked function in self.analyzer._algorithm["functions"].
        """
        # Get the parent of the clicked item
        parent = item.parent()

        # If the clicked item is a top-level function
        if parent is None:
            # Get the index of the function number in the algorithm
            index = self.t_Functions.indexOfTopLevelItem(item)
            self.algorithm_function_index = index

            # Run the algorithm up to the selected function
            self.analyzer._run_algorithm(step = index)

            # Updates the graph
            self.update_graph(average=True)

    def open_algorithm(self):
        """
        Opens a file dialog to select an algorithm file.
        """
        # Opens a filedialog to select an algorithm file
        filepath = qtw.QFileDialog.getOpenFileName(self, "Open File", "algorithms/Analysis/VIPA spectrometer", "JSON Files (*.json)")[0]
        if not filepath:
            return 
        
        # Opens the algorithm file and automatically selects the first function
        self.algorithm_path = filepath
        self.analyzer._open_algorithm(filepath = filepath)
        self.algorithm_function_index = 0

        # Enables the graph button 
        self.b_GraphAlgorithm.setEnabled(True)
        self.b_SaveAlgorithm.setEnabled(True)
        self.b_RunAll.setEnabled(True)

        # Sets the title of the algorithm
        self.l_titleAlgorithm.setText(self.analyzer._algorithm["name"] + " - " + self.analyzer._algorithm["version"])

        # Updates the treeview and the graph
        self.update_treeview()

        # Selects the first function of the algorithm, try to run it, and updates the graph
        self.t_Functions.setCurrentIndex(self.t_Functions.model().index(0, 0))
        self.analyzer._run_algorithm(step = 0)
        self.update_graph(average=True)

    def run_all(self):
        """
        Creates a new algorithm.
        """
        index_last = len(self.analyzer._algorithm["functions"])-1
        self.t_Functions.setCurrentIndex(self.t_Functions.model().index(index_last, 0))
        self.analyzer._run_algorithm(step = index_last)
        self.update_graph(average=True)

    def save_algorithm(self):
        """
        Creates a new algorithm.
        """
        # Create a file dialog with an additional checkbox for saving parameters
        dialog = qtw.QFileDialog(self, "Save File", "", "JSON Files (*.json)")
        dialog.setAcceptMode(qtw.QFileDialog.AcceptSave)
        dialog.setOption(qtw.QFileDialog.DontUseNativeDialog, True)

        # Add a checkbox to the dialog
        checkbox = qtw.QCheckBox("Save parameter values")
        layout = dialog.layout()
        layout.addWidget(checkbox, layout.rowCount(), 0, 1, layout.columnCount())

        if dialog.exec_() == qtw.QDialog.Accepted:
            filepath = dialog.selectedFiles()[0]
            save_parameters = checkbox.isChecked()
            if filepath:
                self.analyzer._save_algorithm(filepath=filepath, save_parameters=save_parameters)

    def update_treeview(self):
        """
        Shows the treeview of the algorithm with two columns and makes the second column editable.
        """
        def add_function_step(i, function_data):
            # Extract the function name, description, and parameters
            function_name = function_data["function"]
            description = function_data.get("description", "")

            # Add a top-level item for the function
            function_item = qtw.QTreeWidgetItem(self.t_Functions)
            function_item.setText(0, str(i))
            function_item.setText(1, function_name)
            function_item.setText(2, "")  # Leave the second column empty for the parameters

            # Set tooltip for the function item
            set_tooltip_function(function_item, description)

            return function_item

        def add_paramter_step(index_function, function_item, function_data):
            def activate_position(param_name):
                # Change the button text to indicate the user should click on the graph
                parameter_widgets[param_name].setText("Click on graph")

                def on_click(event):
                    # Check if the click is within the graph axes
                    if event.inaxes == self.graph_canvas.axes:
                        # Update the button text with the clicked x value (rounded to 2 decimals)
                        x_value = event.xdata
                        parameter_widgets[param_name].setText(f"{x_value:.2f}")

                        # Update the parameter in the algorithm
                        self.analyzer._algorithm["functions"][index_function]["parameters"][param_name.split(".")[1]] = x_value

                        # Run the algorithm up to the current step
                        self.analyzer._run_algorithm(step=self.algorithm_function_index)

                        # Update the graph
                        self.update_graph(average=True, keep_lim = True)

                        # Disconnect the click event
                        self.graph_canvas.mpl_disconnect(cid)

                # Connect the click event to the graph
                cid = self.graph_canvas.mpl_connect("button_press_event", on_click)

            def change_type(param_name):
                # Get the new type of the peak
                new_type = parameter_widgets[param_name].currentText()

                # Update the parameter in the algorithm
                self.analyzer._algorithm["functions"][index_function]["parameters"][param_name.split(".")[1]] = new_type

                # Run the algorithm up to the current step
                self.analyzer._run_algorithm(step=self.algorithm_function_index)

                # Update the graph
                self.update_graph(average=True)

            def change_value(param_name):
                # Get the new value of the parameter
                new_value = parameter_widgets[param_name].text()

                # Update the parameter in the algorithm. Adding a try/except in case the user deletes the whole line edit
                try:
                    self.analyzer._algorithm["functions"][index_function]["parameters"][param_name.split(".")[1]] = float(new_value)

                    # Run the algorithm up to the current step
                    self.analyzer._run_algorithm(step=self.algorithm_function_index)

                    # Update the graph
                    self.update_graph(average=True)
                except:
                    pass
                    
            # Get the parameters of the function
            parameters = function_data.get("parameters", {})

            # Initiate a parameter widget dictionnary to store the widgets for each parameter
            parameter_widgets = {}

            # Add parameters as child items
            for param_name, param_value in parameters.items():
                # Create a new treeview idem and sets its name to the name of the function at this step.
                param_item = qtw.QTreeWidgetItem(function_item)
                param_item.setText(1, param_name)

                if param_name.startswith("position"):
                    # Add a text edit and a button
                    widget = qtw.QWidget()
                    layout = qtw.QHBoxLayout(widget)
                    if param_value is None:
                        param_value = 0
                    parameter_widgets[f"{index_function}.{param_name}"] = qtw.QPushButton(f"{param_value:.2f}")
                    parameter_widgets[f"{index_function}.{param_name}"].clicked.connect(lambda i=index_function, param_name=param_name: activate_position(f"{index_function}.{param_name}"))
                    layout.addWidget(parameter_widgets[f"{index_function}.{param_name}"])
                    layout.setContentsMargins(0, 0, 0, 0)
                    self.t_Functions.setItemWidget(param_item, 2, widget)
                elif param_name.startswith("type"):
                    # Add a spinbox with predefined values
                    parameter_widgets[f"{index_function}.{param_name}"] = qtw.QComboBox()
                    parameter_widgets[f"{index_function}.{param_name}"].addItems(["Elastic", "Stokes", "Anti-Stokes"])
                    if param_value is None:
                        param_value = "Elastic"
                    parameter_widgets[f"{index_function}.{param_name}"].setCurrentText(str(param_value))
                    parameter_widgets[f"{index_function}.{param_name}"].currentTextChanged.connect(lambda i=index_function, param_name=param_name: change_type(f"{index_function}.{param_name}"))
                    self.t_Functions.setItemWidget(param_item, 2, parameter_widgets[f"{index_function}.{param_name}"])
                elif param_name.startswith("center"):
                    # Add a spinbox with predefined values
                    parameter_widgets[f"{index_function}.{param_name}"] = qtw.QComboBox()
                    parameter_widgets[f"{index_function}.{param_name}"].addItems(["Elastic", "Inelastic"])
                    if param_value is None:
                        param_value = "Elastic"
                    parameter_widgets[f"{index_function}.{param_name}"].setCurrentText(str(param_value))
                    parameter_widgets[f"{index_function}.{param_name}"].currentTextChanged.connect(lambda i=index_function, param_name=param_name: change_type(f"{index_function}.{param_name}"))
                    self.t_Functions.setItemWidget(param_item, 2, parameter_widgets[f"{index_function}.{param_name}"])
                else:
                    # Add a line text
                    widget = qtw.QWidget()
                    layout = qtw.QHBoxLayout(widget)
                    if param_value is None:
                        param_value = 0
                    parameter_widgets[f"{index_function}.{param_name}"] = qtw.QLineEdit(f"{param_value}")
                    parameter_widgets[f"{index_function}.{param_name}"].textChanged.connect(lambda i=index_function, param_name=param_name: change_value(f"{index_function}.{param_name}"))
                    layout.addWidget(parameter_widgets[f"{index_function}.{param_name}"])
                    layout.setContentsMargins(0, 0, 0, 0)
                    self.t_Functions.setItemWidget(param_item, 2, widget)
                    
            return parameter_widgets

        def remove_function(item):
            """
            Removes a function from the algorithm.

            Parameters
            ----------
            item : QTreeWidgetItem
                The item to be removed.
            """
            self.analyzer._remove_step(step=self.algorithm_function_index)
            self.analyzer._run_algorithm(step=self.algorithm_function_index)

            self.update_treeview()
            self.update_graph(average=True)

        def set_tooltip_function(item, description):
            # Add line breaks to the description at the last space before every 100 characters
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

            # Set the tooltip with line breaks
            item.setToolTip(1, formatted_description.strip())

        def show_context_menu(item):
            """
            Displays a context menu when right-clicking on a treeview item.

            Parameters
            ----------
            position : QPoint
                The position where the context menu should appear.
            """
            # Set self.algorithm_function_index to the index of the selected item
            tree_item = self.t_Functions.itemAt(item)
            if tree_item:
                self.algorithm_function_index = self.t_Functions.indexOfTopLevelItem(tree_item)
            else:
                self.algorithm_function_index = 0

            # Create the context menu
            menu = qtw.QMenu(self)

            # Add actions to the menu
            add_before_action = menu.addAction("Add Function Before")
            add_after_action = menu.addAction("Add Function After")
            menu.addSeparator()
            remove_action = menu.addAction("Delete Function")

            # Execute the menu and get the selected action
            action = menu.exec_(self.t_Functions.viewport().mapToGlobal(item))
            
            # Perform the corresponding action
            if action == add_before_action:
                self.add_function(step=self.algorithm_function_index)
            elif action == add_after_action:
                self.add_function(step=self.algorithm_function_index+ 1)
            elif action == remove_action:
                remove_function(item)

        # Set up the tree widget with two columns
        self.t_Functions.setColumnCount(3)
        self.t_Functions.setEditTriggers(qtw.QAbstractItemView.DoubleClicked | qtw.QAbstractItemView.SelectedClicked)
        self.t_Functions.setHeaderLabels(["", "Name", "Value"])
        self.t_Functions.clear()

        # Create an empty list of the widgets for each parameter of each function. Each element of the list is a dictionnary with the name of the parameter as key and the widget as value, that corresponds to the parameters of the function at the current step.
        parameter_widgets = {}
        for i, function_data in enumerate(self.analyzer._algorithm.get("functions", [])):
            # Add a top-level item for the function
            function_item = add_function_step(i, function_data)

            # Add parameters as child items
            parameter_widgets.update(add_paramter_step(i, function_item, function_data))
        
        # Make the treeview scrollable if needed
        self.t_Functions.header().setSectionResizeMode(qtw.QHeaderView.ResizeToContents)
        self.t_Functions.header().setStretchLastSection(False)
        self.t_Functions.itemClicked.connect(self.on_treeview_item_clicked)

        # Expands the function selected in self.algorithm_function_index
        self.t_Functions.setCurrentIndex(self.t_Functions.model().index(self.algorithm_function_index, 0))
        # Add context menu to the treeview
        self.t_Functions.setContextMenuPolicy(qtc.Qt.CustomContextMenu)
        self.t_Functions.customContextMenuRequested.connect(show_context_menu)

    def update_graph(self, single=False, average=False, keep_lim = False):
        """
        Updates the graph with the selected parameters.

        Parameters
        ----------
        single : bool
            If True, the graph will display a single spectrum based on the spinbox values.
        average : bool
            If True, the graph will display the average spectrum.
        """
        if keep_lim:
            xlim = self.graph_canvas.axes.get_xlim()
            ylim = self.graph_canvas.axes.get_ylim()

        # Clear the graph
        self.graph_canvas.axes.cla()
        self.points_graph = {}
        self.points_graph_value = []

        # Determine the data to plot
        if average:
            y_temp = self.analyzer.y
            while y_temp.ndim > 1:
                y_temp = np.average(y_temp, axis=0)
        elif single:
            dimension = [self.spinbox_dimension[i].value() for i in self.spinbox_dimension.keys()]
            y_temp = self.analyzer.y
            for d in dimension:
                y_temp = y_temp[d, :]
        self.graph_canvas.axes.plot(self.analyzer.x, y_temp)

        # Plot points and windows
        for elt_p, elt_w in zip(self.analyzer.points, self.analyzer.windows):
            k, v = elt_p[0], elt_p[1]
            color = "red" if k[0] == "E" else "blue" if k[0] == "S" else "green"
            self.points_graph_value.append(v)
            self.points_graph[str(v)] = {
                "line": self.graph_canvas.axes.axvline(v, color=color),
                "type": "point",
                "name": k,
            }
            s, e = elt_w[0], elt_w[1]
            self.points_graph[str(s)] = {
                "line": self.graph_canvas.axes.axvspan(s, e, color=color, alpha=0.2),
                "type": "window",
                "name": k,
            }
            self.points_graph[str(e)] = {"linked": str(s)}

        # Set axis labels and redraw
        self.graph_canvas.axes.set_xlabel("x")
        self.graph_canvas.axes.set_ylabel("y")
        self.graph_canvas.draw()
        if keep_lim:
            self.graph_canvas.axes.set_xlim(xlim)
            self.graph_canvas.axes.set_ylim(ylim)
