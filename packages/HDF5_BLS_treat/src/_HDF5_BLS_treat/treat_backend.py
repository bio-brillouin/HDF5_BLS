import numpy as np
import json
import inspect
from functools import wraps

def record_algorithm(func):
    """Decorator to record the function call in the algorithm and history.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Extract the description of the function from the docstring
        docstring = inspect.getdoc(func)
        description = docstring.split('\n\n')[0] if docstring else ""

        # Get the default parameter values from the function signature
        signature = inspect.signature(func)
        
        # Handle positional arguments if they are passed as such
        # This is a bit tricky if we want to store them by name in the JSON
        params = signature.bind(self, *args, **kwargs)
        params.apply_defaults()
        recorded_params = params.arguments.copy()
        if 'self' in recorded_params:
            del recorded_params['self']

        # If the attribute _record_algorithm is True, add the function to the algorithm
        if self._record_algorithm:
            name = func.__name__
            # If the same function has already been run in the algorithm, change the description to "See previous run"
            if name in [f["function"] for f in self._algorithm["functions"]]:
                description = "See previous run"

            self._algorithm["functions"].append({
                "function": name,
                "parameters": recorded_params,
                "description": description
            })

        # Store the attributes of the class in memory to compare them to the ones after the function is run
        treat_selection = getattr(self, "_treat_selection", None)
        if treat_selection == "sampled":
            temp_PSD_sample = self.PSD_sample.copy()
            temp_frequency_sample = self.frequency_sample.copy()
            temp_points = self.points.copy()
            temp_windows = self.windows.copy()

        # Run the function
        result = func(self, *args, **kwargs)

        # If the attribute _save_history is True, compare the attributes of the class with the ones stored in memory and update the history if needed
        if treat_selection == "sampled":
            self._history.append({"function": func.__name__})
            if not np.all(self.PSD_sample == temp_PSD_sample):
                self._history[-1]["PSD_sample"] = self.PSD_sample.copy().tolist()
            if not np.all(self.frequency_sample == temp_frequency_sample):
                self._history[-1]["frequency_sample"] = self.frequency_sample.copy().tolist()
            if self.points != temp_points:
                self._history[-1]["points"] = self.points.copy()
            if self.windows != temp_windows:
                self._history[-1]["windows"] = self.windows.copy()
        
        return result
    return wrapper

def record_class_methods(cls):
    """Class decorator to apply record_algorithm to all public methods.
    """
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if not name.startswith('_') and not name.startswith('silent_') and name != '__init__':
            setattr(cls, name, record_algorithm(method))
    return cls

@record_class_methods
class Treat_backend:
    """This class is the base class for all the treat classes. Its purpose is to provide the basic silent functions to open, create and save algorithms, and to store the different steps of the treatment and their effects on the data.
    """
    _record_algorithm = True # This attribute is used to record the steps of the analysis

    def __init__(self, frequency: np.ndarray, PSD: np.ndarray, frequency_sample_dimension = None):
        """Initializes the class by storing the PSD and frequency arrays. Also initializes the sample sub-arrays using the frequency_sample_dimension parameter.
        """
        # Initialize the algorithm and history
        self._algorithm = {
            "name": "Algorithm",
            "version": "v0",
            "author": "No author",
            "description": "No description",
            "functions": []
        } 
        
        # Initializing the attributes that will store the fitted values on sample arrays.
        self.shift_sample = []
        self.shift_err_sample = []
        self.linewidth_sample = []
        self.linewidth_err_sample = []
        self.amplitude_sample = []
        self.amplitude_err_sample = []
        self.offset_sample = []
        self.slope_sample = []

        # Intializing the estimators and fit model
        self.width_estimator = []
        self.fit_model = None

        # Initializing the global attributes 
        self.shift = None
        self.linewidth = None
        self.shift_var = None
        self.linewidth_var = None
        self.amplitude = None
        self.amplitude_var = None
        self.offset = None

        # Initializing points and windows of interest
        self.points = []
        self.windows = []

        # Initializes the progress callback
        self._progress_callback = None

    def silent_clear_points(self):
        """
        Clears the list of points and the list of windows.
        """
        self.points = []    
        self.windows = []

    def silent_create_algorithm(self, algorithm_name: str ="Unnamed Algorithm", version: str ="0.1", author: str = "Unknown", description: str = "", new_algorithm = False):
        """Creates a new JSON algorithm with the given name, version, author and description. This algorithm is stored in the _algorithm attribute. This function also creates an empty history. for the software.
        """
        if new_algorithm:
            self._algorithm["functions"] = []
            self._history = []
        self._algorithm = {
            "name": algorithm_name,
            "version": version,
            "author": author,
            "description": description,
            "functions": self._algorithm["functions"]
        } 

    def silent_move_step(self, step: int, new_step: int):
        """Moves a step from one position to another in the _algorithm attribute. Deletes the elements of the _history attribute that are after the moved step (included)
        """
        # Moves the step
        self._algorithm["functions"].insert(new_step, self._algorithm["functions"].pop(step))

        # Deletes the elements of the _history attribute that are after the moved step (included)
        if len(self._history) > new_step:
            self._history = self._history[:new_step]

    def silent_open_algorithm(self, filepath: str =None):
        """Opens an existing JSON algorithm and stores it in the _algorithm attribute. This function also creates an empty history.
        """
        # Ensures that the filepath is not None
        if filepath is None:
            return 
        
        # Open the JSON file, stores it in the _algorithm attribute and creates an empty history
        with open(filepath, 'r') as f:
            self._algorithm = json.load(f)
        self._history = []

    def silent_remove_step(self, step: int = None):
        """Removes the step from the _history attribute of the class. If no step is given, removes the last step.
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

    def silent_return_string_algorithm(self):
        """Returns a string representation of the algorithm stored in the _algorithm attribute of the class.
        """
        return json.dumps(self._algorithm, indent=4)

    def silent_run_algorithm(self, step: int = None, algorithm: dict = None):
        """Runs an algorithm. By default, the algorithm run is the one stored in the _algorithm attribute of the class. This function can also run other algorithms if specified. The function runs the algorithm up to the given step (included). If no step is given, the algorithm is run up to the last step (included). 
        """
        def extract_parameters_from_history(self, step):
            """Extracts the parameters from the _history attribute of the class up to the given step.
            """
            # Goes through the steps of the _history attribute up to the given step (excluded) and updates the attributes of the class
            for i in range(step):
                hist_step = self._history[i]
                if "PSD_sample" in hist_step.keys():
                    self.PSD_sample = np.array(hist_step["PSD_sample"])
                if "frequency_sample" in hist_step.keys():
                    self.frequency_sample = np.array(hist_step["frequency_sample"])
                if "points" in hist_step.keys():
                    self.points = hist_step["points"].copy()
                if "windows" in hist_step.keys():
                    self.windows = hist_step["windows"].copy()

        def run_step(self, step):
            """Runs the algorithm stored in the _algorithm attribute of the class. This function can also run up to a specific step of the algorithm.
            """
            function_name = algorithm["functions"][step]["function"]
            parameters = algorithm["functions"][step]["parameters"]
            if hasattr(self, function_name) and callable(getattr(self, function_name)):
                func_to_call = getattr(self, function_name)
                func_to_call(**parameters)

        # If the algorithm is None, set the algorithm to the _algorithm attribute of the class
        if algorithm is None:
            algorithm = self._algorithm

        # If the step is None, set the step to the length of the functions list
        if step is None:
            step = len(algorithm["functions"])-1

        # Ensures that the step is within the range of the functions list, raise an error if not
        if step < 0 or step >= len(algorithm["functions"]):
            raise ValueError(f"The step parameter has to be a positive integersmaller than the number of functions (here {len(algorithm['functions'])}, step = {step}).")

        # Sets the _record_algorithm attribute to False to avoid recording the steps in the _algorithm attributes when running the __getattribute__ function
        self._record_algorithm = False

        # If the _treat_selection attribute is set to "sampled", we store the steps in history to reduce algorithmic complexity
        if self._treat_selection == "sampled":
            # In the particular case where the first step is to be run, we start by retrieving the parameters of the first step from the _history_base attribute, then we remove the first element of the _history attribute and run the functions sequentially from there, up to the given step
            if step == 0:
                # Reinitialize the points and windows attributes
                self.points = []
                self.windows = []

                # Reinitialize the _history attribute
                self._history = []

                # Reinitialize the sampled frequency and PSD arrays
                self.frequency_sample = self._history_base["frequency_sample"]
                self.PSD_sample = self._history_base["PSD_sample"]
                
                # Run the first step
                run_step(self, 0)

                # Makes sure that the x and y attributes are stored in the history
                if not "frequency_sample" in self._history[-1].keys(): 
                    self._history[-1]["frequency_sample"] = self.frequency_sample.copy().tolist()
                if not "PSD_sample" in self._history[-1].keys(): 
                    self._history[-1]["PSD_sample"] = self.PSD_sample.copy().tolist()

            # If now we want to run another step, look at the _history attribute to extract the parameters that have been stored up to the current step (or the last step stored in the _history attribute), limit the _history attribute to the current step and run the functions sequentially from there, up to the given step
            else:
                # If we want to execute a step that was previously executed and whose results were stored in the _history attribute:
                if step <= len(self._history):
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
                        run_step(self, i)

                # Run the selected step
                run_step(self, step)

        # If the _treat_selection attribute is set to "all" or "errors", the _history attribute is not used and the functions are run sequentially from the first step to the given step (included)
        elif self._treat_selection in ["all", "errors"]:
            for s in range(step+1):
                run_step(self, s)

        self._record_algorithm = True

    def silent_save_algorithm(self, filepath: str = "algorithm.json", save_parameters: bool = False):
        """Saves the algorithm to a JSON file with or without the parameters used. If the parameters are not saved, their value is set to a default value proper to their type.
        """
        # Creates a local dictionnary to store the algorithm to save. This allows to reinitiate the parameters if needed.
        algorithm_loc = {}

        # Then go through the keys of the algorithm
        for k in self._algorithm.keys():
            # In particular for functions, if we don't want to save the parameters, we reinitiate them to empty lists or dictionaries
            if k == "functions":
                algorithm_loc[k] = []
                for f in self._algorithm[k]:
                    algorithm_loc[k].append({})
                    algorithm_loc[k][-1]["function"] = f["function"]
                    if not save_parameters:
                        for k_param in f["parameters"].keys():
                            if type(f["parameters"][k_param]) == list:
                                f["parameters"][k_param] = []
                            elif type(f["parameters"][k_param]) == dict:
                                f["parameters"][k_param] = {}
                            else:
                                f["parameters"][k_param] = None
                    algorithm_loc[k][-1]["parameters"] = f["parameters"]
                    algorithm_loc[k][-1]["description"] = f["description"]
            # Otherwise we just copy the value of the key
            else:
                algorithm_loc[k] = self._algorithm[k]

        # We save the algorithm to the given filepath
        with open(filepath, 'w') as f:
            json.dump(algorithm_loc, f, indent=4)
