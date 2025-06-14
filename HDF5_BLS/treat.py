import numpy as np
from scipy import optimize
import json
import inspect

Treat_version = 0.1

class TreatmentError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Models():
    """
    This class repertoriates all the models that can be used for the fit.
    """

    models = {}

    def __init__(self):
        self.models["Lorentzian"] = lambda nu, b, a, nu0, gamma, IR=None: self.lorentzian(nu, b, a, nu0, gamma, IR)
        self.models["Lorentzian elastic"] = lambda nu, be, a, nu0, gamma, ae, IR=None: self.lorentzian_elastic(nu, ae, be, a, nu0, gamma, IR)
        self.models["DHO"] = lambda nu, b, a, nu0, gamma, IR=None: self.DHO(nu, b, a, nu0, gamma, IR)
        self.models["DHO elastic"] = lambda nu, be, a, nu0, gamma, ae, IR=None: self.DHO_elastic(nu, ae, be, a, nu0, gamma, IR)
        
    def lorentzian(self, nu, b, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        b : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func = b + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
        if IR is not None: return np.convolve(func, IR, "same")
        return func
    
    def lorentzian_elastic(self, nu, ae, be, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        ae : float
            The slope of the first order Taylor expansion of the elastic peak at the position of the peak fitted
        be : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func =  be + ae*nu + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
        if IR is not None: return np.convolve(func, IR, "same")
        return func
    
    def DHO(self, nu, b, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        b : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func = b + a*(gamma*nu0**2)/((nu**2-nu0**2)**2+gamma*nu**2)
        if IR is not None: return np.convolve(func, IR, "same")
        return func 
    
    def DHO_elastic(self, nu, ae, be, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        ae : float
            The slope of the first order Taylor expansion of the elastic peak at the position of the peak fitted
        be : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func = be + ae*nu + a*(gamma*nu0**2)/((nu**2-nu0**2)**2+gamma*nu**2)
        if IR is not None: return np.convolve(func, IR, "same")
        return func
 
class Treat_backend:
    """This class is the base class for all the treat classes. Its purpose is to provide the basic silent functions to open, create and save algorithms, and to store the different steps of the treatment and their effects on the data.
    The philosophy of this class is to rely on 2 fixed attributes:
    - frequency: the array of frequency axis corresponding to the PSD
    - PSD: the array of power spectral density to be treated
    And to update the following attributes:
    - shift: the shift array obtained after the treatment
    - shift_var: the array of standard deviation of the shift array obtained after the treatment
    - linewidth: the linewidth array obtained after the treatment
    - amplitude: the amplitude array obtained after the treatment
    This treatment is performed on the whole PSD array using the following attributes:
    - shift_ini: the list of initial guesses for the shift on which to perform the treatment
    - linewidth_ini: the list of initial guesses for the linewidth on which to perform the treatment
    - window_peak_find: the list of windows around the peak on which the treatment is performed
    
    The treatment itself is stored in the _algorithm attribute and each change to a classe's attribute is stored in the _history attribute:
    - _algorithm: a dictionary that stores the name of the algorithm, its version, the author, and a description
    - _record_algorithm: a boolean that indicates whether the algorithm should be recorded or not while running the functions of the class

    When a treatment fails or is identified as not well fitted, the class stores the information in the following attributes:
    - point_errors: the list of points that are not well fitted

    Additionally, the class uses sub-attributes to test the treatment on particular spectra. These sub-attributes are:
    - frequency_sample: A 1-D sampled frequency array
    - PSD_sample: A 1-D sampled PSD array
    - selected_sample : the index of the selected element in the PSD array
    - shift_sample: A list of shift values obtained on the sampled PSD array
    - linewidth_sample: A list of linewidth values obtained on the sampled PSD array
    - amplitude_sample: A list of amplitude values obtained on the sampled PSD array    
    - shift_ini_sample: A list of shift values obtained on the sampled PSD array
    - linewidth_ini_sample: A list of linewidth values obtained on the sampled PSD array
    - amplitude_ini_sample: A list of amplitude values obtained on the sampled PSD array  
    For treating these samples, the class offers an argument to store the steps of the treatment. This is stored in the _history attribute.
    - _history: a list that stores the evolution of the attributes 
    
    To switch the class between the treatment of all the PSD array, sampled PSD arrays or error points, we use the attribute:
    - _treat_selection: a string that directs the treatment towards the whole PSD array, sampled PSD arrays or error points with the following options:
        - all: the whole PSD array is treated
        - sampled: the sampled PSD arrays are treated
        - errors: the error points are treated
    Note that the _history attribute is implemented only if _treat_selection is set to "sampled".

    Parameters
    ----------
    frequency : np.ndarray
        The array of frequency axis corresponding to the PSD
    PSD : np.ndarray
        The array of power spectral density to be treated
    shift : np.ndarray
        The shift array obtained after the treatment
    linewidth : np.ndarray
        The linewidth array obtained after the treatment
    amplitude : np.ndarray
        The amplitude array obtained after the treatment
    shift_var : np.ndarray
        The array of standard deviation of the shift array obtained after the treatment
    linewidth_var : np.ndarray
        The array of standard deviation of the linewidth array obtained after the treatment
    amplitude_var : np.ndarray
        The array of standard deviation of the amplitude array obtained after the treatment
    point_errors : list
        The list of points that are not well fitted
    shift_ini : list
        The list of initial guesses for the shift on which to perform the treatment
    linewidth_ini : list
        The list of initial guesses for the linewidth on which to perform the treatment
    window_peak_find : list
        The list of windows around the peak on which the treatment is performed
    _algorithm : dict
        The algorithm used to analyze the data.
    frequency_sample : np.ndarray
        The array of frequency axis corresponding to the PSD
    PSD_sample : np.ndarray
        The array of power spectral density to be treated
    shift_sample : list
        A list of shift values obtained on the sampled PSD array
    linewidth_sample : list
        A list of linewidth values obtained on the sampled PSD array
    amplitude_sample : list
        A list of amplitude values obtained on the sampled PSD array    
    shift_ini_sample : list
        A list of shift values obtained on the sampled PSD array
    linewidth_ini_sample : list
        A list of linewidth values obtained on the sampled PSD array
    amplitude_ini_sample : list
        A list of amplitude values obtained on the sampled PSD array    
    """
    _record_algorithm = True # This attribute is used to record the steps of the analysis

    def __init__(self, frequency: np.ndarray, PSD: np.ndarray, frequency_sample_dimension = None):
        """Initializes the class by storing the PSD and frequency arrays. Also initializes the sample sub-arrays using the frequency_sample_dimension parameter.

        Parameters
        ----------
        frequency : np.ndarray
            An array corresponding to the frequency axis of the PSD
        PSD : np.ndarray
            An array corresponding to the power spectral density to treat
        frequency_sample_dimension : tuple, optional
            The tuple leading to the 1-D array to use as frequency axis. By default, the first dimension of the frequency is used.
        """
        # Initialize the algorithm and history
        self._algorithm = {}
        self._history = []

        # Initializing main attributes
        self.frequency = frequency
        self.PSD = PSD

        # Initializing treatment applicator selection attributes
        self._treat_selection = "sampled"

        # Initializing array sample attributes WARNING: ONLY 1D frequency arrays are supported for now
        if len(self.frequency.shape) == 1:
            self.frequency_sample = self.frequency
            self.PSD_sample = self.PSD
            while len(self.PSD_sample.shape) > 1:
                self.PSD_sample = np.average(self.PSD_sample, axis = 0) 
        else:
            raise ValueError("Only 1D frequency arrays are supported for now")

        # Store the base arrays
        self._history_base = {"frequency_sample": self.frequency_sample,
                            "PSD_sample": self.PSD_sample}

        # Initializing the attributes that will store the fitted values on sample arrays.
        self.shift_sample = []
        self.shift_std_sample = []
        self.linewidth_sample = []
        self.linewidth_std_sample = []
        self.amplitude_sample = []
        self.amplitude_std_sample = []
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

        # Initializing points and windows of interest
        self.points = []
        self.windows = []

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

        # If the attribute is a function, and its name doesn't start with an underscore, we run the intermediate function "wrapper"
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
                    # If the same function has already been run in the algorithm, change the description to "See previous run"
                    if name in [func["function"] for func in self._algorithm["functions"]]:
                        description = "See previous run"

                    self._algorithm["functions"].append({
                        "function": name,
                        "parameters": merged_kwargs,
                        "description": description
                    })

                # Store the attributes of the class in memory to compare them to the ones after the function is run
                if self._treat_selection == "sampled":
                    temp_PSD_sample = self.PSD_sample.copy()
                    temp_frequency_sample = self.frequency_sample.copy()
                    temp_points = self.points.copy()
                    temp_windows = self.windows.copy()

                # Run the function
                result = attribute(*args, **kwargs)

                # If the attribute _save_history is True, compare the attributes of the class with the ones stored in memory and update the history if needed
                if self._treat_selection == "sampled":
                    self._history.append({"function": name})
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
        return attribute

    def _clear_points(self):
        """
        Clears the list of points and the list of windows.
        """
        self.points = []    
        self.windows = []

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

    def _return_string_algorithm(self):
        """Returns a string representation of the algorithm stored in the _algorithm attribute of the class.

        Returns
        -------
        str
            The string representation of the algorithm.
        """
        return json.dumps(self._algorithm, indent=4)

    def _run_algorithm(self, step: int = None, algorithm: dict = None):
        """Runs an algorithm. By default, the algorithm run is the one stored in the _algorithm attribute of the class. This function can also run other algorithms if specified. The function runs the algorithm up to the given step (included). If no step is given, the algorithm is run up to the last step (included). 

        Parameters
        ----------
        step : int, optional
            The number of the function up to which the algorithm has to be run (included), by default None means that all the steps of the algorithm are run.
        algorithm : dict, optional
            The algorithm to be run. If None, the algorithm stored in the _algorithm attribute is used. Default is None.
        """
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
                if "PSD_sample" in hist_step.keys():
                    self.PSD_sample = np.array(hist_step["PSD_sample"])
                if "frequency_sample" in hist_step.keys():
                    self.frequency_sample = np.array(hist_step["frequency_sample"])

        def run_step(self, step):
            """Runs the algorithm stored in the _algorithm attribute of the class. This function can also run up to a specific step of the algorithm.

            Parameters
            ----------
            step : int
                The number of the function up to which the algorithm has to be run.
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
                if step < len(self._history):
                    # Reduce the _history attribute to the given step (excluded)
                    self._history = self._history[:step]

                    # Extract the parameters from the _history attribute up to the given step (exlucded)
                    extract_parameters_from_history(self, step)

                # If now we want to execute a step that is beyond what was previously executed, we need to run all the steps from the last stored step to the given step
                elif step > len(self._history):
                    # In the particular case where no steps are stored, we run the first step of the algorithm recursively. This reinitializes the points and windows attributes, the _history attribute, and the x and y attributes
                    if len(self._history) == 0:
                        self._run_algorithm(step = 0)
                        first_step = 1

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

    def _save_algorithm(self, filepath: str = "algorithm.json", save_parameters: bool = False):
        """Saves the algorithm to a JSON file with or without the parameters used. If the parameters are not saved, their value is set to a default value proper to their type.

        Parameters
        ----------
        filepath : str, optional
            The filepath to save the algorithm to. Default is "algorithm.json".
        save_parameters : bool, optional
            Whether to save the parameters of the functions. Default is False.
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

class Treat(Treat_backend):
    """This class is a class inherited from the Treat_backend class used to define functions to treat the data. Each function is meant to perform the minimum of operation so as to give the user a total control over the treatment. 
    """
    def __init__(self, frequency, PSD):
        super().__init__(frequency = frequency, PSD = PSD)

        self._algorithm = {
            "name": "Brillouin treatment",
            "version": "0.0",
            "author": "None",
            "description": "A blank algorithm for treating BLS spectra.",
            "functions": []
        } 

    def add_point(self, position_center_window: float = None, window_width: float = None, type_pnt: str = "Other"):
        """
        Adds a single point to the list of points together with a window to the list of windows with its type. Each point is an intensity extremum obtained by fitting a quadratic polynomial to the windowed data.
        The point is given as a value on the frequency axis (not a position on this axis).
        The "position_center_window" parameter is the center of the window surrounding the peak. The "window_width" parameter is the width of the window surrounding the peak (full width). The "type_pnt" parameter is the type of the peak. It can be either "Stokes", "Anti-Stokes", "Elastic" or "Other".
        
        Parameters
        ----------
        position_center_window : float
            A value on the self.x axis corresponding to the center of a window surrounding a peak
        window : float
            A value on the self.x axis corresponding to the width of a window surrounding a peak
        type_pnt : str
            The nature of the peak. Must be one of the following: "Other","Stokes", "Anti-Stokes" or "Elastic"
        """

        def refine_peak_position(frequency, PSD, window):
            """Refines the position of a peak based on a window surrounding it. The refining is done by finding the maximum of the windowed data, interpolating the gradient around this maximum, and then finding the position of the maximum based on a zero gradient.

            Parameters
            ----------
            window : list
                The window surrounding the peak. The format is [start, end].
            """
            # Extract the windowed abscissa and ordinate arrays
            pos = np.where((frequency >= window[0]) & (frequency <= window[1]))
            wndw_x = frequency[pos] 
            wndw_y = PSD[pos]

            # Fit a quadratic polynomial to the windowed data and returns the local extremum
            params = np.polyfit(wndw_x, wndw_y, 2)
            new_x = -params[1]/(2*params[0])

            return new_x

        # Base case: if any of the parameters is None, return
        if position_center_window is None or window_width is None or type_pnt is None:
            return

        # Check that the type of the point is correct
        if type_pnt not in ["Other", "Stokes", "Anti-Stokes", "Elastic"]:
            raise ValueError("The type of the point must be one of the following: 'Stokes', 'Anti-Stokes' or 'Elastic'")

        # Check that the window is in the range of the data
        window = [position_center_window-window_width/2, position_center_window+window_width/2]
        if window[1]<self.frequency_sample[0] or window[0]>self.frequency_sample[-1]:
            raise ValueError(f"The window {window} is out of the range of the data")

        # Ensure that the window is within the range of the data
        window[0] = max(self.frequency_sample[0], window[0])
        window[1] = min(self.frequency_sample[-1], window[1])

        # Refine the position of the peaks
        new_x = refine_peak_position(frequency = self.frequency_sample, PSD = self.PSD_sample, window = window)

        # Goes through the list of points to get the number of occurences of peaks of same type
        i = 0
        for elt in self.points:
            nme = elt[0].split("_")[0]
            if type_pnt == nme:
                i+=1
        
        # Add the point to the list of points and the list of windows
        self._save_history = False
        self.points.append([f"{type_pnt}_{i}", new_x])

        # Add the window to the list of windows
        self.windows.append([window[0], window[1]])
    
    def add_window(self, position_center_window: float = None, window_width: float = None):
        """
        Adds a single window to the list of windows together with the central point (with type "Window") to the list of windows. 
        The positions are given as values on the frequency axis (not a position).
        The "position_center_window" parameter is the center of the window surrounding the peak. The "window_width" parameter is the width of the window surrounding the peak (full width).
        
        Parameters
        ----------
        position_center_window : float
            A value on the self.x axis corresponding to the center of a window surrounding a peak
        window : float
            A value on the self.x axis corresponding to the width of a window surrounding a peak
        """

        # Base case: if any of the parameters is None, return
        if position_center_window is None or window_width is None:
            return

        # Check that the window is in the range of the data
        window = [position_center_window-window_width/2, position_center_window+window_width/2]
        if window[1]<self.frequency_sample[0] or window[0]>self.frequency_sample[-1]:
            raise ValueError(f"The window {window} is out of the range of the data")

        # Ensure that the window is within the range of the data
        window[0] = max(self.frequency_sample[0], window[0])
        window[1] = min(self.frequency_sample[-1], window[1])

        # Set the central point of the window
        new_x = (window[0] + window[1])/2

        # Goes through the list of points to get the number of occurences of peaks of same type
        i = 0
        for elt in self.points:
            nme = elt[0].split("_")[0]
            if nme == "Window":
                i+=1
        
        # Add the point to the list of points and the list of windows
        self._save_history = False
        self.points.append([f"Window_{i}", new_x])

        # Add the window to the list of windows
        self.windows.append([window[0], window[1]])
    
    def apply_algorithm_on_all(self, amplitude_weight_of_shift_and_linewidth: bool = True, keep_max_amplitude: bool = True):
        """
        Takes all the steps of the algorithm up to the moment this function is called and applies the steps to each individual spectrum in the dataset. 
        This function updates the global attributes of the class concerning the shift, the linewidth and the amplitude together with their variance, taking into account error propagation. 
        If a spectrum could not be fitted, its value is set to 0 in the global attributes.
        All the points where the spectra could not be fitted are marked with the "fit_error_marker" parameter in the global attributes (shift, linewidth, amplitude, shift_var, linewidth_var, amplitude_var) and their coordinates are stored in the "point_error" list. The "point_error_type" attribute is also updated with the type of error returned by the fit function (see scipy.optimize.curve_fit documentation). The function returns the number of spectra that could not be fitted.

        Parameters
        ----------
        fit_error_marker : float or None, optional
            The marker to use to mark the points where the spectra could not be fitted. Default is None.
        amplitude_weight_of_shift_and_linewidth : bool, optional
            If True, the amplitude of the spectra is used to weight the shift and linewidth. If set to false, a simple average is performed. Default is True.
        keep_max_amplitude : bool, optional
            If True, maximum of the peak amplitude is stored in the amplitude array. If False, an average of all the amplitudes is stored. Default is True.
        """
        def plus_one(shape, max_shape, dim):
            if dim == -1: 
                return None
            if shape[dim] == max_shape[dim]-1:
                shape[dim] = 0
                return plus_one(shape, max_shape, dim-1)
            else:
                shape[dim] += 1
                return shape

        def initialize():    
            # Initialize the list of points that could not be fitted
            self.point_error = []
            self.point_error_type = []
            self.point_error_value = []

            # Initialize the list of fitted points
            self.shift = np.zeros(self.PSD.shape[:-1]).astype(float)
            self.linewidth = np.zeros(self.PSD.shape[:-1]).astype(float)
            self.shift_var = np.zeros(self.PSD.shape[:-1]).astype(float)
            self.linewidth_var = np.zeros(self.PSD.shape[:-1]).astype(float)
            self.amplitude = np.zeros(self.PSD.shape[:-1]).astype(float)        
            self.amplitude_var = np.zeros(self.PSD.shape[:-1]).astype(float)

            # Initialize the index of the selected spectrum
            return np.zeros(len(self.PSD.shape[:-1])).astype(int)

        # Initialize the list of fitted points, error point and index of selected spectrum
        PSD_i = initialize()

        # Set the treat selection to "all"
        self._treat_selection = "all"

        # Remove the last step of the algorithm (corresponding to this function)
        temp_algorithm = self._algorithm["functions"][-1]
        self._algorithm["functions"] = self._algorithm["functions"][:-1]

        # Sets the frequency array to the main frequency array (assuming 1D frequency array)
        self.frequency_sample = self.frequency

        # Iterate on each spectrum of the PSD array
        while PSD_i is not None:
            # Assign the current PSD and frequency arrays to the corresponding variables
            self.PSD_sample = self.PSD[tuple(PSD_i)]

            # Run the algorithm on the current PSD and frequency arrays
            self._run_algorithm()

            # Combine the results of the algorithm to get an average value for the shift and linewidth and store them
            temp_shift, temp_linewidth, temp_shift_std, temp_linewidth_std, temp_amplitude, temp_amplitude_std = 0, 0, 0, 0, 0, 0
            nb = 0

            if amplitude_weight_of_shift_and_linewidth:
                for a, s, l,std_s, std_l, std_a in zip(self.amplitude_sample, self.shift_sample, self.linewidth_sample, self.shift_std_sample, self.linewidth_std_sample, self.amplitude_std_sample):
                    if not a == np.nan:
                        if keep_max_amplitude and a > temp_amplitude:
                            temp_amplitude, temp_amplitude_std = a, std_a
                        else:
                            temp_amplitude += a
                            temp_amplitude_std += (a*std_a)**2
                        temp_shift += a*np.abs(s)
                        temp_linewidth += a*l
                        temp_shift_std += (a*std_s)**2
                        temp_linewidth_std += (a*std_l)**2
                        nb += 1
                if keep_max_amplitude:
                    self.amplitude[tuple(PSD_i)] = temp_amplitude
                    self.amplitude_var[tuple(PSD_i)] = temp_amplitude_std
                else:
                    self.amplitude[tuple(PSD_i)] = temp_amplitude/nb
                    self.amplitude_var[tuple(PSD_i)] = np.sqrt(temp_amplitude_std)/(nb**2)
                self.shift[tuple(PSD_i)] = temp_shift/np.sum(self.amplitude_sample)
                self.linewidth[tuple(PSD_i)] = temp_linewidth/np.sum(self.amplitude_sample)
                self.shift_var[tuple(PSD_i)] = np.sqrt(temp_shift_std)/np.sum(self.amplitude_sample)**2
                self.linewidth_var[tuple(PSD_i)] = np.sqrt(temp_linewidth_std)/np.sum(self.amplitude_sample)**2
            else:
                self.shift[tuple(PSD_i)] = np.nanmean(np.abs(self.shift_sample))
                self.linewidth[tuple(PSD_i)] = np.nanmean(self.linewidth_sample)
                self.shift_var[tuple(PSD_i)] = np.sqrt(np.nansum(np.array(self.shift_std_sample)**2)) / (np.count_nonzero(~np.isnan(self.amplitude_sample))**2)
                self.linewidth_var[tuple(PSD_i)] = np.sqrt(np.nansum(np.array(self.linewidth_std_sample)**2))/(np.count_nonzero(~np.isnan(self.amplitude_sample))**2)
            
            if np.isnan(self.shift[tuple(PSD_i)]):
                self.point_error.append(PSD_i.copy())
                self.point_error_type.append("fit_error")
                self.point_error_value.append(np.nan)

            PSD_i = plus_one(PSD_i, self.PSD.shape[:-1], len(PSD_i)-1)
        
        self.BLT = self.linewidth/self.shift
        self.BLT_var = self.BLT**2*((self.shift_var/self.shift)**2 + (self.linewidth_var/self.linewidth)**2)

        self._algorithm["functions"].append(temp_algorithm)

    def estimate_width_inelastic_peaks(self, max_width_guess : float = 2):
        """Estimates the full width at half maximum of the inelastic peaks stored in self.points. Note that the data is supposed to be normalized.

        Parameters
        ----------
        max_width_guess : float, optional
            The higher limit to the estimation of the full width. Default is 2 GHz.
        """
        # Initiate the width estimator
        self.width_estimator = []

        # Extract the points corresponding either to Stokes or Anti-Stokes peaks
        for i in range(len(self.points)):
            if self.points[i][0].split("_")[0] in ["Anti-Stokes", "Stokes"]:
                p = self.points[i][1]
    
                # Extract the peak position
                pos_peak = np.argmin(np.abs(self.frequency_sample - p))

                # Guess the width of the peak by finding the points at half the height
                pos_half = pos_peak
                while pos_half>0:
                    if self.PSD_sample[pos_half] > self.PSD_sample[pos_peak]/2:
                        pos_half = pos_half-1
                    else:
                        break
                gamma = self.frequency_sample[pos_half]

                pos_half = pos_peak
                while pos_half<len(self.frequency_sample)-1:
                    if self.PSD_sample[pos_half] > self.PSD_sample[pos_peak]/2:
                        pos_half = pos_half+1
                    else:
                        break
                gamma = min(max_width_guess, self.frequency_sample[pos_half] - gamma)

                self.width_estimator.append(gamma)
            else:
                self.width_estimator.append(0)

    def define_model(self, model: str = "Lorentzian", elastic_correction: bool = False):
        """Defines the model to be used to fit the data.

        Parameters
        ----------
        model : str, optional
            The model to be used. The models should match the names of the attribute "models" of the class Models, by default "Lorentzian"
        elastic_correction : bool, optional
            Whether to correct for the presence of an elastic peak by setting adding a linear function to the model, by default False
        """
        if elastic_correction:
            model = model + " elastic"

        # Try selecting the model, raise an error if the model is not found
        Model = Models()
        try:
            self.fit_model = model
        except:
            raise ValueError(f"The model {model} is not recognized.")

    def fit_all_inelastic_of_curve(self, default_width: float = 1, guess_offset: bool = False, update_point_position: bool = True, bound_shift: list = None, bound_linewidth: list = None):
        """
        Fits a lineshape to the data using the points stored as Stokes or Anti-Stokes peaks in the points attribute. The linewidth can be estimated beforehand using the function estimate_width_inelastic_peaks. If not estimated, a fixed width is used (default_width). The offset can also be guessed or not (guess_offset). In the case the offset is guessed, the minimum of the data on the selected window is used as an initial guess. The position of the peak can also be updated based on the fitted shift if update_point_position is set to True. If set to False, the positions are not updated.

        Parameters
        ----------
        default_width : float, optional
            If the width has not been estimated, the default width to use, by default 1 GHz
        guess_offset : bool, optional
            If True, the offset is guessed based on the minimum of the data on the selected window. If false, the data is supposed to be normalized and the offset guess is set to 0, by default False
        update_point_position : bool, optional
            If True, the position of the peak is updated based on the fitted shift. If False, the position of the peak is not updated, by default True
        bound_shift : list, optional
            The lower and upper bounds of the shift, by default None means no restrictions are applied
        bound_linewidth : list, optional
            The lower and upper bounds of the linewidth, by default None means no restrictions are applied
        """
        def reinitialize_fitted_list():
            self.shift_sample = []
            self.shift_std_sample = []
            self.linewidth_sample = []
            self.linewidth_std_sample = []
            self.amplitude_sample = []
            self.amplitude_std_sample = []
            self.offset_sample = []
            self.slope_sample = []
        
        def extract_point_window_gammaGuess():
            peaks, windows, guess_gamma = [], [], []
            for i in range(len(self.points)):
                if self.points[i][0].split("_")[0] in ["Anti-Stokes", "Stokes"]:
                    peaks.append(self.points[i][1])
                    windows.append(self.windows[i])
                    if len(self.width_estimator) > 0:
                        guess_gamma.append(self.width_estimator[i])
                    else:
                        guess_gamma.append(default_width)
            return peaks, windows, guess_gamma

        def update_results(popt = None, pcov = None, all_nan=False):
            if all_nan:
                popt = [np.nan for i in range(5)]
                pcov = [[np.nan for i in range(5)] for i in range(5)]
            self.offset_sample.append(popt[0])
            self.amplitude_sample.append(popt[1])
            self.shift_sample.append(popt[2])
            self.linewidth_sample.append(np.abs(popt[3]))
            if "elastic" in self.fit_model:
                self.slope_sample.append(popt[4])

            self.amplitude_std_sample.append(np.sqrt(pcov[1][1]))
            self.shift_std_sample.append(np.sqrt(pcov[2][2]))
            self.linewidth_std_sample.append(np.sqrt(pcov[3][3]))

        # Initializes the list of fitted parameters 
        reinitialize_fitted_list()

        # If the user wants to correct for the presence of an elastic peak, we add " elastic" to the name of the model to use
        if self.fit_model is None:
            raise ValueError("The model has not been defined. Please use the function 'define_model' to define the model before calling 'fit_all_inelastic_of_curve'.")
    
        # Extract the points to fit, select only the ones of type Stokes or Anti-Stokes. Also extract the guess for the width of the peaks or if it is not defined, use the default width
        peaks, windows, guess_gamma = extract_point_window_gammaGuess()
        
        # Fit each peak that has been selected
        for peak, window, gamma in zip(peaks, windows, guess_gamma):
            # Extract the peak position and the window around the peak
            pos_peak = np.argmin(np.abs(self.frequency_sample - peak))
            pos_window = np.where((self.frequency_sample >= window[0]) & (self.frequency_sample <= window[1]))

            # Guess the amplitude of the peak by selecting its intensity
            amplitude_guess = self.PSD_sample[pos_peak]

            # Set the offset guess to the minimum of the intensity array on the selected window or to 0
            if guess_offset:
                offset_guess = np.min(self.PSD_sample[pos_window])
            else: 
                offset_guess = 0

            # Check if we want to correct for the presence of an elastic peak and apply the fitting
            models = Models()

            if "elastic" in self.fit_model:
                # Estimate the slope from the first and last points of the window
                slope_guess = (self.PSD_sample[pos_window[0][-1]] - self.PSD_sample[pos_window[0][0]])/(self.frequency_sample[pos_window[0][-1]] - self.frequency_sample[pos_window[0][0]])

                # Adjust the offset accordingly
                if self.PSD_sample[pos_window[0][0]] < self.PSD_sample[pos_window[0][-1]]:
                    offset_guess = offset_guess - slope_guess*self.frequency_sample[pos_window[0][0]]
                else:
                    offset_guess = offset_guess - slope_guess*self.frequency_sample[pos_window[0][-1]]
                
                # Adjust the amplitude accordingly
                amplitude_guess = amplitude_guess - offset_guess - slope_guess * (self.frequency_sample[pos_peak])

                error_fit = False
                try:
                    popt, pcov = optimize.curve_fit(models.models[self.fit_model], 
                                                    self.frequency_sample[pos_window], 
                                                    self.PSD_sample[pos_window], 
                                                    p0=[offset_guess, amplitude_guess, peak, gamma, slope_guess])
                except:
                    error_fit = True
            else:
                error_fit = False
                try:
                    popt, pcov = optimize.curve_fit(models.models[self.fit_model], 
                                                    self.frequency_sample[pos_window], 
                                                    self.PSD_sample[pos_window], 
                                                    p0=[offset_guess, amplitude_guess, peak, gamma])
                except:
                    error_fit = True

            # If the fit succeeded, check that the bounds are not violated and update the parameters, if not store np.nan
            if not error_fit:
                if bound_shift is not None:
                    if abs(popt[2]) < bound_shift[0] or abs(popt[2]) > bound_shift[1]: 
                        error_fit = True
                
                if bound_linewidth is not None:
                    if popt[3] < bound_linewidth[0] or popt[3] > bound_linewidth[1]:
                        error_fit = True
                update_results(popt, pcov)
            else:
                update_results(all_nan = True)

            # Update the points with the fitted shift of the peak.
            if update_point_position:
                for i, elt in enumerate(self.points):                
                    if elt[1] == peak:
                        index = i
                        pos_peak = self.shift_sample[-1]
                        self.points[index][1] = pos_peak
                        break

    def blind_deconvolution(self, default_width: float = None):
        """Subtracts a constant width to all the linewidth array and recomputes the BLT array. If default_width is not specified, the width is estimated by fitting a Lorentzian to the most proeminent elastic peak. If no elastic peak are specified, and default_width is not specified, no deconvolution is performed.

        Parameters
        ----------
        default_width : float, optional 
            The value of the width to subtract to the linewidth array, by default None. If None, the width is estimated by fitting a Lorentzian to the most proeminent elastic peak.
        """
        # If default_width is not specified, we estimate the width by fitting a Lorentzian to the most proeminent elastic peak
        if default_width is None:
            # Extract the peaks that are not elastic or not windows
            peaks = [p[1] for p in self.points if p[0][0] == "E"]
            windows = [k for p, k in zip(self.points, self.windows) if p[0][0] == "E"]

            # Return if there are no peaks
            if len(peaks) == 0:
                return

            # Select the most proeminent peak
            sel = 0
            I = 0
            for i, p in enumerate(peaks):
                pos = np.argmin(np.abs(self.frequency_sample - p))
                if self.PSD_sample[pos] > I:
                    sel = i
                    I = self.PSD_sample[pos]
            peak = peaks[sel]
            window = windows[sel]

            # Estimate the width of the peaks
            models = Models()
            lorentzian = models.models["Lorentzian"]

            # Fit the peak
            try:
                popt, pcov = curve_fit(lorentzian, self.frequency_sample[window[0]:window[1]], self.PSD_sample[window[0]:window[1]], p0=[0, I, peak, 1])
            except:
                return
            
            default_width = popt[3]
        
        self.linewidth = self.linewidth-default_width
        self.BLT = self.linewidth/self.shift

    def mark_errors_shift(self, min_shift: float = 0, max_shift: float = 10):
        """Marks the points that present a value of shift above or below given thresholds.

        Parameters
        ----------
        min_shift: float, optional
            The threshold below which the shift is marked as an error , by default 0GHz
        max_shift: float, optional
            The threshold above which the shift is marked as an error , by default 10GHz
        """
        positions = np.where(self.shift > max_shift)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("shift_max")
            self.point_error_value.append(self.shift[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

        positions = np.where(self.shift < min_shift)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("shift_min")
            self.point_error_value.append(self.shift[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

    def mark_errors_std_shift(self, max_error_shift_variance: float = 0.005):
        """Marks the points that present a variance of the shift greater than a certain threshold.

        Parameters
        ----------
        max_error_shift_std : float, optional
            The threshold above which the shift is marked as an error , by default 5MHz
        """
        positions = np.where(self.shift_var > max_error_shift_variance)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("shift_var")
            self.point_error_value.append(self.shift_var[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

    def mark_errors_linewidth(self, min_linewidth: float = 0, max_linewidth: float = 10):
        """Marks the points that present a value of linewidth above or below given thresholds.

        Parameters
        ----------
        min_linewidth: float, optional
            The threshold below which the linewidth is marked as an error , by default 0GHz
        max_linewidth: float, optional
            The threshold above which the linewidth is marked as an error , by default 10GHz
        """
        positions = np.where(self.linewidth > max_linewidth)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("linewidth_max")
            self.point_error_value.append(self.linewidth[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

        positions = np.where(self.linewidth < min_linewidth)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("linewidth_min")
            self.point_error_value.append(self.linewidth[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

    def mark_errors_std_linewidth(self, max_error_linewidth_variance: float = 0.005):
        """Marks the points that present a variance of the linewidth greater than a certain threshold.

        Parameters
        ----------
        max_error_linewidth_variance : float, optional
            The threshold above which the linewidth is marked as an error , by default 5MHz
        """
        positions = np.where(self.linewidth_var > max_error_linewidth_variance)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("linewidth_var")
            self.point_error_value.append(self.linewidth_var[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

    def mark_errors_BLT(self, min_BLT: float = 0, max_BLT: float = 10):
        """Marks the points that present a value of BLT above or below given thresholds.

        Parameters
        ----------
        min_shift: float, optional
            The threshold below which the shift is marked as an error , by default 0GHz
        max_shift: float, optional
            The threshold above which the shift is marked as an error , by default 10GHz
        """
        positions = np.where(self.BLT > max_BLT)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("BLT_max")
            self.point_error_value.append(self.BLT[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

        positions = np.where(self.BLT < min_BLT)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("BLT_min")
            self.point_error_value.append(self.BLT[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

    def mark_errors_std_BLT(self, max_error_BLT_variance: float = 0.005):
        """Marks the points that present a variance of the BLT greater than a certain threshold.

        Parameters
        ----------
        max_error_shift_std : float, optional
            The threshold above which the shift is marked as an error , by default 5MHz
        """
        positions = np.where(self.BLT_var > max_error_BLT_variance)
        for i in range(len(positions[0])):
            pos = [int(p[i]) for p in positions]
            self.point_error.append(pos)
            self.point_error_type.append("BLT_var")
            self.point_error_value.append(self.BLT_var[tuple(pos)])
        self.shift_var[positions] = np.nan
        self.shift[positions] = np.nan
        self.linewidth_var[positions] = np.nan   
        self.linewidth[positions] = np.nan
        self.amplitude_var[positions] = np.nan
        self.amplitude[positions] = np.nan
        self.BLT_var[positions] = np.nan
        self.BLT[positions] = np.nan

    def mark_point_error(self, position : list):
        """ Forces a point located at the position "position" to be considered as an error.

        Parameters
        ----------
        position : list
            The position of the point error to be marked.

        Returns
        -------
        None
        """
        self.point_error.append(position)
        self.point_error_type.append("point_error")
        self.point_error_value.append(np.nan)
        self.shift_var[tuple(position)] = np.nan
        self.shift[tuple(position)] = np.nan
        self.linewidth_var[tuple(position)] = np.nan   
        self.linewidth[tuple(position)] = np.nan
        self.amplitude_var[tuple(position)] = np.nan
        self.amplitude[tuple(position)] = np.nan
        self.BLT_var[tuple(position)] = np.nan
        self.BLT[tuple(position)] = np.nan

    def adjust_treatment_on_errors(self, position = None, new_parameters = None):
        """ Reapplies the treatment on the point error located at the position "position" with the new parameters "new_parameters".

        Parameters
        ----------
        position : list, optional
            The position of the point error to be adjusted. Default is None.
        new_parameters : list of dictionnaries, optional 
            The list of new parameters to be applied to re-run the treatment on the errors. Each element is either None (if we don't change the parameters) or a dictionnary of the parameters to be passed to the function. Default is None, means that all the parameters used earlier are used.
        """
        def extract_initial_algorithm():
            algorithm = {"functions": []}
            mark_errors_algorithm = {"functions": []}
            passed_apply_on_all = False
            # We go through the functions that are applied 
            for f in self._algorithm["functions"]:
                # If we are not applying the algorithm to all the data
                if not f["function"] == "apply_algorithm_on_all":
                    # If the function is before the apply_algorithm_on_all function, we add it to the algorithm
                    if not passed_apply_on_all:
                        algorithm["functions"].append(f)
                    # If it's after but before the adjust_treatment_on_errors function, we add it to the mark_errors as it will be used to mark errors
                    else:
                        if not f["function"] == "adjust_treatment_on_errors":
                            mark_errors_algorithm["functions"].append(f)
                        else:
                            break
                else:
                    amplitude_weight_of_shift_and_linewidth = f["parameters"]["amplitude_weight_of_shift_and_linewidth"]
                    keep_max_amplitude = f["parameters"]["keep_max_amplitude"]
                    passed_apply_on_all = True
            return algorithm, mark_errors_algorithm, amplitude_weight_of_shift_and_linewidth, keep_max_amplitude

        def update_treated_arrays(PSD_i, amplitude_weight_of_shift_and_linewidth, keep_max_amplitude):
            # If we want to update the arrays with values weighted by the amplitude of the peak
            if amplitude_weight_of_shift_and_linewidth:
                temp_shift = 0
                temp_linewidth = 0
                temp_shift_std = 0
                temp_linewidth_std = 0
                temp_amplitude = 0
                temp_amplitude_std = 0
                nb = 0
                for a, s, l,std_s, std_l, std_a in zip(self.amplitude_sample, self.shift_sample, self.linewidth_sample, self.shift_std_sample, self.linewidth_std_sample, self.amplitude_std_sample):
                    if not a == np.nan:
                        if keep_max_amplitude:
                            if a > temp_amplitude:
                                temp_amplitude = a
                                temp_amplitude_std = std_a
                        else:
                            temp_amplitude += a
                            temp_amplitude_std += (a*std_a)**2
                        temp_shift += a*np.abs(s)
                        temp_linewidth += a*l
                        temp_shift_std += (a*std_s)**2
                        temp_linewidth_std += (a*std_l)**2
                        nb += 1
                if keep_max_amplitude:
                    self.amplitude[tuple(PSD_i)] = temp_amplitude
                    self.amplitude_var[tuple(PSD_i)] = temp_amplitude_std
                else:
                    self.amplitude[tuple(PSD_i)] = temp_amplitude/nb
                    self.amplitude_var[tuple(PSD_i)] = np.sqrt(temp_amplitude_std)/(nb**2)
                self.shift[tuple(PSD_i)] = temp_shift/np.sum(self.amplitude_sample)
                self.linewidth[tuple(PSD_i)] = temp_linewidth/np.sum(self.amplitude_sample)
                self.shift_var[tuple(PSD_i)] = np.sqrt(temp_shift_std)/np.sum(self.amplitude_sample)**2
                self.linewidth_var[tuple(PSD_i)] = np.sqrt(temp_linewidth_std)/np.nansusumm(self.amplitude_sample)**2
            # If we don't weigh the values by the amplitude of the peak
            else:
                self.shift[tuple(PSD_i)] = np.nanmean(np.abs(self.shift_sample))
                self.linewidth[tuple(PSD_i)] = np.nanmean(self.linewidth_sample)
                self.shift_var[tuple(PSD_i)] = np.sqrt(np.sum(np.array(self.shift_std_sample)**2)) / (np.count_nonzero(~np.isnan(self.amplitude_sample))**2)
                self.linewidth_var[tuple(PSD_i)] = np.sqrt(np.sum(np.array(self.linewidth_std_sample)**2))/(np.count_nonzero(~np.isnan(self.amplitude_sample))**2)
            
        # Extract the algorithm that was used to initially treat the data, the one used to mark the errors and the parameters used to store the extracted values
        algorithm, mark_errors, amplitude_weight_of_shift_and_linewidth, keep_max_amplitude = extract_initial_algorithm()

        # Update the parameters with the new values
        new_algorithm = {"functions": []}
        if not new_parameters is None:
            for i in range(len(algorithm["functions"])):
                if new_parameters[i] is None:
                    new_algorithm["functions"].append(algorithm["functions"][i])
                elif new_parameters[i] == False:
                    continue
                elif new_parameters[i] is not None:
                    for k, v in new_parameters[i].items():
                        if k in algorithm["functions"][i]["parameters"].keys():
                            algorithm["functions"][i]["parameters"][k] = v
                    new_algorithm["functions"].append(algorithm["functions"][i])
        
        # If no position are specified, we apply the algorithm on all the points that had errors
        if position is None:
            position = self.point_error
        
        # Sets the _treat_selection attribute to "errors". This makes sure that the algorithm doesn't store the results in _history (reduces the memory usage and time complexity)
        self._treat_selection = "errors"
        
        # Apply the algorithm on all the points that had errors
        for PSD_i in position:
            self.PSD_sample = self.PSD[tuple(PSD_i)]
            self._run_algorithm(algorithm = new_algorithm)

            update_treated_arrays(PSD_i, amplitude_weight_of_shift_and_linewidth, keep_max_amplitude)
        
        # Update the Loss Tangent array and its variance
        self.BLT = self.linewidth/self.shift
        self.BLT_var = self.BLT**2*((self.shift_var/self.shift)**2 + (self.linewidth_var/self.linewidth)**2)

        # And we mark the errors again.
        self.point_error = []
        self.point_error_type = []
        self.point_error_value = []
        self._run_algorithm(algorithm = mark_errors)

    def normalize_data(self, threshold_noise : float = 0.01):
        """
        Normalizes the data by identifying the regions corresponding to noise, substracting the average of these regions from the data, and dividing by the average of the amplitude of all peaks that are not of type elastic.

        Parameters
        ----------
        threshold_noise : float, optional
            The threshold for identifying noise regions. This value is the highest possible value for noise relative to the average intensity of the selected peaks, on the PSD when the minimal value of the PSD is brought to 0. Default is 1%

        Returns
        -------
        None
        """
        # Subtract the lowest value of intensity to PSD_sample
        self.PSD_sample = self.PSD_sample - np.min(self.PSD_sample)

        # Extract the peaks that are not elastic or not windows
        peaks = [p[1] for p in self.points if p[0][0] not in ["E", "W"]]

        # Calculate the average intensity of the peaks
        position_peaks = np.array([np.argmin(np.abs(self.frequency_sample - p)) for p in peaks])
        average_intensity_peaks = np.average(self.PSD_sample[position_peaks])

        # Get all regions corresponding to noise (i.e. regions with intensity below 10% of the average intensity of the peaks)
        noise_regions = []
        for i in range(len(self.PSD_sample)):
            if self.PSD_sample[i] < average_intensity_peaks * threshold_noise:
                noise_regions.append(i)
        
        # Get average noise value
        average_noise = np.average(self.PSD_sample[noise_regions])

        # Normalize the data
        self.PSD_sample = self.PSD_sample - average_noise
        self.PSD_sample = self.PSD_sample / average_intensity_peaks

        # Clear the points and windows stored in the class
        self._clear_points()

        return self.PSD_sample
   
    