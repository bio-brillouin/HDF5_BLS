import json
import inspect
import numpy as np

class Analyse_backend:
    """This class is the base class for all the analyse classes. It provides a common interface for all the classes. Its purpose is to provide the basic silent functions to open, create and save algorithms, and to store the different steps of the analysis and their effects on the data.
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
        The algorithm used to analyse the data.
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
        if callable(attribute) and not name.startswith('_') and not name.startswith('silent_'):
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

    def silent_create_algorithm(self, algorithm_name: str ="Unnamed Algorithm", version: str ="0.1", author: str = "Unknown", description: str = ""):
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

    def silent_move_step(self, step: int, new_step: int):
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

    def silent_open_algorithm(self, filepath: str = None, algorithm_str: str = ""):
        """Opens an existing JSON algorithm and stores it in the _algorithm attribute. This function also creates an empty history.

        Parameters
        ----------
        filepath : str, optional
            The filepath to the JSON algorithm, by default None
        """        
        # Delete the _algorithm attribute
        try:
            del self._algorithm
        except: 
            pass

        # Open the JSON file, stores it in the _algorithm attribute and creates an empty history
        if filepath is None:
            if algorithm_str == "":
                return
            else:
                self._algorithm = json.loads(algorithm_str)
        else:
            with open(filepath, 'r') as f:
                self._algorithm = json.load(f)
        self._history = []

    def silent_remove_step(self, step: int = None):
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

    def silent_run_algorithm(self, step: int = None):
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
                    self.silent_run_algorithm(0)
                    first_step = 1
                    self._record_algorithm = False

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

    def silent_save_algorithm(self, filepath: str = "algorithm.json", save_parameters: bool = False):
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

    def set_x_y(self, x, y):
        """
        Sets the x and y values of the data

        Parameters
        ----------
        x : array-like
            The x values of the data
        y : array-like
            The y values of the data
        """
        self.x = x
        self.y = y
