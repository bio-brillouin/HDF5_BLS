import json
import inspect
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

class Analyze:
    """This class is the base class for all the analyze classes. It provides a common interface for all the classes. Its purpose is to provide the basic silent functions to open, create and save algorithms, and to store the different steps of the analysis and their effects on the data.
    The philosophy of this class is to rely on 4 attributes that will be changed by the different functions of the class:
    - x: the x-axis of the data
    - y: the y-axis of the data
    - points: a list of remarkable points in the data where each point is a 2-list of the form [position, type]
    - windows: a list of windows in the data where each window is a 2-list of the form [start, end]
    And to store the different steps of the analysis and their effects on the data:
    - _algorithm: a dictionary that stores the name of the algorithm, its version, the author, and a description
    - _history: a list that stores the evolution of the 4 main attributes of the class with the steps of the analysis.
    The data is defined by 2 1-D arrays: x and y. Additionally, remarkable points and windows are stored in the points and windows attributes.
    Algorithm steps are stored in 2 attributes: _algorithm and _history. The _algorithm attribute is a dictionary that stores the name of the algorithm, its version, the author, and a description. The _history attribute is a list that stores the steps of the analysis and their effects on the data.
    The _execute attribute is a boolean that indicates whether the analysis should be executed or not. It is set to True by default. The _auto_run attribute is a boolean that indicates whether the analysis should be executed automatically or not. It is set to False by default.
    As a general rule, we encourage developers not to modify any of the underscore-prefixed attributes. These attributes are meant to be used internally by the mother class to run, save, and load the analysis and its history.
    All the functions of the class are functions with a zero-argument call signature that returns None. This means that the parameters of the methods of the children class need to be kew-word arguments, and that if no value for these arguments are given, the default value of the arguments leads the function to do nothing. This specificality ensures the modulability of the class.

    Parameters
    ----------
    x : np.ndarray
        The x-axis of the data.
    y : np.ndarray
        The y-axis of the data.
    points : list of 2-list
        A list of remarkable points in the data where each point is a 2-list of the form [position, type].
    windows : list of 2-list
        A list of windows in the data where each window is a 2-list of the form [start, end].
    _algorithm : dict
        The algorithm used to analyze the data.
    _history : list
        The history of the analysis.
    """
    _record_algorithm = True # This attribute is used to record the steps of the analysis
    _save_history = True # This attribute is used to save the effects of the steps of the analysis on the data

    def __init__(self, y: np.ndarray, x: np.ndarray = None):
        """Initializes the class with the most basic attributes: the ordinates and abscissa of the data.

        Parameters
        ----------
        y : array
            The array of ordinates of the data
        x : array, optional
            The array of abscissa of the data. If None, the abscissa is just the index of the points in ordinates.
        """
        self.y = y
        if x is None:
            self.x = np.arange(y.size)
        else:
            self.x = x
        self.points = []
        self.windows = []
        self._history_base = {"x": x, "y": y}
        self._algorithm = {}

    def __getattribute__(self, name: str):
        """This function is used to override the __getattribute__ function of the class. It is used to keep track of the history of the algorithm, its impact on the classes attributes, and to store the algorithm in the _algorithm attribute so as to be able to save it or run it later.

        Parameters
        ----------
        name : str
            The name of a function of the class.

        Returns
        -------
        The result of the function call.
        """
        # If the attribute is a function, we call it with the given arguments
        attribute = super().__getattribute__(name)
        if callable(attribute) and not name.startswith('_'):
            def wrapper(*args, **kwargs):
                # Extract the description of the function from the docstring
                docstring = inspect.getdoc(attribute)
                description = docstring.split('\n\n')[0] if docstring else ""

                # Get the default parameter values from the function signature
                signature = inspect.signature(attribute)
                default_kwargs = {
                    k: v.default for k, v in signature.parameters.items() if v.default is not inspect.Parameter.empty
                }

                # Merge default kwargs with provided kwargs
                merged_kwargs = {**default_kwargs, **kwargs}

                # If the attribute _record_algorithm is True, add the function to the algorithm
                if self._record_algorithm:
                    self._algorithm["functions"].append({
                        "function": name,
                        "parameters": merged_kwargs,
                        "description": description
                    })

                # Store the attributes of the class in memory to compare them to the ones after the function is run
                if self._save_history:
                    temp_x = self.x.copy()
                    temp_y = self.y.copy()
                    temp_points = [[p, tp] for [p, tp] in self.points]
                    temp_windows = [[s, e] for [s, e] in self.windows]

                # Run the function
                result = attribute(*args, **kwargs)

                # If the attribute _save_history is True, compare the attributes of the class with the ones stored in memory and update the history if needed
                if self._save_history:
                    self._history.append({"function": name})
                    if not np.all(self.x == temp_x):
                        self._history[-1]["x"] = self.x.copy().tolist()
                    if not np.all(self.y == temp_y):
                        self._history[-1]["y"] = self.y.copy().tolist()
                    if self.points != temp_points:
                        if self.points == []:
                            self._history[-1]["points"] = []
                        else:
                            self._history[-1]["points"] = self.points.copy()
                    if self.windows != temp_windows:
                        if self.windows == []:
                            self._history[-1]["windows"] = []
                        else:    
                            self._history[-1]["windows"] = self.windows.copy()
                    if len(self._history) == 1:
                        # This is to store the initial value of the x and y arrays
                        self._history[0].update(self._history_base)
                
                return result
            return wrapper
        return attribute

    def _create_algorithm(self, algorithm_name: str ="Unnamed Algorithm", version: str ="0.1", author: str = "Unknown", description: str = ""):
        """Creates a new JSON algorithm with the given name, version, author and description. This algorithm is stored in the _algorithm attribute. This function also creates an empty history. for the software.

        Parameters
        ----------
        algorithm_name : str, optional
            The name of the algorithm, by default "Unnamed Algorithm"
        version : str, optional
            The version of the algorithm, by default "0.1"
        author : str, optional
            The author of the algorithm, by default "Unknown"
        description : str, optional
            The description of the algorithm, by default ""
        """
        self._algorithm = {
            "name": algorithm_name,
            "version": version,
            "author": author,
            "description": description,
            "functions": []
        } 
        self._history = []

    def _move_step(self, step: int, new_step: int):
        """Moves a step from one position to another in the _algorithm attribute. Deletes the elements of the _history attribute that are after the moved step (included)

        Parameters
        ----------
        step : int
            The position of the function to move in the _algorithm attribute.
        new_step : int
            The new position to move the function to.
        """
        # Moves the step
        self._algorithm["functions"].insert(new_step, self._algorithm["functions"].pop(step))

        # Deletes the elements of the _history attribute that are after the moved step (included)
        if len(self._history) > new_step:
            self._history = self._history[:new_step]

    def _open_algorithm(self, filepath: str =None):
        """Opens an existing JSON algorithm and stores it in the _algorithm attribute. This function also creates an empty history.

        Parameters
        ----------
        filepath : str, optional
            The filepath to the JSON algorithm, by default None
        """
        # Ensures that the filepath is not None
        if filepath is None:
            return 
        
        # Open the JSON file, stores it in the _algorithm attribute and creates an empty history
        with open(filepath, 'r') as f:
            self._algorithm = json.load(f)
        self._history = []

    def _remove_step(self, step: int = None):
        """Removes the step from the _history attribute of the class. If no step is given, removes the last step.

        Parameters
        ----------
        step : int, optional
            The number of the function up to which the algorithm has to be run. Default is None, means that the last step is removed.
        """
        # If no step is given, set the step to the last step
        if step is None:
            step = len(self._algorithm["functions"])-1

        # Ensures that the step is within the range of the functions list
        if step < 0 or step >= len(self._algorithm["functions"]):
            raise ValueError(f"The step parameter has to be a positive integer smaller than the number of functions (here {len(self._algorithm['functions'])}).")
        
        # Removes the step from the _algorithm attribute
        self._algorithm["functions"].pop(step)

        # Removes all steps after the removed step (included) from the _history attribute
        if step == 0:
            self._history = []
        elif len(self._history) >= step:
            self._history = self._history[:step]

    def _run_algorithm(self, step: int = None):
        """Runs the algorithm stored in the _algorithm attribute of the class up to the given step (included). If no step is given, the algorithm is run up to the last step.

        Parameters
        ----------
        step : int, optional
            The number of the function up to which the algorithm has to be run (included), by default None means that all the steps of the algorithm are run.
        """
        def run_step_save_history(self, step):
            """Runs the algorithm stored in the _algorithm attribute of the class. This function can also run up to a specific step of the algorithm.

            Parameters
            ----------
            step : int
                The number of the function up to which the algorithm has to be run.
            """
            self._save_history = True
            function_name = self._algorithm["functions"][step]["function"]
            parameters = self._algorithm["functions"][step]["parameters"]
            if hasattr(self, function_name) and callable(getattr(self, function_name)):
                func_to_call = getattr(self, function_name)
                func_to_call(**parameters)
                        
        def extract_parameters_from_history(self, step):
            """Extracts the parameters from the _history attribute of the class up to the given step.

            Parameters
            ----------
            step : int
                The number of the function up to which the algorithm has to be run.
            """
            # Goes through the steps of the _history attribute up to the given step (excluded) and updates the attributes of the class
            for i in range(step):
                hist_step = self._history[i]
                if "x" in hist_step.keys():
                    self.x = np.array(hist_step["x"])
                if "y" in hist_step.keys():
                    self.y = np.array(hist_step["y"])
                if "points" in hist_step.keys():
                    self.points = hist_step["points"].copy()
                if "windows" in hist_step.keys():
                    self.windows = hist_step["windows"].copy()

        # If the step is None, set the step to the length of the functions list
        if step is None:
            step = len(self._algorithm["functions"])-1

        # Ensures that the step is within the range of the functions list
        if step < 0 or step >= len(self._algorithm["functions"]):
            raise ValueError(f"The step parameter has to be a positive integersmaller than the number of functions (here {len(self._algorithm['functions'])}). The step value given was {step}")

        # Sets the _record_algorithm attribute to False to avoid recording the steps in the _algorithm attributes when running the __getattribute__ function
        self._record_algorithm = False

        # In the particular case where the first step is to be run, we start by retrieving the parameters of the first step from the _history_base attribute, then we remove the first element of the _history attribute and run the functions sequentially from there, up to the given step
        if step == 0:
            # Reinitialize the points and windows attributes
            self.points = []
            self.windows = []

            # Reinitialize the _history attribute
            self._history = []

            # Reinitialize the x and y attributes
            self.x = self._history_base["x"]
            self.y = self._history_base["y"]
            
            # Run the first step
            run_step_save_history(self, 0)

            # Makes sure that the x and y attributes are stored in the history
            if not "x" in self._history[-1].keys(): 
                self._history[-1]["x"] = self.x.copy().tolist()
            if not "y" in self._history[-1].keys(): 
                self._history[-1]["y"] = self.y.copy().tolist()

        # If now we want to run another step, look at the _history attribute to extract the parameters that have been stored up to the current step (or the last step stored in the _history attribute), limit the _history attribute to the current step and run the functions sequentially from there, up to the given step
        else:
            # If we want to execute a step that was previously executed and whose results were stored in the _history attribute:
            if step < len(self._history):
                # Reduce the _history attribute to the given step (excluded)
                self._history = self._history[:step]

                # Extract the parameters from the _history attribute up to the given step (exlucded)
                extract_parameters_from_history(self, step)

            # If now we want to execute a step that is beyond what was previously executed, we need to run all the steps from the last stored step to the given step
            elif step > len(self._history):
                # In the particular case where no steps are stored, we run the first step of the algorithm recursively. This reinitializes the points and windows attributes, the _history attribute, and the x and y attributes
                if len(self._history) == 0:
                    self._run_algorithm(0)
                    first_step = 1

                # If some steps are stored, we update the attributes using the parameters stored in the _history attribute and run from there
                else:
                    extract_parameters_from_history(self, len(self._history))
                    first_step = len(self._history)

                # Run the steps from the last stored step to the given step (excluded)
                for i in range(first_step, step):
                    run_step_save_history(self, i)

            # Run the selected step
            run_step_save_history(self, step)

        self._record_algorithm = True

    def _save_algorithm(self, filepath: str = "algorithm.json", save_parameters: bool = False):
        """Saves the algorithm to a JSON file with or without the parameters used. If the parameters are not saved, their value is set to a default value proper to their type.

        Parameters
        ----------
        filepath : str, optional
            The filepath to save the algorithm to. Default is "algorithm.json".
        save_parameters : bool, optional
            Whether to save the parameters of the functions. Default is False.
        """
    



        # Creates a local dictionary to store the algorithm to save. This allows to reinitiate the parameters if needed.
        algorithm_loc = {}

        # Then go through the keys of the algorithm
        # for k in self._algorithm.keys():
        #     # In particular for functions, if we don't want to save the parameters, we reinitiate them to empty lists or dictionaries
        #     if k == "functions":
        #         algorithm_loc[k] = []
        #         for f in self._algorithm[k]:
        #             algorithm_loc[k].append({})
        #             algorithm_loc[k][-1]["function"] = f["function"]
        #             if not save_parameters:
        #                 for k_param in f["parameters"].keys():
        #                     if type(f["parameters"][k_param]) == list:
        #                         f["parameters"][k_param] = []
        #                     elif type(f["parameters"][k_param]) == dict:
        #                         f["parameters"][k_param] = {}
        #                     else:
        #                         f["parameters"][k_param] = None
        #             algorithm_loc[k][-1]["parameters"] = f["parameters"]
        #             algorithm_loc[k][-1]["description"] = f["description"]
        for k in self._algorithm.keys():
            # In particular for functions, if we don't want to save the parameters, we reinitiate them to empty lists or dictionaries
            if k == "functions":
                algorithm_loc[k] = []
                for f in self._algorithm[k]:
                    algorithm_loc[k].append({})
                    algorithm_loc[k][-1]["function"] = f["function"]
                    if not save_parameters:
                        sgn = inspect.signature(f["function"])
                        for k, v in sgn.parameters.items():
                            if k != "self":
                                f["parameters"][k] = v.default
                    algorithm_loc[k][-1]["parameters"] = f["parameters"].copy()
                    algorithm_loc[k][-1]["description"] = f["description"]
            # Otherwise we just copy the value of the key
            else:
                algorithm_loc[k] = self._algorithm[k]

        # We save the algorithm to the given filepath
        with open(filepath, 'w') as f:
            json.dump(algorithm_loc, f, indent=4)

class Analyze_general(Analyze):
    """This class is a class inherited from the Analyze class used to store steps of analysis that are not specific to a particular type of spectrometer and that are not interesting to show in an algorithm. For example, the function to add a remarkable point to the data
    """
    def __init__(self, y, x = None):
        super().__init__(y = y, x = x)
    
    def _add_point(self, x, type_pnt, window):
        """
        Adds points to the points dictionary and a window to the windows dictionary

        Parameters
        ----------
        x : float
            The x-value of the point.
        type : str
            The type of the point.
        window : tuple
            The window around the point to refine its position
        """
        #Initiate a counter to count the number of these kind of peaks
        i = 0
        for elt in self.points:
            nme = elt[0].split("_")[0]
            if type_pnt == nme:
                i+=1
        
        temp = self._save_history
        self._save_history = False
        # Add the point to the list of points and the list of windows
        self.points.append([f"{type_pnt}_{i}", x])
        self._save_history = temp

        if window[0] < min(self.x):
            window[0] = min(self.x)
        if window[1] > max(self.x):
            window[1] = max(self.x)
        self.windows.append([window[0], window[1]])

    def _clear_points(self):
        """
        Clears the list of points and the list of windows.
        """
        self.points = []
        self.windows = []

    def _refine_peak_position(self, window = None):
        """Refines the position of a peak based on a window surrounding it.

        Parameters
        ----------
        window : list, optional
            The window surrounding the peak. The format is [start, end]. The default is None.

        Returns
        -------
        _type_
            _description_
        """
        # Extract the windowed abscissa and ordinate arrays
        wndw_x = self.x[np.where((self.x >= window[0]) & (self.x <= window[1]))]
        y = self.y
        while len(y.shape) > 1:
            y = np.average(y, axis = 0)
        wndw_y = y[np.where((self.x >= window[0]) & (self.x <= window[1]))]

        # Fit a quadratic polynomial to the windowed data and returns the local extremum
        params = np.polyfit(wndw_x, wndw_y, 2)
        new_x = -params[1]/(2*params[0])
        return new_x

    def _return_string_algorithm(self):
        """Returns a string representation of the algorithm stored in the _algorithm attribute of the class.

        Returns
        -------
        str
            The string representation of the algorithm.
        """
        return json.dumps(self._algorithm, indent=4)

class Analyze_VIPA(Analyze_general):
    """This class is a child class of Analyze_general. It inherits all the methods of the parent class and adds the functions specific to VIPA spectrometers.
    """
    def __init__(self, x, y):
        super().__init__(x = x, y = y)

        self._algorithm = {
            "name": "VIPA spectrum analyzer",
            "version": "0.0",
            "author": "None",
            "description": "A blank algorithm for VIPA spectrometers.",
            "functions": []
        } 
        self._history = []

    def add_point(self, position_center_window: float = 0, window_width: float = 0, type_pnt: str = "Elastic"):
        """
        Adds a single point to the list of points together with a window to the list of windows with its type. Each point is an intensity extremum obtained by fitting a quadratic polynomial to the windowed data.
        The point is given as a value on the x axis (not a position).
        The "position_center_window" parameter is the center of the window surrounding the peak. The "window_width" parameter is the width of the window surrounding the peak (full width). The "type_pnt" parameter is the type of the peak. It can be either "Stokes", "Anti-Stokes" or "Elastic".
        
        Parameters
        ----------
        position_center_window : float
            A value on the self.x axis corresponding to the center of a window surrounding a peak
        window : float
            A value on the self.x axis corresponding to the width of a window surrounding a peak
        type_pnt : str
            The nature of the peak. Must be one of the following: "Stokes", "Anti-Stokes" or "Elastic"
        """

        # Base case: if any of the parameters is None, return
        if window_width == 0:
            return

        # Check that the type of the point is correct
        if type_pnt not in ["Stokes", "Anti-Stokes", "Elastic"]:
            raise ValueError(f"The type of the point must be one of the following: 'Stokes', 'Anti-Stokes' or 'Elastic'. Here the value given was '{type_pnt}'")

        # Check that the window is in the range of the data
        window = [position_center_window-window_width/2, position_center_window+window_width/2]
        if window[1]<self.x[0] or window[0]>self.x[-1]:
            raise ValueError(f"The window {window} is out of the range of the data")
        
        # Ensure that the window is within the range of the data
        window[0] = max(self.x[0], window[0])
        window[1] = min(self.x[-1], window[1])

        # Refine the position of the peaks
        new_x = self._refine_peak_position(window = window)

        # Add the point to the list of points and the list of windows using the silent method
        self._add_point(new_x, type_pnt, window)
        
    def center_x_axis(self, center_type: str = None):
        """
        Centers the x axis using the first points stored in the class. The parameter "center_type" is used to determine wether to center the axis using the first elastic peak (center_type = "Elastic") or the average of two Stokes and Anti-Stokes peaks (center_type = "Inelastic").

        Parameters
        ----------
        center_type: str
            The type of the peak to center the x axis around. Must be either "Elastic" or "Inelastic".
        """
        # Base case: if center_type is None, return
        if center_type is None:
            return 
        
        # Check that type is either "Elastic" or "Inelastic" 
        if center_type not in ["Elastic", "Inelastic"]:
            raise ValueError("The attribute 'center_type' must be either 'Elastic' or 'Inelastic'")
       
        # If type is "Elastic", center the x axis around the elastic peak or raise an error if there is no elastic peak
        if center_type == "Elastic":
            not_in_list = True
            for point in self.points:
                name, value = point
                if name == "Elastic_0":
                    v_E = value
                    not_in_list = False
                    break
            if not_in_list:
                raise ValueError("There is no elastic peak stored in the class")
            else:
                self.x = self.x - v_E
        # If type is "Inelastic", center the x axis around the average of the Stokes and Anti-Stokes peaks or raise an error if there is no Stokes and Anti-Stokes peaks
        else:
            not_in_list_AS = True
            not_in_list_S = True
            for point in self.points:
                name, value = point
                if name == "Stokes_0":
                    v_S = value
                    not_in_list_S = False
                elif name == "Anti-Stokes_0":
                    v_AS = value
                    not_in_list_AS = False
            if not_in_list_AS or not_in_list_S:
                raise ValueError("There are no Stokes and Anti-Stokes peaks stored in the class")
            else:
                self.x = self.x - v_S/2 - v_AS/2
        
        
        # Clear the points and windows
        self._clear_points()
        
        # Return the x axis if the user wants to use it
        return self.x

    def interpolate_elastic_inelastic(self, shift: float = None, FSR: float = None):
        """
        Uses the elastic peaks, and the positions of the Brillouin peaks on the different orders to obtain a frequency axis by interpolating the position of the peaks with a quadratic polynomial. The user can either enter a value for the shift or the FSR, or both. The shift value is used to calibrate the frequency axis using known values of shifts when using a calibration sample to obtain the frequency axis. The FSR value is used to calibrate the frequency axis using a known values of FSR for the VIPA.

        Parameters
        ----------  
        shift : float
            The shift between the elastic and inelastic peaks (in GHz).
        FSR : float
            The free spectral range of the VIPA spectrometer (in GHz).
        """
        def get_order(AS, S, E):
            AS_order = []
            for p in AS:
                temp = 0
                for i in range(len(E)):
                    e = E[i]
                    if abs(p-e)<abs(p-E[temp]):
                        temp = i
                AS_order.append(temp)

            if len(AS_order) > 2:
                if AS_order[-1] == AS_order[-2]:
                    AS.pop(-1)
                    AS_order.pop(-1)

            S_order = []
            for p in S:
                temp = 0
                for i in range(len(E)):
                    e = E[i]
                    if abs(p-e)<abs(p-E[temp]):
                        temp = i
                S_order.append(temp)

            if len(S_order) > 2:
                if S_order[-1] == S_order[-2]:
                    S.pop(-1)
                    S_order.pop(-1)

            return AS_order, S_order

        def create_matrices(AS, S, E, AS_order, S_order):
            # Create the matrices that will be used to minimize the second order polynomial
            A = []
            B = []
            C = []
            # Ensuring that the difference between antistokes and stokes is the same for all orders
            i = max(min(AS_order), min(S_order))
            while i <= min(max(AS_order), max(S_order))-1:
                AS_0 = AS[AS_order.index(i)]
                S_0 = S[S_order.index(i)]
                AS_1 = AS[AS_order.index(i+1)]
                S_1 = S[S_order.index(i+1)]
                A.append(AS_1**2 - S_1**2 - AS_0**2 + S_0**2)
                B.append(AS_1 - S_1 - AS_0 + S_0)
                C.append(0)
                i+=1
            if FSR is not None:
                #Ensuring that the distance between two neighboring stokes peaks is one FSR
                for i in range(len(S)-1):
                    A.append(S[i+1]**2 - S[i]**2)
                    B.append(S[i+1] - S[i])
                    C.append(-FSR)
                #Ensuring that the distance between two neighboring anti-stokes peaks is one FSR
                for i in range(len(AS)-1):
                    A.append(AS[i+1]**2 - AS[i]**2)
                    B.append(AS[i+1] - AS[i])
                    C.append(-FSR)
                #Ensuring that the distance between two neighboring elastic peaks is one FSR
                for i in range(len(E)-1):
                    A.append(E[i+1]**2 - E[i]**2)
                    B.append(E[i+1] - E[i])
                    C.append(-FSR)
            elif shift is not None:
                i = max(min(AS_order), min(S_order))
                while i <= min(max(AS_order), max(S_order)):
                    AS = AS[AS_order.index(i)]
                    S = S[S_order.index(i)]
                    A.append(AS**2 + S**2)
                    B.append(AS - S)
                    C.append(shift)
                    i+=1
            return A, B, C

        def error(params):
            a, b, c = params
            return np.sum((a * A + b * B + c + C) ** 2)

        if shift is None and FSR is None:
            return
        
        # Start by extracting the stokes, anti-Stokes and elastic peaks
        E, S, AS = [], [], []
        for point in self.points:
            name, value = point
            if name[0] == "E":
                E.append(value)
            elif name[0] == "S":
                S.append(value)
            elif name[0] == "A":
                AS.append(value)

        AS_order, S_order = get_order(AS, S, E)
        
        A, B, C = create_matrices(AS, S, E, AS_order, S_order)
       
        # Converting the lists to numpy arrays
        A = np.array(A)
        B = np.array(B)
        C = np.array(C)
        # Defining the minimization function
        if FSR is None:
            result = minimize(error, [0, 1, 0], method='SLSQP')
        else: 
            result = minimize(error, [0, max(max(AS_order), max(S_order))*FSR/self.x.size, 0], method='SLSQP')
        
        a, b, c = result.x

        # Now we can create the new x axis
        self.x = a*self.x**2 + b*self.x + c

        # Clear the points and windows
        self._clear_points()

        # Return the x axis if the user wants to use it
        return self.x

    def interpolate_between_one_order(self, FSR: float = None):
        """
        Creates a frequency axis by using the signal between two elastic peaks included. By imposing that the distance in frequency between two neighboring elastic peaks is one FSR, and that the shift of both stokes and anti-stokes peaks to their respective elastic peak is the same, we can obtain a frequency axis. The user has to enter a value for the FSR to calibrate the frequency axis.

        Parameters
        ----------  
        FSR : float
            The free spectral range of the VIPA spectrometer (in GHz).
        """
        if FSR is None:
            return
        
        # Start by extracting the elastic peaks
        E, AS, S = [], [], []
        for point in self.points:
            name, value = point
            if name[0] == "E":
                E.append(value)
            elif name[0] == "A":
                AS.append(value)
            elif name[0] == "S":
                S.append(value)
        
        if len(AS) != 1:
            raise ValueError("There must be exactly one anti-Stokes peak to use this function.")
        if len(S) != 1:
            raise ValueError("There must be exactly one Stokes peak to use this function.")

        E.sort()

        x0 = E[0]
        x1 = S[0]
        x2 = AS[0]
        x3 = E[1]

        # Create the matrices that will be used to minimize the second order polynomial
        temp = x3**2 - x2**2 - x1**2 + x0**2
        denom = (x3**2-x0**2)*(x1-x0-x3+x2) + (x3-x0)*(x3**2-x2**2-x1**2+x0**2)
        b =  FSR*temp/denom

        a = (FSR-b*(x3-x0))/(x3**2-x0**2)

        f = lambda freq: a*freq**2 + b*freq
        c = -f(x0)  

        # Now we can create the new x axis
        self.x = a*self.x**2 + b*self.x + c

        # Clear the points and windows
        self._clear_points()

        # Return the x axis if the user wants to use it
        return self.x

    def interpolate_elastic(self, FSR: float = None):
        """
        Uses positions of the elastic peaks on the different orders, to obtain a frequency axis by interpolating the position of the peaks with a quadratic polynomial. The user has to enter a value for the FSR to calibrate the frequency axis.

        Parameters
        ----------  
        FSR : float
            The free spectral range of the VIPA spectrometer (in GHz).
        """
        def create_matrices(E):
            # Create the matrices that will be used to minimize the second order polynomial
            A = []
            B = []
            C = []
            for i in range(len(E)-1):
                A.append(E[i+1]**2 - E[i]**2)
                B.append(E[i+1] - E[i])
                C.append(-FSR)
            return A, B, C

        def error(params):
            a, b, c = params
            return np.sum((a * A + b * B + c + C) ** 2)

        if FSR is None:
            return
        
        # Start by extracting the stokes, anti-Stokes and elastic peaks
        E = []
        for point in self.points:
            name, value = point
            if name[0] == "E":
                E.append(value)
        
        E.sort()

        A, B, C = create_matrices(E)
       
        # Converting the lists to numpy arrays
        A = np.array(A)
        B = np.array(B)
        C = np.array(C)
        # Defining the minimization function
        result = minimize(error, [0, len(E)*FSR/self.x.size, 0], method='SLSQP')
        
        a, b, c = result.x

        # Now we can create the new x axis
        self.x = a*self.x**2 + b*self.x + c

        # Clear the points and windows
        self._clear_points()

        # Return the x axis if the user wants to use it
        return self.x


# Example Usage
if __name__ == "__main__":
    import h5py

    with h5py.File("/Users/pierrebouvet/Documents/Databases/2504 - Measures fixed cells/Test.h5", "r") as f:
        data = np.array(f["Brillouin/HCU29/HCU29 - 1/Acq 1/Raw data"][()])
    
    average = data
    while len(average.shape) > 1:
        average = np.average(average, axis = 0)

    analyzer = Analyze_VIPA(x = np.arange(average.size), y = average)
   
    # analyzer._create_algorithm(algorithm_name="VIPA spectrum analyzer", 
    #                            version="v0", 
    #                            author="Pierre Bouvet", 
    #                            description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")
    # analyzer.add_point(position_center_window=12, type_pnt="Elastic", window_width=5)
    # analyzer.add_point(position_center_window=37, type_pnt="Anti-Stokes", window_width=5)
    # analyzer.add_point(position_center_window=236, type_pnt="Stokes", window_width=5)
    # analyzer.add_point(position_center_window=259, type_pnt="Elastic", window_width=5)
    # analyzer.add_point(position_center_window=282, type_pnt="Anti-Stokes", window_width=5)
    # analyzer.add_point(position_center_window=466, type_pnt="Stokes", window_width=5)
    # analyzer.add_point(position_center_window=488, type_pnt="Elastic", window_width=5)
    # analyzer.add_point(position_center_window=509, type_pnt="Anti-Stokes", window_width=5)
    # analyzer.interpolate_elastic_inelastic(FSR = 60)
    # analyzer.add_point(position_center_window=57, type_pnt="Stokes", window_width=1)
    # analyzer.add_point(position_center_window=68.5, type_pnt="Anti-Stokes", window_width=1)
    # analyzer.center_x_axis(center_type = "Inelastic")

    # analyzer._save_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/Test.json", save_parameters=True)
    
    analyzer._open_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/MUW_PB_VIPA_FSR_Shift_v0.json")
    analyzer._run_algorithm()
    
    plt.plot(analyzer.x, analyzer.y)
    plt.show()

    # analyzer._print_algorithm()


    