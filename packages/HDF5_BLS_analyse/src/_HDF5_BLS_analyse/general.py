import json
import numpy as np

from .analyse_backend import Analyse_backend

class Analyse_general(Analyse_backend):
    """This class is a class inherited from the Analyse_backend class used to store steps of analysis that are not specific to a particular type of spectrometer and that are not interesting to show in an algorithm. For example, the function to add a remarkable point to the data
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

    def silent_clear_points(self):
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

    def silent_return_string_algorithm(self):
        """Returns a string representation of the algorithm stored in the _algorithm attribute of the class.

        Returns
        -------
        str
            The string representation of the algorithm.
        """
        return json.dumps(self._algorithm, indent=4)


    