from .general import Analyse_general

import numpy as np
from scipy.optimize import curve_fit, minimize


class Analyse_VIPA(Analyse_general):
    """This class is a child class of Analyse_general. It inherits all the methods of the parent class and adds the functions specific to VIPA spectrometers.
    """
    def __init__(self, x, y):
        super().__init__(x = x, y = y)

        self._algorithm = {
            "name": "VIPA spectrum analyser",
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
        self.silent_clear_points()
        
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
        
        # Sort the lists
        E.sort()
        S.sort()
        AS.sort()

        # Set the boundaries for a
        a_min = -np.inf
        a_max = np.inf
        if FSR is not None:
            if len(E)>2 or len(S)>2 or len(AS)>2:
                if len(E) >= len(S) and len(E)>= len(AS):
                    p0 = E[0]
                    p1 = E[-1]
                    k = len(E)-1
                    if E[1]-E[0] > E[2]-E[1]:
                        a_max = k*FSR/(p1**2-p0**2)
                    else:
                        a_min = k*FSR/((p1-p0)(p0+p1-2*len(self.x)))
                elif len(S)>= len(AS):
                    p0 = S[0]
                    p1 = S[-1]
                    k = len(S)-1
                    if S[1]-S[0] > S[2]-S[1]:
                        a_max = k*FSR/(p1**2-p0**2)
                    else:
                        a_min = k*FSR/((p1-p0)(p0+p1-2*len(self.x)))
                else:
                    p0 = AS[0]
                    p1 = AS[-1]
                    k = len(AS)-1
                    if AS[1]-AS[0] > AS[2]-AS[1]:
                        a_max = k*FSR/(p1**2-p0**2)
                    else:
                        a_min = k*FSR/((p1-p0)(p0+p1-2*len(self.x)))

        AS_order, S_order = get_order(AS, S, E)
        
        A, B, C = create_matrices(AS, S, E, AS_order, S_order)

        # Converting the lists to numpy arrays
        A = np.array(A)
        B = np.array(B)
        C = np.array(C)

        # Defining the minimization function
        if FSR is None:
            result = minimize(error, [0, 1, 0])
        else: 
            result = minimize(error, [0, max(max(AS_order), max(S_order))*FSR/self.x.size, 0], bounds=[(a_min, a_max), (-np.inf, np.inf), (-np.inf, np.inf)])
        
        a, b, c = result.x

        print(a, a_min, a_max)

        # Create the new x axis corresponding to the frequency axis fitted
        self.x = a*self.x**2 + b*self.x + c

        # Clear the points and windows
        self.silent_clear_points()

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
        
        if len(E) != 2:
            raise ValueError("There must be exactly two elastic peaks to use this function.")
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
        self.silent_clear_points()

        # Return the x axis if the user wants to use it
        return self.x

    def interpolate_on_one_order(self, shift: float = 1):
        """
        Uses positions of one elastic peak and associated Brillouin doublet to obtain a frequency axis by interpolating the position of the peak with a quadratic polynomial. The user has to enter a value for the Brillouin shift to calibrate the frequency axis. By default, this value is set to 1 so that the measured frequencies are normalized to the calibration sample.

        Parameters
        ----------  
        shift : float
            The frequency shift between the elastic and inelastic peaks (in GHz). By default 1.
        """
        # Start by extracting the peaks by their nature
        E, AS, S = [], [], []
        for point in self.points:
            name, value = point
            if name[0] == "E":
                E.append(value)
            elif name[0] == "A":
                AS.append(value)
            elif name[0] == "S":
                S.append(value)
        
        if len(E) != 1:
            raise ValueError("There must be exactly two elastic peaks to use this function.")
        if len(AS) != 1:
            raise ValueError("There must be exactly one anti-Stokes peak to use this function.")
        if len(S) != 1:
            raise ValueError("There must be exactly one Stokes peak to use this function.")

        # Get the positions of the inelastic peaks (x0 and x2) and of the elastic peak (x1)
        x0 = min(AS[0], S[0])
        x1 = E[0]
        x2 = max(AS[0], S[0])

        # Get the value of a, b and c based on theory 
        a = shift * (x2+x0-2*x1) / ((x2 - x1)*(x0*x2 - x1*x2 + x0*x1 - x0**2))
        b = (shift - a*(x2**2-x1**2))/(x2-x1)
        c = - (a*x1**2 + b*x1)

        # Now we can create the new x axis
        self.x = a*self.x**2 + b*self.x + c

        # Clear the points and windows
        self.silent_clear_points()

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
        self.silent_clear_points()

        # Return the x axis if the user wants to use it
        return self.x


# Example Usage
if __name__ == "__main__":
    import h5py
    import matplotlib.pyplot as plt

    with h5py.File("/Users/pierrebouvet/Documents/Databases/2504 - Measures fixed cells/Test.h5", "r") as f:
        data = np.array(f["Brillouin/HCU29/HCU29 - 1/Acq 1/Raw data"][()])
    
    average = data
    while len(average.shape) > 1:
        average = np.average(average, axis = 0)

    analyser = Analyse_VIPA(x = np.arange(average.size), y = average)
   
    # analyser.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
    #                            version="v0", 
    #                            author="Pierre Bouvet", 
    #                            description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")
    # analyser.add_point(position_center_window=12, type_pnt="Elastic", window_width=5)
    # analyser.add_point(position_center_window=37, type_pnt="Anti-Stokes", window_width=5)
    # analyser.add_point(position_center_window=236, type_pnt="Stokes", window_width=5)
    # analyser.add_point(position_center_window=259, type_pnt="Elastic", window_width=5)
    # analyser.add_point(position_center_window=282, type_pnt="Anti-Stokes", window_width=5)
    # analyser.add_point(position_center_window=466, type_pnt="Stokes", window_width=5)
    # analyser.add_point(position_center_window=488, type_pnt="Elastic", window_width=5)
    # analyser.add_point(position_center_window=509, type_pnt="Anti-Stokes", window_width=5)
    # analyser.interpolate_elastic_inelastic(FSR = 60)
    # analyser.add_point(position_center_window=57, type_pnt="Stokes", window_width=1)
    # analyser.add_point(position_center_window=68.5, type_pnt="Anti-Stokes", window_width=1)
    # analyser.center_x_axis(center_type = "Inelastic")

    # analyser.silent_save_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/Test.json", save_parameters=True)
    
    analyser.silent_open_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/MUW_PB_VIPA_FSR_Shift_v0.json")
    analyser.silent_run_algorithm()
    
    plt.plot(analyser.x, analyser.y)
    plt.show()

    # analyser._print_algorithm()
