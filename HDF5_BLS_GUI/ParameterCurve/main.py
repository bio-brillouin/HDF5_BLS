from PySide6 import QtCore as qtc
from PySide6 import QtWidgets as qtw
from PySide6 import QtGui as qtg
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from inspect import getmembers, isfunction, signature, isclass, Parameter
import numpy as np

from ParameterCurve.UI.parameters_curve_ui import Ui_Dialog

from HelpFunction.main import HelpFunction

from HDF5_BLS import wrapper
import numpy as np

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class ParameterCurve(qtw.QDialog, Ui_Dialog):
    """"
    This class is the least common denominator to display a data, extract parameters and apply a function to it. 
    This class creates a GUI divided in two areas: 
    - a plotting area 
    - a treatment area
    The plotting area is composed of:
    - a combobox with the available curves: self.cb_curves
    - a matplotlib canvas where the data is plotted: self.graph_canvas
    The treatment area is composed of:
    - a combobox to select the function to apply: self.cb_function
    - a frame where all the parameters of the function are listed: self.list_parameters
    - a frame to interact with the function: self.frame_confirmParam

    Methods
    -------
    __init__(self, parent, wrapper)
        Initialize the GUI to be a child of the parent. Initialize also the wrapper.
    set_combobox_curves(self, curves)
        Set the combobox with the curves.
    get_results(self)
        This function is called when the user clicks on the OK button. It returns the self.parameter_return attribute.
    show_parameters_function(self, functions, function_names)
        Creates the combobox with all the function names in "function_names". For each function, it extracts its parameters and adds them in the frame dedicated to the parameters. All the parameters widgets can be accessed in the self.parameters attribute, which is a dictionnary where all the items have for a key, the name of the parameter of the function, and then 3 elements: a layout, a label and a line edit named respectively "layout", "label" and "line edit".
    """

    parameters = {}
    data = None
    parameter_return = {} # Stores the parameters that will be returned to the conversion_ui module.
    treatment = ""

    graph_canvas = None
    graph_toolbar = None
    graph_layout = None

    def __init__(self, parent=None, wrapper=None):
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

        self.wrapper = wrapper

        # Initializes the graph
        initialize_graph(self)

        # Initializes or reinitializes the parameters
        self.parameters = {}
        self.data = None
        self.parameter_return = {}
        self.treatment = ""

        # Set the combobox with the curve names
        self.set_combobox_curves()
    
    def set_combobox_curves(self):
        """
        Sets the combobox to choose the curve to work on. The curves are plotted following the structure of the wrapper selected. For example:
        Laser
            |- Laser_0
            |- Laser_1
            |- Laser_2
        """
        def get_structure_wrapper(wrp, l = {}):
            for e in wrp.data.keys():
                if isinstance(wrp.data[e], wrapper.Wrapper):
                    if "Treat" in e: continue
                    name = wrp.data[e].attributes["FILEPROP.Name"]
                    l[name] = {}
                    get_structure_wrapper(wrp.data[e],l[name])
            return l
    
        def list_from_structure(structure, ls=[], code = [], l=0, code_up = "Data", ls_up = ""):
            for i, e in enumerate(structure.keys()):
                if ls_up: ls.append("  |- " + ls_up + "/" + e)
                else: ls.append(e)
                code.append(code_up+"/Data_"+str(i))
                if structure[e] is not None: 
                    ls, code = list_from_structure(structure[e], ls, code, l+1, code[-1], ls[-1])
            return ls, code

        temp = get_structure_wrapper(self.wrapper) # Extracts the structure of the wrapper
        if temp: structure = temp
        else: structure = {self.wrapper.attributes["FILEPROP.Name"]: {}}
        self.combobox_curve_names, self.combobox_curve_codes = list_from_structure(structure) # Transforms the structure into a list of strings and a list of codes
        self.cb_curves.addItems(self.combobox_curve_names,)
    
    def get_results(self):
        return self.parameter_return

    def show_parameters_function(self, functions, function_names):
        """
        Displays the functions associated to the technique used to capture the data and their parameters on the GUI.

        Parameters
        ----------
        functions : list of functions
            List of the functions to display corresponding to the function names in the combobox.
        function_names : list of str
            List of the function names that will be displayed in the combobox.
        """
        # Get the function selected in the combobox
        self.function_name = self.cb_functions.currentText()
        if not self.function_name: return
        func = functions[function_names.index(self.function_name)]

        # Get the signature of the function and extract its docstring, places the doscstring in a dedicated window 
        sig = signature(func)

        # Clears the parameters layout
        for k in self.parameters.keys():
            for k_e in self.parameters[k].keys():
                try: self.parameters[k][k_e].setParent(None)
                except: pass
        
        # Creates the parameters layout
        self.parameters = {}
        i=0
        for name, param in sig.parameters.items():
            # Extract the type of the parameter
            typ = param.annotation if param.annotation is not Parameter.empty else None
            # If a parameter starts with "n_", it is not a parameter that should be displayed on the GUI
            if name[:2] == "n_": continue
            
            if typ == bool: # If the parameter is a boolean
                # Create the elements of the GUI for the parameter.
                temp_dict = {}
                temp_dict["layout"] = qtw.QGridLayout() # Creates the layout where the parameter will be displayed
                temp_dict["label"] = qtw.QLabel(name) # Creates the label for the parameter
                temp_dict["checkbox"] = qtw.QCheckBox() # Creates the checkbox for the parameter

                # Initializes the line edit with the default value of the parameter if it exists
                if not param.default == Parameter.empty:
                    temp_dict["checkbox"].setChecked(param.default)

                # Places the elements in the layout
                temp_dict["layout"].addWidget(temp_dict["label"], 0, 0, 1, 1)
                temp_dict["layout"].addWidget(temp_dict["checkbox"], 0, 1, 1, 1)
            
            elif name[:2] == "c_": # If the parameter starts with "c_", then the choice will be limited to a list of choices and a combobox will be used to choose between them. Note that the initialization of the combobox has to be done in the inherited classes.
                # Create the elements of the GUI for the parameter.
                temp_dict = {}
                temp_dict["layout"] = qtw.QGridLayout() # Creates the layout where the parameter will be displayed
                temp_dict["label"] = qtw.QLabel(name) # Creates the label for the parameter
                temp_dict["combobox"] = qtw.QComboBox() # Creates the combobox for the parameter

                # Places the elements in the layout
                temp_dict["layout"].addWidget(temp_dict["label"], 0, 0, 1, 1)
                temp_dict["layout"].addWidget(temp_dict["combobox"], 0, 1, 1, 1)
            
            else:
                # Create the elements of the GUI for the parameter.
                temp_dict = {}
                temp_dict["layout"] = qtw.QGridLayout() # Creates the layout where the parameter will be displayed
                temp_dict["label"] = qtw.QLabel(name) # Creates the label for the parameter
                temp_dict["line_edit"] = qtw.QLineEdit() # Creates the line edit for the parameter

                # Initializes the line edit with the default value of the parameter if it exists
                if not param.default == Parameter.empty:
                    temp_dict["line_edit"].setText(str(param.default))

                # Places the elements in the layout
                temp_dict["layout"].addWidget(temp_dict["label"], 0, 0, 1, 1)
                temp_dict["layout"].addWidget(temp_dict["line_edit"], 0, 1, 1, 1)

            # Adds the layout to the dictionary of all the parameters
            self.parameters[name] = temp_dict

            # Adds the layout to the GUI
            self.gridLayout_4.addLayout(temp_dict["layout"], i+1, 0, 1, 1)
            i+=1


class ar_BLS_VIPA_parameters(ParameterCurve):
    def __init__(self, parent=None, wrapper=None):
        super().__init__(parent, wrapper)

        # Initializes the graph
        self.cb_curves.currentIndexChanged.connect(self.handle_data)
        self.handle_data()

        # Initializes the buttons to apply the function
        self.setup_button_apply()

        # Initializes the graph
        self.setup_graph()

    def add_curve(self):
        if "center" not in self.parameter_return.keys(): 
            self.parameter_return["center"] = {}
        if "data shape" not in self.parameter_return.keys(): 
            self.parameter_return["data shape"] = self.data.shape
        if "treatment" not in self.parameter_return.keys(): 
            self.parameter_return["treatment"] = self.function_name

        if not self.cb_curves.currentText() in self.parameter_return["center"].keys():
            self.parameter_return["center"][self.cb_curves.currentText()] = [[self.c_x, self.c_y, self.r]]
        else:
            self.parameter_return["center"][self.cb_curves.currentText()].append([self.c_x, self.c_y, self.r])
        self.setup_graph()

        self.button_add.setEnabled(False)
        self.button_del.setEnabled(False)

    def apply_function(self):
        func = self.functions[self.function_names.index(self.function_name)]

        if self.function_name == "extract_center_v0":
            # Extract the parameters of the function
            x_0 = int(self.parameters["x_0"]["line_edit"].text())
            y_0 = int(self.parameters["y_0"]["line_edit"].text())
            pixel_window = int(self.parameters["pixel_window"]["line_edit"].text())
            threshold = float(self.parameters["threshold"]["line_edit"].text())
            error_pos = float(self.parameters["error_pos"]["line_edit"].text())

            # Apply the function to retrieve the center and radii fitted on the arc circle
            self.c_x, self.c_y, self.r = func(n_data=self.data, 
                                              x_0=x_0, 
                                              y_0=y_0, 
                                              pixel_window=pixel_window, 
                                              threshold=threshold, error_pos=error_pos)

            # Plot the fitted circle on the graph
            curv_x, curv_y = self.get_circle(self.c_x, self.c_y, self.r)
            self.setup_graph()
            self.cur_curve = self.graph_canvas.axes.plot(curv_x, curv_y, color='red')
            self.graph_canvas.draw()

            # Enable the buttons to add or delete the curve to the returned parameters.
            self.button_add.setEnabled(True)
            self.button_del.setEnabled(True)
        
        elif self.function_name == "get_frequency_from_elastic_v0":
            # Extract the parameters of the function
            x_0 = int(self.parameters["x_0"]["line_edit"].text())
            y_0 = int(self.parameters["y_0"]["line_edit"].text())
            pixel_window = int(self.parameters["pixel_window"]["line_edit"].text())
            threshold = float(self.parameters["threshold"]["line_edit"].text())
            error_pos = float(self.parameters["error_pos"]["line_edit"].text())

            # Apply the function to retrieve the center and radii fitted on the arc circle
            curv_x, curv_y = func(n_data=self.data, 
                                  x_0=x_0, 
                                  y_0=y_0, 
                                  pixel_window=pixel_window, 
                                  threshold=threshold, error_pos=error_pos)

            # Plot the fitted circle on the graph
            self.setup_graph()
            self.cur_curve = self.graph_canvas.axes.plot(curv_x, curv_y, color='red')
            self.graph_canvas.draw()

            # Enable the buttons to add or delete the curve to the returned parameters.
            self.button_add.setEnabled(True)
            self.button_del.setEnabled(True)

        else: # If the function is not implemented, display a warning message.
            qtw.QMessageBox.warning(self.parent, "Warning", "Function not implemented")

    def delete_curve(self):
        self.setup_graph()
        self.button_add.setEnabled(False)
        self.button_del.setEnabled(False)

    def get_circle(self, c_x = None, c_y = None, r = None):
        """
        Returns the circle defined by the parameters self.c_x, self.c_y and self.r with the data.
        """
        if c_x is None: c_x = self.c_x
        if c_y is None: c_y = self.c_y
        if r is None: r = self.r
        y = np.arange(self.data.shape[0])
        x = np.sqrt(r**2 - (y-c_y)**2) + c_x

        return x,y

    def handle_data(self):
        """
        Plots the curve that is currently selected in the combobox. This function also defines self.data and updates the parameters.
        """
        # Extract the raw data from the wrapper corresponding to the selected curve in the combobox
        wrp = self.wrapper
        path = self.combobox_curve_codes[self.combobox_curve_names.index(self.cb_curves.currentText())]
        for e in path.split("/")[1:]: wrp = wrp.data[e]

        self.data = wrp.data["Raw_data"]

        # Plot the data
        self.graph_canvas.axes.cla()

        self.graph_canvas.axes.imshow(self.data)
        self.graph_canvas.axes.set_xlabel("Pixel")
        self.graph_canvas.axes.set_ylabel("Pixel")
        self.graph_canvas.draw()
        self.update_parameters()
    
    def update_parameters(self):
        def initialize_parameters(self, module):
            functions = [func for func in getmembers(module, isfunction)]
            function_names = [func[0] for func in functions]
            functions = [func[1] for func in functions]

            self.cb_functions.clear()
            self.cb_functions.addItems(function_names)
            self.cb_functions.setCurrentIndex(0)
            self.cb_functions.currentIndexChanged.connect(lambda: self.show_parameters_function(functions, function_names))

            return functions, function_names

        def setup_button_help_function(self, functions, function_names):
            def show_help_function():
                docstring = functions[function_names.index(self.function_name)].__doc__ or ""
                msgBox = HelpFunction(self, self.function_name, docstring)
                msgBox.exec_()

            self.b_helpFunction.clicked.connect(show_help_function)

        # Define the module to be used 
        from HDF5_BLS.conversion_PSD_modules import ar_BLS_VIPA as module

        # Extracts the functions and the function names from the module
        self.functions, self.function_names = initialize_parameters(self, module)

        # Sets the combobox with the functions
        self.show_parameters_function(self.functions, self.function_names)

        # Sets the help button to display the function's docstring
        setup_button_help_function(self, self.functions, self.function_names)
    
    def setup_button_apply(self):
        """
        Creates the layout for the buttons to apply the function.
        """
        layout = qtw.QGridLayout(self.frame_confirmParam)

        button_vis = qtw.QPushButton()
        button_vis.setText("Visualize curve")
        button_vis.clicked.connect(self.apply_function)

        self.button_add = qtw.QPushButton()
        self.button_add.setText("Add curve")
        self.button_add.clicked.connect(self.add_curve)
        self.button_add.setEnabled(False)

        self.button_del = qtw.QPushButton()
        self.button_del.setText("Delete curve")
        self.button_del.clicked.connect(self.delete_curve)
        self.button_del.setEnabled(False)

        layout.addWidget(button_vis, 0, 0, 1, 2)
        layout.addWidget(self.button_add, 1, 0, 1, 1)
        layout.addWidget(self.button_del, 1, 1, 1, 1)

    def setup_graph(self):
        def onclick(event = None):
            if event.inaxes:
                x, y = int(event.xdata), int(event.ydata)
                self.parameters["x_0"]["line_edit"].setText(str(x))
                self.parameters["y_0"]["line_edit"].setText(str(y))
        
        self.graph_canvas.axes.cla()
        self.graph_canvas.axes.imshow(self.data)
        self.graph_canvas.axes.set_xlabel("Pixel")
        self.graph_canvas.axes.set_ylabel("Pixel")
        self.graph_canvas.draw()

        data_selected = self.cb_curves.currentText()
        if "center" in self.parameter_return.keys():
            if data_selected in self.parameter_return["center"].keys():
                for (cx, cy, r) in self.parameter_return["center"][data_selected]:
                    curv_x, curv_y = self.get_circle(cx, cy, r)
                    self.graph_canvas.axes.plot(curv_x, curv_y, color='blue')
                self.graph_canvas.draw()

        # Connects the graph to the onclick function
        self.graph_canvas.mpl_connect('button_press_event', onclick)

class ar_BLS_VIPA_treat(ParameterCurve):
    def __init__(self, parent=None, wrapper=None, frequency = None):
        super().__init__(parent, wrapper)

        self.frequency = frequency

        # Initializes the graph
        self.cb_curves.currentIndexChanged.connect(self.handle_data)
        self.handle_data()

        self.setup_button_apply()

    def apply_function(self):
        def apply_on_wrapper(func, wrp, center_frequency, linewidth, normalize, c_model, fit_S_and_AS, window_peak_find, window_peak_fit, correct_elastic, IR_wndw):
            for e in wrp.data.keys():
                if isinstance(wrp.data[e], wrapper.Wrapper):
                    return {e:apply_on_wrapper(func, wrp.data[e], center_frequency, linewidth, normalize, c_model, fit_S_and_AS, window_peak_find, window_peak_fit, correct_elastic, IR_wndw)}
                else:
                    Popt, Std = [], []
                    for f, d in zip(self.frequency, wrp.data[e]):
                        try:
                            popt, std, treat_steps = func(n_frequency = f, 
                                                          n_data = d, 
                                                          center_frequency = center_frequency, 
                                                          linewidth = linewidth, 
                                                          normalize = normalize, 
                                                          c_model = c_model, 
                                                          fit_S_and_AS = fit_S_and_AS, 
                                                          window_peak_find = window_peak_find, 
                                                          window_peak_fit = window_peak_fit, 
                                                          correct_elastic = correct_elastic, 
                                                          IR_wndw = IR_wndw)
                            n = popt.size
                        except:
                            popt, std, treat_steps = None, None,[ "Error"]
                        Popt.append(popt)
                        Std.append(std)
                    for i in range(len(Popt)):
                        if Popt[i] is None: 
                            Popt[i] = np.zeros(n)
                            Std[i] = np.zeros(n)
                    return {"Popt": np.array(Popt), "Std": np.array(Std), "treat_steps": treat_steps}

        def update_wrapper(wrp,dic):
            if "Popt" in dic.keys():
                data = {"Shift" : dic["Popt"][:,-2],
                        "Shift_std" : dic["Std"][:,-2],
                        "Linewidth" : dic["Popt"][:,-1], 
                        "Linewidth_std" : dic["Std"][:,-1]}
                i = 0
                while f"Treat_{i}" in wrp.data.keys(): i += 1
                wrp.data[f"Treat_{i}"] = wrapper.Wrapper(data = data,
                                                         attributes = {"FILEPROP.Name": f"Treat_{i}"}, 
                                                         data_attributes={})
            # Goes through the dictionary and updates the wrapper accordingly by creating a new group to store the treatment
            else:    
                for e in dic.keys():
                    update_wrapper(wrp.data[e], dic[e])
                    
        func = self.functions[self.function_names.index(self.function_name)]

        if self.function_name == "fit_model_v0":
            # Extract the parameters of the function
            try:
                center_frequency = float(self.parameters["center_frequency"]["line_edit"].text())
                linewidth = float(self.parameters["linewidth"]["line_edit"].text())
                normalize = not bool(self.parameters["normalize"]["checkbox"].text())
                c_model = str(self.parameters["c_model"]["combobox"].currentText())
                fit_S_and_AS = not bool(self.parameters["fit_S_and_AS"]["checkbox"].checkState())
                window_peak_find = float(self.parameters["window_peak_find"]["line_edit"].text()) 
                window_peak_fit = float(self.parameters["window_peak_fit"]["line_edit"].text())
                correct_elastic = not bool(self.parameters["correct_elastic"]["checkbox"].checkState())
                IR_wndw = (self.parameters["IR_wndw"]["line_edit"].text())

                if IR_wndw == "None": IR_wndw = None
            except:
                qtw.QMessageBox.warning(self, "Error while retrieving parameters", "An error happened while retrieving the parameters")
            
            # Apply the function to fit the data
            dic = apply_on_wrapper(func, self.wrapper, center_frequency, linewidth, normalize, c_model, fit_S_and_AS, window_peak_find, window_peak_fit, correct_elastic, IR_wndw)
            
            # Updates the wrapper
            update_wrapper(self.wrapper, dic)

        else: # If the function is not implemented, display a warning message.
            qtw.QMessageBox.warning(self.parent, "Warning", "Function not implemented")

    def handle_data(self):
        """
        Plots the curve that is currently selected in the combobox. This function also defines self.data and updates the parameters.
        """
        # Extract the raw data from the wrapper corresponding to the selected curve in the combobox
        wrp = self.wrapper
        
        if len(self.combobox_curve_codes) > 1:
            path = self.combobox_curve_codes[self.combobox_curve_names.index(self.cb_curves.currentText())]
            for e in path.split("/")[1:]:
                wrp = wrp.data[e]

        if "Raw_data" in wrp.data.keys() and wrp.data_attributes["Raw_data"]["Name"] == "Power Spectral Density":
            self.data = wrp.data["Raw_data"]

            # Plot the data
            self.graph_canvas.axes.cla()

            _, y = np.meshgrid(np.arange(self.data.shape[1]), np.arange(self.data.shape[0]))
            self.graph_canvas.axes.pcolormesh(self.frequency, y, self.data, shading='auto', cmap='viridis')
            self.graph_canvas.axes.set_xlabel("Frequency Shift (GHz)")
            self.graph_canvas.axes.set_ylabel("Pixel")
            self.graph_canvas.draw()
            self.update_parameters()
  
    def update_parameters(self):
        def initialize_parameters(self, module):
            functions = [func for func in getmembers(module, isfunction)]
            function_names = [func[0] for func in functions]
            functions = [func[1] for func in functions]

            self.cb_functions.clear()
            self.cb_functions.addItems(function_names)
            self.cb_functions.setCurrentIndex(0)
            self.cb_functions.currentIndexChanged.connect(lambda: self.show_parameters_function(functions, function_names))

            return functions, function_names

        def setup_button_help_function(self, functions, function_names):
            def show_help_function():
                docstring = functions[function_names.index(self.function_name)].__doc__ or ""
                msgBox = HelpFunction(self, self.function_name, docstring)
                msgBox.exec_()

            self.b_helpFunction.clicked.connect(show_help_function)

        def onclick_x0(event = None):
            if event.inaxes:
                x = float(event.xdata) * 1e6//1
                x = x/1e6
                self.parameters["center_frequency"]["line_edit"].setText(str(x))
        
        def onclick_linewidth(event = None):
            if event.inaxes:
                self.temp_linewidth = float(event.xdata)
                self.graph_canvas.mpl_connect('motion_notify_event', on_drag)

        def on_drag(event):
            if event.inaxes and event.button == 1:
                x1 = float(event.xdata)
            linewidth = abs(x1 - self.temp_linewidth) * 1e6//1
            linewidth = linewidth/1e6
            self.parameters["linewidth"]["line_edit"].setText(str(linewidth))

        # Define the module to be used 
        import HDF5_BLS.treat as module 

        # Extracts the functions and the function names from the module
        self.functions, self.function_names = initialize_parameters(self, module)

        # Sets the combobox with the functions
        self.show_parameters_function(self.functions, self.function_names)

        # Adds the models in the dedicated combobox.
        Models = module.Models()
        self.parameters["c_model"]["combobox"].addItems(Models.models.keys())

        # Connects the QLineEdit widget to the onclick_x0 function
        self.parameters["center_frequency"]["line_edit"].mousePressEvent = lambda event: self.graph_canvas.mpl_connect('button_press_event', onclick_x0)
        
        # Connects the QLineEdit widget to the onclick_linewidth function
        self.parameters["linewidth"]["line_edit"].mousePressEvent = lambda event: self.graph_canvas.mpl_connect('button_press_event', onclick_linewidth)

        # Sets the help button to display the function's docstring
        setup_button_help_function(self, self.functions, self.function_names)

    def setup_button_apply(self):
        """
        Creates the layout for the buttons to apply the function.
        """
        layout = qtw.QGridLayout(self.frame_confirmParam)

        button_treat = qtw.QPushButton()
        button_treat.setText("Treat")
        button_treat.clicked.connect(self.apply_function)

        layout.addWidget(button_treat, 0, 0, 1, 1)
  
class TFP_treat(ParameterCurve):
    def __init__(self, parent=None, wrp_base = None, path_base = None, path_curves = None, path_frequency = None, frequency = None):
        super().__init__(parent, wrp_base.get_child(path_base))

        if frequency is None:
            self.path_curves = path_curves
            self.path_frequency = path_frequency
            self.path_frequency_unique = None
        else:
            self.path_curves = None
            self.path_frequency = None
            self.path_frequency_unique = frequency

        # Initializes the graph
        self.cb_curves.currentIndexChanged.connect(self.handle_data)
        self.handle_data()

        self.setup_button_apply()
    
    def apply_function(self):
        """
        Extracts the parameters from the GUI and pplies the treatment to the data.
        """
        func = self.functions[self.function_names.index(self.function_name)]

        if self.function_name == "fit_model_v0":
            # Extract the parameters of the function
            dic = {}
            try:
                dic["center_frequency"] = float(self.parameters["center_frequency"]["line_edit"].text())
                dic["linewidth"] = float(self.parameters["linewidth"]["line_edit"].text())
                dic["normalize"] = bool(self.parameters["normalize"]["checkbox"].checkState())
                dic["c_model"] = str(self.parameters["c_model"]["combobox"].currentText())
                dic["fit_S_and_AS"] = bool(self.parameters["fit_S_and_AS"]["checkbox"].checkState())
                dic["window_peak_find"] = float(self.parameters["window_peak_find"]["line_edit"].text()) 
                dic["window_peak_fit"] = float(self.parameters["window_peak_fit"]["line_edit"].text())
                dic["correct_elastic"] = bool(self.parameters["correct_elastic"]["checkbox"].checkState())
                IR_wndw = self.parameters["IR_wndw"]["line_edit"].text()
                if IR_wndw == "None": 
                    dic["IR_wndw"] = None
                else:
                    dic["IR_wndw"] = IR_wndw.replace("(","").replace(")","").replace(" ","")
                    dic["IR_wndw"] = tuple(map(float, dic["IR_wndw"].split(",")))

                self.parameter_return["Parameters"] = dic
                self.parameter_return["Function"] = func

                qtw.QMessageBox.information(self, "Treatment parameters stored", "The parameters for the treatment have been stored. You can now close the window to apply the treatment.")
            
            except:
                qtw.QMessageBox.warning(self, "Error while retrieving parameters", "An error happened while retrieving the parameters")
            
    def handle_data(self):
        """
        Plots the curve that is currently selected in the combobox. This function also defines self.data and updates the parameters.
        """
        # Extract the raw data from the wrapper corresponding to the selected curve in the combobox
        wrp = self.wrapper
        
        if len(self.combobox_curve_codes) > 1:
            path = self.combobox_curve_codes[self.combobox_curve_names.index(self.cb_curves.currentText())]
            path = path[5:]

            if type(path) == list:
                for e in path:
                    wrp = wrp.data[e]
            else:
                wrp = wrp.data[path]
            
            self.data = wrp.data["Power Spectral Density"]
            if self.path_frequency is None:
                self.frequency = wrp.get_child(self.path_frequency_unique)[:]
            else:
                self.frequency = wrp.get_child(self.path_frequency[self.path_curves.index(path+"/Power Spectral Density")])[:]
            
            # Plot the data
            self.graph_canvas.axes.cla()

            self.graph_canvas.axes.plot(self.frequency, self.data)
            self.graph_canvas.axes.set_xlabel("Frequency Shift (GHz)")
            self.graph_canvas.axes.set_ylabel("Intensity (AU)")
            self.graph_canvas.draw()
            self.update_parameters()

    def update_parameters(self):
        def initialize_parameters(self, module):
            functions = [func for func in getmembers(module, isfunction)]
            function_names = [func[0] for func in functions]
            functions = [func[1] for func in functions]

            self.cb_functions.clear()
            self.cb_functions.addItems(function_names)
            self.cb_functions.setCurrentIndex(0)
            self.cb_functions.currentIndexChanged.connect(lambda: self.show_parameters_function(functions, function_names))

            return functions, function_names

        def setup_button_help_function(self, functions, function_names):
            def show_help_function():
                docstring = functions[function_names.index(self.function_name)].__doc__ or ""
                msgBox = HelpFunction(self, self.function_name, docstring)
                msgBox.exec_()

            self.b_helpFunction.clicked.connect(show_help_function)

        def onclick_x0(event = None):
            if event.inaxes:
                x = float(event.xdata) * 1e6//1
                x = x/1e6
                self.parameters["center_frequency"]["line_edit"].setText(str(x))
        
        def onclick_linewidth(event = None):
            if event.inaxes:
                self.temp_linewidth = float(event.xdata)
                self.graph_canvas.mpl_connect('motion_notify_event', on_drag)

        def on_drag(event):
            if event.inaxes and event.button == 1:
                x1 = float(event.xdata)
                linewidth = abs(x1 - self.temp_linewidth) * 1e6//1
                linewidth = linewidth/1e6
                self.parameters["linewidth"]["line_edit"].setText(str(linewidth))

        # Define the module to be used 
        import HDF5_BLS.treat as module 

        # Extracts the functions and the function names from the module
        self.functions, self.function_names = initialize_parameters(self, module)

        # Sets the combobox with the functions
        self.show_parameters_function(self.functions, self.function_names)

        # Adds the models in the dedicated combobox.
        Models = module.Models()
        self.parameters["c_model"]["combobox"].addItems(Models.models.keys())

        # Connects the QLineEdit widget to the onclick_x0 function
        self.parameters["center_frequency"]["line_edit"].mousePressEvent = lambda event: self.graph_canvas.mpl_connect('button_press_event', onclick_x0)
        
        # Connects the QLineEdit widget to the onclick_linewidth function
        self.parameters["linewidth"]["line_edit"].mousePressEvent = lambda event: self.graph_canvas.mpl_connect('button_press_event', onclick_linewidth)

        # Sets the help button to display the function's docstring
        setup_button_help_function(self, self.functions, self.function_names)
    
    def setup_button_apply(self):
        """
        Creates the layout for the buttons to apply the function.
        """
        layout = qtw.QGridLayout(self.frame_confirmParam)

        button_treat = qtw.QPushButton()
        button_treat.setText("Treat")
        button_treat.clicked.connect(self.apply_function)

        layout.addWidget(button_treat, 0, 0, 1, 1)

    