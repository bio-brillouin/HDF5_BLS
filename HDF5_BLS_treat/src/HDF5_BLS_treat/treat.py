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
        self.models["Gaussian"] = lambda nu, b, a, nu0, gamma, IR=None: self.gaussian(nu, b, a, nu0, gamma, IR)

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
        func = b + a * (gamma*nu0)**2/((nu**2-nu0**2)**2+(gamma*nu)**2)
        # This is to only generate one peak and not a doublet
        if np.sign(nu0) == -1: 
            func = func*(nu<=0)
        else: 
            func = func*(nu>=0)
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
        func = ae*nu + self.DHO(nu, be, a, nu0, gamma)
        if IR is not None: return np.convolve(func, IR, "same")
        return func
  
    def gaussian(self, nu, b, a, nu0, gamma, IR = None):
        """Model of a simple gaussian lineshape
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
        gamma = 2*np.log(2)/gamma
        func = b + a*np.exp(-(nu-nu0)**2/(2*gamma**2))
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
    - linewidth_var: the array of standard deviation of the linewidth array obtained after the treatment
    - amplitude: the amplitude array obtained after the treatment
    - amplitude_var: the array of standard deviation of the amplitude array obtained after the treatment

    The treatment itself is stored in the _algorithm attribute and each change to a classe's attribute is stored in the _history attribute:
    - _algorithm: a dictionary that stores the name of the algorithm, its version, the author, and a description
    - _record_algorithm: a boolean that indicates whether the algorithm should be recorded or not while running the functions of the class

    When a treatment fails or is identified as not well fitted, the class stores the information in the following attributes:
    - point_errors: the list of points that are not well fitted

    Additionally, the class uses sub-attributes to test the treatment on particular spectra. These sub-attributes are:
    - frequency_sample: A 1-D sampled frequency array
    - PSD_sample: A 1-D sampled PSD array
    - offset_sample: A list of offset values obtained on the sampled PSD array (size of lists corresponds to number of peaks analyzed)
    - shift_sample: A list of shift values obtained on the sampled PSD array(size of lists corresponds to number of peaks analyzed)
    - shift_err_sample: A list of the standard deviation on the shift values obtained on the sampled PSD array(size of lists corresponds to number of peaks analyzed)
    - linewidth_sample: A list of linewidth values obtained on the sampled PSD array(size of lists corresponds to number of peaks analyzed)
    - linewidth_err_sample: A list of the standard deviation on the linewidth values obtained on the sampled PSD array(size of lists corresponds to number of peaks analyzed)
    - amplitude_sample: A list of amplitude values obtained on the sampled PSD array  (size of lists corresponds to number of peaks analyzed)  
    - amplitude_err_sample: A list of the standard deviation on the amplitude values obtained on the sampled PSD array(size of lists corresponds to number of peaks analyzed)
    For treating these samples, the class offers an argument to store the steps of the treatment. This is stored in the _history attribute.
    - _history: a list that stores the evolution of the attributes 
    
    To switch the class between the treatment of all the PSD array, sampled PSD arrays or error points, we use the attribute:
    - _treat_selection: a string that directs the treatment towards the whole PSD array, sampled PSD arrays or error points with the following options:
        - all: the whole PSD array is treated
        - sampled: the sampled PSD arrays are treated
        - errors: the error points are treated
    Note that the _history attribute is implemented only if _treat_selection is set to "sampled".
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
        self._algorithm = {
            "name": "Algorithm",
            "version": "v0",
            "author": "No author",
            "description": "No description",
            "functions": []
        } 
        self._history = []

        # Initializing main attributes
        self.frequency = frequency
        self.PSD = PSD

        # Initializing treatment applicator selection attributes
        self._treat_selection = "sampled"

        # Delete unused dimensions
        new_shape = []
        for s in self.frequency.shape:
            if s > 1: new_shape.append(s)
        self.frequency = self.frequency.reshape(new_shape)
        
        new_shape = []
        for s in self.PSD.shape:
            if s > 1: new_shape.append(s)


        # Initializing array sample attributes WARNING: ONLY 1D frequency arrays are supported for now
        if len(self.frequency.shape) == 1:
            self.frequency_sample = self.frequency
            self.PSD_sample = self.PSD
            while len(self.PSD_sample.shape) > 1:
                self.PSD_sample = np.average(self.PSD_sample, axis = 0) 
        else:
            raise ValueError(f"Only 1D frequency arrays are supported for now. The given frequency array has the following dimension: {self.frequency.shape}.")

        # Store the base arrays
        self._history_base = {"frequency_sample": self.frequency_sample,
                            "PSD_sample": self.PSD_sample}

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

    def _create_algorithm(self, algorithm_name: str ="Unnamed Algorithm", version: str ="0.1", author: str = "Unknown", description: str = "", new_algorithm = False):
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

    # Point and window definition

    def add_point(self, position_center_window: float = None, window_width: float = None, type_pnt: str = "Other"):
        """
        Adds a single point to the list of points together with a window to the list of windows with its type. Each point is an intensity extremum obtained by fitting a quadratic polynomial to the windowed data.
        The point is given as a value on the frequency axis (not a position on this axis).
        The "position_center_window" parameter is the center of the window surrounding the peak. The "window_width" parameter is the width of the window surrounding the peak (full width). The "type_pnt" parameter is the type of the peak. It can be either "Stokes", "Anti-Stokes", "Elastic" or "Other".
        
        Parameters
        ----------
        position_center_window : float
            A value on the self.x axis corresponding to the center of a window surrounding a peak
        window_width : float or 2-tuple of float
            A value on the self.x axis corresponding to the width of a window surrounding a peak. If a tuple is given, the first element is the lower bound of the window and the second element is the upper bound given in absolute value from center point.
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

            # select the window of 10 points around the peak
            pos_peak0 = np.argmax(wndw_y)
            loc_wndw = np.arange(max(0, pos_peak0-5), min(len(wndw_y), pos_peak0+5))

            # Fit a quadratic polynomial to the windowed data and returns the local extremum
            params = np.polyfit(wndw_x[loc_wndw], wndw_y[loc_wndw], 2)
            new_x = -params[1]/(2*params[0])

            return new_x

        # Base case: if any of the parameters is None, return
        if position_center_window is None or window_width is None or type_pnt is None:
            return

        # Check that the type of the point is correct
        if type_pnt not in ["Other", "Stokes", "Anti-Stokes", "Elastic"]:
            raise ValueError("The type of the point must be one of the following: 'Stokes', 'Anti-Stokes' or 'Elastic'")

        # Check that the window is in the range of the data
        if not window_width is None:
            if type(window_width) in [float, int]:
                window = [position_center_window-window_width/2, position_center_window+window_width/2]
                if window[1]<self.frequency_sample[0] or window[0]>self.frequency_sample[-1]:
                    raise ValueError(f"The window {window} is out of the range of the data")
            else:
                window = [position_center_window - window_width[0], position_center_window + window_width[1]]
                if window[1]<self.frequency_sample[0] or window[0]>self.frequency_sample[-1]:
                    raise ValueError(f"The window {window} is out of the range of the data")

            # Ensure that the window is within the range of the data
            window[0] = max(self.frequency_sample[0], window[0])
            window[1] = min(self.frequency_sample[-1], window[1])

            # Refine the position of the peaks
            new_x = refine_peak_position(frequency = self.frequency_sample, PSD = self.PSD_sample, window = window)
        else:
            new_x = position_center_window

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
    
    # Pre-treatment functions

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
   
    # Estimation functions

    def estimate_width_inelastic_peaks(self, max_width_guess : float = 2):
        """
        Estimates the full width at half maximum of the inelastic peaks stored in self.points. Note that the data is supposed to have a zero offset. The estimation is done by finding the samples of the data closes to half of the peak height.

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

    # Fitting model definition

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
        if model not in Model.models.keys():
            raise ValueError(f"The model {model} is not recognized.")
        self.fit_model = model

    # Algorithm application functions

    def apply_algorithm_on_all(self):
        """
        Takes all the steps of the algorithm up to the moment this function is called and applies the steps to each individual spectrum in the dataset. 
        This function updates the global attributes of the class concerning the shift, the linewidth and the amplitude together with their variance, taking into account error propagation. 
        If a spectrum could not be fitted, its value is set to 0 in the global attributes.
        All the points where the spectra could not be fitted are marked with the "fit_error_marker" parameter in the global attributes (shift, linewidth, amplitude, shift_var, linewidth_var, amplitude_var) and their coordinates are stored in the "point_error" list. The "point_error_type" attribute is also updated with the type of error returned by the fit function (see scipy.optimize.curve_fit documentation). The function returns the number of spectra that could not be fitted.

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
            dim = list(self.PSD.shape[:-1])+[len(self.shift_sample)]
            self.shift = np.zeros(dim).astype(float)
            self.offset = np.zeros(dim).astype(float)
            self.linewidth = np.zeros(dim).astype(float)
            self.shift_var = np.zeros(dim).astype(float)
            self.linewidth_var = np.zeros(dim).astype(float)
            self.amplitude = np.zeros(dim).astype(float)        
            self.amplitude_var = np.zeros(dim).astype(float)

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

        # Initialize the attributes for the progress callback
        count = 0
        total = np.prod(self.PSD.shape[:-1])

        # Iterate on each spectrum of the PSD array
        while PSD_i is not None:
            # Assign the current PSD and frequency arrays to the corresponding variables
            self.PSD_sample = self.PSD[tuple(PSD_i)]

            # Run the algorithm on the current PSD and frequency arrays
            self._run_algorithm()

            self.offset[tuple(PSD_i)] = self.offset_sample
            self.shift[tuple(PSD_i)] = self.shift_sample
            self.linewidth[tuple(PSD_i)] = self.linewidth_sample
            self.shift_var[tuple(PSD_i)] = self.shift_err_sample
            self.linewidth_var[tuple(PSD_i)] = self.linewidth_err_sample
            self.amplitude[tuple(PSD_i)] = self.amplitude_sample
            self.amplitude_var[tuple(PSD_i)] = self.amplitude_err_sample

            if np.all(np.isnan(self.shift[tuple(PSD_i)])):
                self.point_error.append(PSD_i.copy())
                self.point_error_type.append("fit_error")
                self.point_error_value.append(np.nan)

            PSD_i = plus_one(PSD_i, self.PSD.shape[:-1], len(PSD_i)-1)

            if self._progress_callback is not None:
                count += 1
                self._progress_callback(count, total)
        
        self.BLT = self.linewidth/self.shift
        self.BLT_var = self.BLT**2 * ((self.shift_var/self.shift)**2 + (self.linewidth_var/self.linewidth)**2)

        self._algorithm["functions"].append(temp_algorithm)

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
            """Extracts the functions that are applied before the apply_algorithm_on_all function.

            Returns
            -------
            3 dictionaries
                The algorithm that has been applied to all the data, the algorithm that has been used to combine the data and the algorithm used to mark errors
            """
            algorithm = {"functions": []}
            combine_algotihm = {"functions": []}
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
                        if f["function"] == "combine_results_FSR":
                            combine_algotihm["functions"].append(f)
                        elif f["function"] == "adjust_treatment_on_errors":
                            break
                        else:
                            mark_errors_algorithm["functions"].append(f)
                else:
                    passed_apply_on_all = True
            return algorithm, combine_algotihm, mark_errors_algorithm

        def set_position(algorithm, position):
            for f in algorithm["functions"]:
                if f["function"] == "combine_results_FSR":
                    f["parameters"]["position"] = position
            return algorithm

        # Extract the algorithm that was used to initially treat the data, the one used to mark the errors and the parameters used to store the extracted values
        algorithm, combine_algorithm, mark_errors_algorithm = extract_initial_algorithm()

        # Update the parameters with the new values. If new value is None, keep as is, if False, don't add step, else update with the provided new values
        new_algorithm = {"functions": []}
        if not new_parameters is None:
            for i in range(len(algorithm["functions"])):
                if new_parameters[i] is None:
                    new_algorithm["functions"].append(algorithm["functions"][i])
                elif new_parameters[i] == False:
                    continue
                else:
                    for k, v in new_parameters[i].items():
                        if k in algorithm["functions"][i]["parameters"].keys():
                            algorithm["functions"][i]["parameters"][k] = v
                    new_algorithm["functions"].append(algorithm["functions"][i])
        
        
        # If no position are specified, we apply the algorithm on all the points that had errors
        if position is None:
            position = self.point_error.copy()
        
        # Sets the _treat_selection attribute to "errors". This makes sure that the algorithm doesn't store the results in _history (reduces the memory usage and time complexity)
        self._treat_selection = "errors"

        # Initialize the list of error points
        self.point_error = []
        self.point_error_type = []
        self.point_error_value = []

        # Initialize the callback for the progress bar
        count = 0
        total = len(position)

        # Apply the algorithm on either the provided positions or all the points that had errors
        for PSD_i in position:
            self.PSD_sample = self.PSD[tuple(PSD_i)]
            self._run_algorithm(algorithm = new_algorithm)

            combine_algorithm = set_position(algorithm = combine_algorithm, position = PSD_i)
            self._run_algorithm(algorithm = combine_algorithm)

            if self._progress_callback is not None:
                count += 1
                self._progress_callback(count, total)

        # And we mark the errors again.
        self._run_algorithm(algorithm = mark_errors_algorithm)

    # Fitting functions

    def single_fit_all_inelastic(self, default_width: float = 1, guess_offset: bool = False, update_point_position: bool = True, bound_shift: list = None, bound_linewidth: list = None):
        """
        Fits each inelastically scattered peak individually. The linewidth can be estimated beforehand using the function estimate_width_inelastic_peaks. If not estimated, a fixed width is used (default_width). The offset can also be guessed or not (guess_offset). In the case the offset is guessed, the minimum of the data on the selected window is used as an initial guess. 
        When applying the fit to data acquired successively, it might be interesting to update the initial position of the peak by selecting the last fitted position. This can be done by setting update_point_position to True.

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
            self.shift_err_sample = []
            self.linewidth_sample = []
            self.linewidth_err_sample = []
            self.amplitude_sample = []
            self.amplitude_err_sample = []
            self.offset_sample = []
            self.slope_sample = []
        
        def extract_point_window_gammaGuess():
            """Extracts all the inelastic peaks from the list of points and their corresponding windows. Also extracts the guess for the width of the peaks or if it is not defined, uses the default width.

            Returns
            -------
            3-tuple of lists
                peaks: the list of peaks
                windows: the list of windows around the peaks
                guess_gamma: the list of guess for the width of the peaks
            """
            peaks, windows, guess_gamma = [], [], []
            for i in range(len(self.points)):
                # If the selected peak is an inelastic peak, extract the peak position and the window around it
                if self.points[i][0].split("_")[0] in ["Anti-Stokes", "Stokes"]:
                    peaks.append(self.points[i][1])
                    windows.append(self.windows[i])

                    # If the width has been estimated, use it, otherwise use the default width
                    if len(self.width_estimator) > 0:
                        guess_gamma.append(self.width_estimator[i])
                    else:
                        guess_gamma.append(default_width)
            return peaks, windows, guess_gamma

        def update_results(popt = None, pcov = None, all_nan=False):
            """
            Stores the results of the fit in the corresponding sample lists. If all_nan is True, the fitted parameters are set to NaN. 

            Parameters
            ----------
            popt : list, optional
                The fitted parameters, by default None
            pcov : list, optional
                The covariance matrix of the fit, by default None
            all_nan : bool, optional
                Wether to set all the fitted parameters to NaN, by default False
            """
            # If the all_nan is set to True, set all the fitted parameters to NaN
            if all_nan:
                popt = [np.nan for i in range(5)]
                pcov = [[np.nan for i in range(5)] for i in range(5)]
            
            # Save the fitted parameters in the corresponding sample lists
            self.offset_sample.append(popt[0])
            self.amplitude_sample.append(popt[1])
            self.shift_sample.append(popt[2])
            self.linewidth_sample.append(np.abs(popt[3]))
            if "elastic" in self.fit_model:
                self.slope_sample.append(popt[4])

            # Save the standard deviation of the fitted parameters in the corresponding sample lists
            self.amplitude_err_sample.append(np.sqrt(pcov[1][1]))
            self.shift_err_sample.append(np.sqrt(pcov[2][2]))
            self.linewidth_err_sample.append(np.sqrt(pcov[3][3]))

        # Initializes the list of fitted parameters 
        reinitialize_fitted_list()

        # Raise an error if the model has not been defined
        if self.fit_model is None:
            raise ValueError("The model has not been defined. Please use the function 'define_model' to define the model before calling 'fit_all_inelastic_of_curve'.")
    
        # Extract the points to fit, select only the ones of type Stokes or Anti-Stokes. Also extract the guess for the width of the peaks or if it is not defined, use the default width
        peaks, windows, guess_gamma = extract_point_window_gammaGuess()
        
        # Fit each peak that has been selected
        for peak, window, gamma, bs, bl in zip(peaks, windows, guess_gamma, bound_shift, bound_linewidth):
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
                # Define the bounds for the fit (ensure the linewidth is positive)
                bounds = [[-np.inf, -np.inf, -np.inf, 0, -np.inf], [np.inf, np.inf, np.inf, np.inf, np.inf]]

                # If bounds are provided for the shift or the linewidth , update them accordingly
                if bound_shift is not None:
                    bounds[0][2] = bs[0]
                    bounds[1][2] = bs[1]
                    peak = min(max(peak, bounds[0][2]), bounds[1][2])  # Ensure the peak is within the bounds
                if bound_linewidth is not None:
                    bounds[0][3] = bl[0]
                    bounds[1][3] = bl[1]
                    gamma = min(max(gamma, bounds[0][3]), bounds[1][3])  # Ensure the gamma is within the bounds

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
                    popt, pcov = optimize.curve_fit(f = models.models[self.fit_model], 
                                                    xdata = self.frequency_sample[pos_window], 
                                                    ydata = self.PSD_sample[pos_window], 
                                                    p0 = [offset_guess, amplitude_guess, peak, gamma, slope_guess],
                                                    bounds = bounds)
                except Exception as e:
                    print(e)
                    error_fit = True
            else:
                # Define the bounds for the fit (ensure the linewidth and amplitude are positive)
                bounds = [[-np.inf, 0, -np.inf, 0], [np.inf, np.inf, np.inf, np.inf]]

                # If bounds are provided for the shift or the linewidth , update them accordingly
                if bound_shift is not None:
                    bounds[0][2] = bs[0]
                    bounds[1][2] = bs[1]
                    peak = min(max(peak, bounds[0][2]), bounds[1][2])  # Ensure the peak is within the bounds
                if bound_linewidth is not None:
                    bounds[0][3] = bl[0]
                    bounds[1][3] = bl[1]
                    gamma = min(max(gamma, bounds[0][3]), bounds[1][3])  # Ensure the gamma is within the bounds

                error_fit = False
                try:
                    popt, pcov = optimize.curve_fit(f = models.models[self.fit_model], 
                                                    xdata = self.frequency_sample[pos_window], 
                                                    ydata = self.PSD_sample[pos_window], 
                                                    p0 = [offset_guess, amplitude_guess, peak, gamma],
                                                    bounds = bounds)
                except Exception as e:
                    print(e)
                    error_fit = True

            # If the fit succeeded, update the parameters, if not store np.nan
            if not error_fit:
                update_results(popt, pcov)
            else:
                update_results(all_nan = True)

            # If the user want to update the peak position with the fitted shift, update the point positions
            if update_point_position:
                for i, elt in enumerate(self.points):                
                    if elt[1] == peak:
                        index = i
                        pos_peak = self.shift_sample[-1]
                        self.points[index][1] = pos_peak
                        break

    def multi_fit_all_inelastic(self, default_width: float = 1, guess_offset: bool = False, update_point_position: bool = True, bound_shift: list = None, bound_linewidth: list = None):
        """
        Fits all inelastically scattered peak as a single curve. The linewidth of the individual peaks can be estimated beforehand using the function estimate_width_inelastic_peaks. If not estimated, a fixed width is used (default_width). The offset can also be guessed or not (guess_offset). In the case the offset is guessed, the minimum of the data on the window defined as the combination of all the peaks windoes is used as an initial guess. 
        When applying the fit to data acquired successively, it might be interesting to update the initial position of the peak by selecting the last fitted position. This can be done by setting update_point_position to True.

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
            self.shift_err_sample = []
            self.linewidth_sample = []
            self.linewidth_err_sample = []
            self.amplitude_sample = []
            self.amplitude_err_sample = []
            self.offset_sample = []
            self.slope_sample = []
        
        def extract_point_window_gammaGuess():
            """Extracts all the inelastic peaks from the list of points and their corresponding windows. Also extracts the guess for the width of the peaks or if it is not defined, uses the default width.

            Returns
            -------
            3-tuple of lists
                peaks: the list of peaks
                windows: the list of windows around the peaks
                guess_gamma: the list of guess for the width of the peaks
            """
            peaks, windows, guess_gamma = [], [], []
            for i in range(len(self.points)):
                # If the selected peak is an inelastic peak, extract the peak position and the window around it
                if self.points[i][0].split("_")[0] in ["Anti-Stokes", "Stokes"]:
                    peaks.append(self.points[i][1])
                    windows.append(self.windows[i])

                    # If the width has been estimated, use it, otherwise use the default width
                    if len(self.width_estimator) > 0:
                        guess_gamma.append(self.width_estimator[i])
                    else:
                        guess_gamma.append(default_width)
            return peaks, windows, guess_gamma

        def update_results(popt = None, pcov = None, all_nan=False):
            """
            Stores the results of the fit in the corresponding sample lists. If all_nan is True, the fitted parameters are set to NaN. 

            Parameters
            ----------
            popt : list, optional
                The fitted parameters, by default None
            pcov : list, optional
                The covariance matrix of the fit, by default None
            all_nan : bool, optional
                Wether to set all the fitted parameters to NaN, by default False
            """
            # If the all_nan is set to True, set all the fitted parameters to NaN
            if all_nan:
                popt = np.array([np.nan for i in range(len(popt))])
                pcov = np.array([[np.nan for i in range(len(popt))] for i in range(len(popt))])
            
            popt = popt.reshape((-1,4))
            std = np.sqrt(np.diag(pcov)).reshape((-1,4))

            # Save the fitted parameters in the corresponding sample lists
            self.offset_sample = popt[:, 0].tolist()
            self.amplitude_sample = popt[:, 1].tolist()
            self.shift_sample = popt[:, 2].tolist()
            self.linewidth_sample = np.abs(popt[:, 3]).tolist()

            # Save the standard deviation of the fitted parameters in the corresponding sample lists
            self.amplitude_err_sample = std[:, 1].tolist()
            self.shift_err_sample = std[:, 2].tolist()
            self.linewidth_err_sample = std[:, 3].tolist()

        # Initializes the list of fitted parameters 
        reinitialize_fitted_list()

        # Raise an error if the model has not been defined
        if self.fit_model is None:
            raise ValueError("The model has not been defined. Please use the function 'define_model' to define the model before calling 'fit_all_inelastic_of_curve'.")
    
        # Extract the points to fit, select only the ones of type Stokes or Anti-Stokes. Also extract the guess for the width of the peaks or if it is not defined, use the default width
        peaks, windows, guess_gamma = extract_point_window_gammaGuess()

        # Initializes the initial conditions and boundary conditions for the fit
        p0 = []
        bounds = [[], []]

        # Initializes the window for the fit
        wndw_fit = np.array([])
        
        # Fit each peak that has been selected
        for peak, window, gamma, bs, bl in zip(peaks, windows, guess_gamma, bound_shift, bound_linewidth):
            # Extract the peak position and the window around the peak
            pos_peak = np.argmin(np.abs(self.frequency_sample - peak))
            pos_window = np.where((self.frequency_sample >= window[0]) & (self.frequency_sample <= window[1]))
            wndw_fit = np.append(wndw_fit, pos_window)

            # Guess the amplitude of the peak by selecting its intensity
            amplitude_guess = self.PSD_sample[pos_peak]

            # Set the offset guess to the minimum of the intensity array on the selected window or to 0
            if guess_offset:
                offset_guess = np.min(self.PSD_sample[pos_window])
            else: 
                offset_guess = 0

            # Check if we want to correct for the presence of an elastic peak and apply the fitting
            models = Models()

            # Check if the model is elastic and if so, raise an error if the fit_model is not compatible with the elastic correction
            if "elastic" in self.fit_model:
                raise ValueError("The multi-fit for inelastic peaks does not support the elastic correction. Please use the single fit for inelastic peaks instead.")
            
            # Define the bounds for the fit (ensure the linewidth and amplitude are positive)
            temp_bounds = [[-np.inf, 0, -np.inf, 0], [np.inf, np.inf, np.inf, np.inf]]

            # If bounds are provided for the shift or the linewidth , update them accordingly
            if bound_shift is not None:
                temp_bounds[0][2] = bs[0]
                temp_bounds[1][2] = bs[1]
                peak = min(max(peak, bs[0]), bs[1])  # Ensure the peak is within the bounds
            if bound_linewidth is not None:
                temp_bounds[0][3] = bl[0]
                temp_bounds[1][3] = bl[1]
                gamma = min(max(gamma, bl[0]), bl[1])  # Ensure the gamma is within the bounds

            # Append the initial conditions to the list of initial conditions
            if len(p0) == 0:
                # If this is the first peak, we initialize the initial conditions
                p0 += [offset_guess, amplitude_guess, peak, gamma]
            else:
                # Ensure that only one constant parameter is used for all the curve
                temp_bounds[0][0] = -1e-10
                temp_bounds[1][0] = 1e-10
                p0 += [0, amplitude_guess, peak, gamma]

            # Append the bounds to the list of bounds
            bounds[0] += temp_bounds[0]
            bounds[1] += temp_bounds[1]
        
        def func(x, *p0):
            """
            The function to fit the data. It sums the contributions of all the peaks defined in p0.

            Parameters
            ----------
            x : array-like
                The frequency array to fit
            p0 : list 
                The list of initial conditions for each peak

            Returns
            -------
            array-like
                The sum of the contributions of all the peaks at the given frequencies
            """
            p0 = np.array(p0).reshape((-1, 4))
            # Sum the contributions of all the peaks defined in p0
            return sum(models.models[self.fit_model](x, *params) for params in p0)

        wndw_fit = np.unique(wndw_fit.astype(int))

        error_fit = False
        try:
            popt, pcov = optimize.curve_fit(f = func, 
                                            xdata = self.frequency_sample[wndw_fit], 
                                            ydata = self.PSD_sample[wndw_fit], 
                                            p0 = p0,
                                            bounds = bounds)
        except Exception as e:
            print(e)
            error_fit = True

        # If the fit succeeded, update the parameters, if not store np.nan
        if not error_fit:
            update_results(popt, pcov)
        else:
            p0 = np.array(p0).flatten()
            update_results(p0, np.zeros((len(p0), len(p0))), all_nan = True)

        # If the user want to update the peak position with the fitted shift, update the point positions
        if update_point_position:
            for i, elt in enumerate(self.points):                
                if elt[1] == peak:
                    index = i
                    pos_peak = self.shift_sample[-1]
                    self.points[index][1] = pos_peak
                    break

    def fit_all_inelastic_of_curve(self, default_width: float = 1, guess_offset: bool = False, update_point_position: bool = True, bound_shift: list = None, bound_linewidth: list = None):
        """
        Fits a lineshape to each of the inelastic peaks using the points stored as Stokes or Anti-Stokes peaks in the points attribute. The linewidth can be estimated beforehand using the function estimate_width_inelastic_peaks. If not estimated, a fixed width is used (default_width). The offset can also be guessed or not (guess_offset). In the case the offset is guessed, the minimum of the data on the selected window is used as an initial guess. The position of the peak can also be updated based on the fitted shift if update_point_position is set to True. If set to False, the positions are not updated.

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
            self.shift_err_sample = []
            self.linewidth_sample = []
            self.linewidth_err_sample = []
            self.amplitude_sample = []
            self.amplitude_err_sample = []
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

            self.amplitude_err_sample.append(np.sqrt(pcov[1][1]))
            self.shift_err_sample.append(np.sqrt(pcov[2][2]))
            self.linewidth_err_sample.append(np.sqrt(pcov[3][3]))

        # Initializes the list of fitted parameters 
        reinitialize_fitted_list()

        # Raise an error if the model has not been defined
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

    # Post-treatment functions

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

    def combine_results_FSR(self, FSR: float = 15, keep_max_amplitude: bool = False, amplitude_weight: bool = False, shift_err_weight: bool = False, position: list = None):
        """
        Combines the results of the algorithm to have a value for frequency shift based on a known Free Spectral Range (FSR) value. The end shift value is obtained by "moving" the peak by a FSR value until the peak is within the [-FSR/2, FSR/2] range. Then the absolute value of the shift is taken as the end shift value.
        The combination of the result is done by taking the average of all the values by default. Alternatively, the user can choose to keep the maximum of the amplitude of the peak by setting the "keep_max_amplitude" parameter to True. The user can also choose to weight the shift and linewidth by the amplitude of the peak by setting the "amplitude_weight" parameter to True. Note that in the latter case, the precise knowledge of the frequency axis is a must as averaging slightly uncentered peaks will lead to a wrong result.

        Parameters
        ----------
        FSR : float, optional
            The Free Spectral Range of the spectrometer, by default 15Ghz
        keep_max_amplitude : bool, optional
            If True, the maximum of the peak amplitude is stored in the amplitude array. If False, an average of all the amplitudes is stored. Default is False.
        amplitude_weight : bool, optional    
            If True, the amplitude of the spectra is used to weight the shift and linewidth. If set to false, a simple average is performed. Default is False.
        shift_err_weight : bool, optional
            If True, the inverse of the standard deviation of the shift is used to weight the shift and linewidth. If set to false, a simple average is performed. Default is False.
        position: list, optional
            The position of the spectrum to be updated in case we combine the sampled results. This is used to update the values of a spectrum that has been re-fitted.  
        """
        def nature_peaks():
            """
            Returns the nature (Stokes or Anti-Stokes) of peaks that are not elastic or not windows
            """
            tpe = []
            for i in range(len(self.points)):
                # If the selected peak is an inelastic peak, extract the peak position and the window around it
                if self.points[i][0].split("_")[0] in ["Anti-Stokes", "Stokes"]:
                    tpe.append(self.points[i][0].split("_")[0])
            return tpe

        # Check if the user has set both combining methods to True, if so raise an error
        if keep_max_amplitude and amplitude_weight:
            raise ValueError("The parameters 'keep_max_amplitude' and 'amplitude_weight' cannot be both set to True.")
        
        if position is None:
            # Average the values of shift on all the PSDs 
            shift = np.nanmean(self.shift, axis = 0)
            while shift.ndim > 1:
                shift = np.mean(shift, axis = 0)
        else:
            shift = self.shift_sample
        
        # Get the nature of the peaks (Stokes or Anti-Stokes)
        nature = nature_peaks()

        # Compute the correction factor to ensure the shift is contained in [-FSR/2, FSR/2]
        k = []
        for s in shift:
            temp = -(s+FSR/2)/FSR
            k.append(np.ceil(temp))

        if position is None:
            # Realign the shift values
            self.shift = np.moveaxis(self.shift, [0, -1], [-1, 0])
            for i in range(len(k)):
                self.shift[i] += k[i] * FSR
                if nature[i] == "Anti-Stokes":
                    self.shift[i] = -self.shift[i]
            self.shift = np.moveaxis(self.shift, [-1, 0], [0, -1])
        else:
            for i in range(len(k)):
                self.shift_sample[i] += k[i] * FSR
                if nature[i] == "Anti-Stokes":
                    self.shift_sample[i] = -self.shift_sample[i]
            offset_sample = np.array(self.offset_sample)
            shift_sample = np.array(self.shift_sample)
            linewidth_sample = np.array(self.linewidth_sample)
            amplitude_sample = np.array(self.amplitude_sample)
            shift_err_sample = np.array(self.shift_err_sample)
            linewidth_err_sample = np.array(self.linewidth_err_sample)
            amplitude_err_sample = np.array(self.amplitude_err_sample)


        # If keep_max_amplitude is set to True, we select only the shift corresponding to the maximum amplitude
        if keep_max_amplitude:
            if position is None:
                # For each set of amplitudes along the last axis, find the index of the maximum amplitude
                max_indices = np.argmax(self.amplitude, axis=-1)
                # Use advanced indexing to select the corresponding shift values
                self.offset = np.take_along_axis(self.offset, np.expand_dims(max_indices, axis=-1), axis=-1).squeeze(-1)
                self.shift = np.take_along_axis(self.shift, np.expand_dims(max_indices, axis=-1), axis=-1).squeeze(-1)
                self.amplitude = np.take_along_axis(self.amplitude, np.expand_dims(max_indices, axis=-1), axis=-1).squeeze(-1)
                self.linewidth = np.take_along_axis(self.linewidth, np.expand_dims(max_indices, axis=-1), axis=-1).squeeze(-1)
                self.shift_var = np.take_along_axis(self.shift_var, np.expand_dims(max_indices, axis=-1), axis=-1).squeeze(-1)
                self.linewidth_var = np.take_along_axis(self.linewidth_var, np.expand_dims(max_indices, axis=-1), axis=-1).squeeze(-1)
                self.amplitude_var = np.take_along_axis(self.amplitude_var, np.expand_dims(max_indices, axis=-1), axis=-1).squeeze(-1)
            else:
                pos = np.argmax(amplitude_sample)
                self.offset[tuple(position)] = offset_sample[pos]
                self.shift[tuple(position)] = shift_sample[pos]
                self.linewidth[tuple(position)] = linewidth_sample[pos]
                self.shift_var[tuple(position)] = shift_err_sample[pos]
                self.linewidth_var[tuple(position)] = linewidth_err_sample[pos]
                self.amplitude[tuple(position)] = amplitude_sample[pos]
                self.amplitude_var[tuple(position)] = amplitude_err_sample[pos]
        
        elif amplitude_weight:
            if position is None:
                # For each set of amplitudes along the last axis, calculate the weighted average of the shift and linewidth
                self.offset = np.average(self.offset, axis=-1, weights=self.amplitude)
                self.shift = np.average(self.shift, axis=-1, weights=self.amplitude)
                self.linewidth = np.average(self.linewidth, axis=-1, weights=self.amplitude)
                self.amplitude = np.average(self.amplitude, axis=-1, weights=self.amplitude)
                self.shift_var = np.sum(self.shift_var**2 * self.amplitude**2, axis = -1) / np.sum(self.amplitude**2, axis=-1)
                self.linewidth_var = np.sum(self.linewidth_var**2 * self.amplitude**2, axis = -1) / np.sum(self.amplitude**2, axis=-1)
                self.amplitude_var = np.sum(self.amplitude_var**4, axis = -1) / np.sum(self.amplitude**2, axis=-1)
            else:
                self.offset[tuple(position)] = np.average(offset_sample)
                self.shift[tuple(position)] = np.average(shift_sample)
                self.linewidth[tuple(position)] = np.average(linewidth_sample)
                self.shift_var[tuple(position)] = np.sum(shift_err_sample**2 * amplitude_sample**2) / np.sum(amplitude_sample**2, axis=-1)
                self.linewidth_var[tuple(position)] = np.sum(linewidth_err_sample**2 * amplitude_sample**2) / np.sum(amplitude_sample**2, axis=-1)
                self.amplitude[tuple(position)] = np.average(amplitude_sample)
                self.amplitude_var[tuple(position)] = np.sum(amplitude_err_sample**4) / np.sum(amplitude_sample**2, axis=-1)

        elif shift_err_weight:
            if position is None:
                # For each set of amplitudes along the last axis, calculate the weighted average of the shift and linewidth
                self.offset = np.average(self.offset, axis=-1, weights=1/self.shift_var)
                self.shift = np.average(self.shift, axis=-1, weights=1/self.shift_var)
                self.linewidth = np.average(self.linewidth, axis=-1, weights=1/self.shift_var)
                self.amplitude = np.average(self.amplitude, axis=-1, weights=1/self.shift_var)
                self.linewidth_var = np.sum(self.linewidth_var**2 / self.shift_var**2, axis = -1) / np.sum(1/self.shift_var**2, axis=-1)
                self.amplitude_var = np.sum(self.amplitude_var**2 / self.shift_var**2, axis = -1) / np.sum(1/self.shift_var**2, axis=-1)
                self.shift_var = self.shift_var.shape[-1] / np.sum(1/self.shift_var**2, axis=-1)
            else:
                self.offset[tuple(position)] = np.average(offset_sample, weights=1/shift_err_sample)
                self.shift[tuple(position)] = np.average(shift_sample, weights=1/shift_err_sample)
                self.linewidth[tuple(position)] = np.average(linewidth_sample, weights=1/shift_err_sample)
                self.amplitude[tuple(position)] = np.average(amplitude_sample, weights=1/shift_err_sample)
                self.shift_var[tuple(position)] = len(shift_err_sample) / np.sum(1/shift_err_sample**2)
                self.linewidth_var[tuple(position)] = np.sum(linewidth_err_sample**2 / shift_err_sample**2) / np.sum(1 / shift_err_sample**2)
                self.amplitude_var[tuple(position)] = np.sum(amplitude_err_sample**2 / shift_err_sample**2) / np.sum(1 / shift_err_sample**2)
        
        else:
            if position is None:
                self.offset = np.nanmean(self.offset, axis=-1)
                self.shift = np.nanmean(self.shift, axis=-1)
                self.linewidth = np.nanmean(self.linewidth, axis=-1)
                self.amplitude = np.nanmean(self.amplitude, axis=-1)
                self.linewidth_var = np.nanmean(self.linewidth_var**2, axis = -1)
                self.amplitude_var = np.nanmean(self.amplitude_var**2, axis = -1)
                self.shift_var = np.nanmean(self.shift_var**2, axis = -1)
            else:
                self.offset[tuple(position)] = np.nanmean(offset_sample)
                self.shift[tuple(position)] = np.nanmean(shift_sample)
                self.linewidth[tuple(position)] = np.nanmean(linewidth_sample)
                self.amplitude[tuple(position)] = np.nanmean(amplitude_sample)
                self.linewidth_var[tuple(position)] = np.nanmean(linewidth_err_sample**2)
                self.amplitude_var[tuple(position)] = np.nanmean(amplitude_err_sample**2)
                self.shift_var[tuple(position)] = np.nanmean(shift_err_sample**2)
        
        if position is None:
            self.BLT = self.linewidth / self.shift 
            self.BLT_var = self.BLT**2 * ((self.linewidth_var / self.linewidth)**2 + (self.shift_var / self.shift)**2)
        else:
            self.BLT[tuple(position)] = self.linewidth[tuple(position)] / self.shift[tuple(position)]
            self.BLT_var[tuple(position)] = self.BLT[tuple(position)]**2 * ((self.linewidth_var[tuple(position)] / self.linewidth[tuple(position)])**2 + (self.shift_var[tuple(position)] / self.shift[tuple(position)])**2)

    # Outliers 

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
        max_error_shift_err : float, optional
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
        max_error_shift_err : float, optional
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

