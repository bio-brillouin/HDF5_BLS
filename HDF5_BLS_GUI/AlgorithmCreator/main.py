from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from inspect import getmembers, isfunction, signature, isclass, Parameter
import numpy as np

from AlgorithmCreator.UI.algorithmCreator_ui import Ui_Dialog
from ComboboxChoose.main import ComboboxChoose
from HelpFunction.main import HelpFunction

from HDF5_BLS import wrapper, analyze
import numpy as np
import json


class AlgorithmCreator(qtw.QDialog, Ui_Dialog):
    """"
    This class defines the GUI of the AlgorithmCreator. It allows to create an algorithm using all the functions stored in the module given as argument.

    Methods
    -------
    __init__(self, parent, wrapper)
        Initialize the GUI to be a child of the parent. Initialize also the wrapper.
    """
    def __init__(self, parent, module, algorithm = None):
        """Inspects the module given as argument to get the functions to use and initializes the GUI.
        """
        super().__init__(parent)
        self.setupUi(self)

        #Initializes the buttons
        self.b_AddAfter.clicked.connect(self.add_after)
        self.b_AddBefore.clicked.connect(self.add_before)
        self.b_Delete.clicked.connect(self.delete)
        self.b_Help.clicked.connect(self.help)
        self.b_MoveDown.clicked.connect(self.move_down)
        self.b_MoveUp.clicked.connect(self.move_up)

        # Deactivate buttons that cannot be used
        self.b_Delete.setEnabled(False)
        self.b_Help.setEnabled(False)
        self.b_MoveDown.setEnabled(False)
        self.b_MoveUp.setEnabled(False)

        # Initializes the ListView of the functions
        self.model_functions = qtg.QStandardItemModel()
        self.model_functions.setHorizontalHeaderLabels(["Name"])
        self.model_functions.setColumnCount(1)
        self.model_functions.setHeaderData(0, qtc.Qt.Horizontal, "Name")

        self.lst_Functions.setModel(self.model_functions)

        functions = getmembers(module, isfunction)
        self.function_names = [name for name, _ in functions if not name.startswith("_")]

        for name in self.function_names:
            item = qtg.QStandardItem(name)
            self.model_functions.appendRow([item])

        # Extracts the docstrings of the functions
        self.docstrings = [func.__doc__ for name, func in functions if not name.startswith("_")]

        # Extracts the parameters of the functions
        self.parameters = []
        for name, func in functions:
            if not name.startswith("_"):
                sgn = signature(func)
                dic = {}
                for k, v in sgn.parameters.items():
                    if k != "self":
                        dic[k] = v.default
                self.parameters.append(dic)

        # Connects the QListView to left-click on a function to select it
        self.lst_Functions.clicked.connect(self.select_function)

        # Connects the QTreeView to left-click on a function to select it
        self.tv_algorithm.clicked.connect(self.select_algorithm)

        # Initializes variables to store the selected function both in the algorithm and in the list of functions
        self.function_list = None
        self.function_algorithm = None

        # Initializes the algorithm
        if algorithm is None:
            self.algorithm = {
                "name": "",
                "version": "",
                "author": "",
                "description": "",
                "functions": []
            } 
        else:
            self.algorithm = algorithm

        # Initializes the Treeview of the algorithm
        self.model_algorithm = qtg.QStandardItemModel()
        self.model_algorithm.setHorizontalHeaderLabels(["Function", "Values"])

        self.tv_algorithm.setModel(self.model_algorithm)

    def add_after(self):
        """Adds a function after a selected function in the algorithm list."""
        # Extract the function name, description, and parameters
        func = self.function_names[self.function_list]
        parameters = self.parameters[self.function_list]
        description = self.docstrings[self.function_list]
        for e in self.algorithm["functions"]:
            if e["function"] == func:
                description = "See previous run"
        
        # Add the function to the algorithm
        if self.function_algorithm is None:
            self.algorithm["functions"].append({
                "function": func,
                "parameters": parameters,
                "description": description
            })
        else:
            self.algorithm["functions"].insert(self.function_algorithm+1, 
                                               {"function": func,
                                                "parameters": parameters,
                                                "description": description
                                            })
        self.update_algorithm()

    def add_before(self):
        """Adds a function before a selected function in the algorithm list."""
        # Extract the function name, description, and parameters
        func = self.function_names[self.function_list]
        parameters = self.parameters[self.function_list]
        description = self.docstrings[self.function_list]
        for e in self.algorithm["functions"]:
            if e["function"] == func:
                description = "See previous run"
        
        # Add the function to the algorithm
        if self.function_algorithm is None:
            self.algorithm["functions"].append({
                "function": func,
                "parameters": parameters,
                "description": description
            })
        else:
            self.algorithm["functions"].insert(self.function_algorithm, 
                                               {"function": func,
                                                "parameters": parameters,
                                                "description": description
                                            })
        self.update_algorithm()

    def delete(self):
        """Delete the selected function from the algorithm."""
        if self.function_algorithm is None:
            return

        # Delete the function from the algorithm
        self.algorithm["functions"].pop(self.function_algorithm)

        # Update the algorithm
        self.update_algorithm()

    def help(self):
        """Displays the help of the selected function which displays the docstring of the function."""
        name = self.function_names[self.function_list]
        docstring = self.docstrings[self.function_list]
        help_wndw = HelpFunction(parent = self, function_name = name, docstring = docstring)
        help_wndw.exec_()

    def move_down(self):
        "Moves an element of the algorithm down in the list of functions."
        if self.function_algorithm is None or self.function_algorithm == len(self.algorithm["functions"])-1:
            return 
        
        # Move the function down in the algorithm
        self.algorithm["functions"].insert(self.function_algorithm+1, 
                                           self.algorithm["functions"].pop(self.function_algorithm))
    
        # Update the algorithm
        self.update_algorithm()

    def move_up(self):    
        """Moves an element of the algorithm up in the list of functions."""
        if self.function_algorithm is None or self.function_algorithm == 0:
            return 
        
        # Move the function up in the algorithm
        self.algorithm["functions"].insert(self.function_algorithm-1, 
                                           self.algorithm["functions"].pop(self.function_algorithm))
    
        # Update the algorithm
        self.update_algorithm()

    def return_algorithm(self):
        """Returns the algorithm as a dictionary."""
        name_algorithm = self.le_NameAlgorithm.text()
        version_algorithm = self.le_Version.text()
        author_algorithm = self.le_Author.text()
        description_algorithm = self.te_Description.toPlainText()

        self.algorithm["name"] = name_algorithm
        self.algorithm["version"] = version_algorithm
        self.algorithm["author"] = author_algorithm
        self.algorithm["description"] = description_algorithm

        return self.algorithm

    def select_algorithm(self, index):
        """Selects the function in the list of functions and in the algorithm.

        Parameters
        ----------
        index : QModelIndex
            The index of the function in the list of functions.
        """
        # Get the name of the function
        name = self.model_algorithm.item(index.row(), 0).text()

        # Get the index of the function in the list of functions
        self.function_algorithm = index.row()

        # Activate the help button
        self.b_Help.setEnabled(False)
        self.b_Delete.setEnabled(True)
        self.b_MoveUp.setEnabled(True)
        self.b_MoveDown.setEnabled(True)

    def select_function(self, index):
        """Selects the function in the list of functions and in the algorithm.

        Parameters
        ----------
        index : QModelIndex
            The index of the function in the list of functions.
        """
        # Get the name of the function
        name = self.model_functions.item(index.row(), 0).text()

        # Get the index of the function in the list of functions
        self.function_list = self.function_names.index(name)

        # Activate the help button
        self.b_Help.setEnabled(True)
        self.b_Delete.setEnabled(False)
        self.b_MoveUp.setEnabled(False)
        self.b_MoveDown.setEnabled(False)

    def update_algorithm(self):
        """
        Updates the tree view with the selected functions and their parameters.
        Each function is added as a top-level element, and its parameters are added as child elements.
        """
        # Clear the tree view
        self.model_algorithm.clear()
        self.model_algorithm.setColumnCount(2)
        self.model_algorithm.setHeaderData(0, qtc.Qt.Horizontal, "Function")
        self.model_algorithm.setHeaderData(1, qtc.Qt.Horizontal, "Values")

        # Add each function as a top-level item
        for function_data in self.algorithm["functions"]:
            function_name = function_data.get("function", "Unknown Function")
            parameters = function_data.get("parameters", {})

            # Create a top-level item for the function
            function_item = qtg.QStandardItem(function_name)
            function_item.setEditable(False)

            # Add parameters as child items
            for param_name, param_value in parameters.items():
                param_item_name = qtg.QStandardItem(param_name)
                param_item_value = qtg.QStandardItem(str(param_value))
                param_item_name.setEditable(False)
                param_item_value.setEditable(False)
                function_item.appendRow([param_item_name, param_item_value])

            # Add the function item to the model
            self.model_algorithm.appendRow([function_item, qtg.QStandardItem("")])
