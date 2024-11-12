import numpy as np
from scipy import optimize


class Treat():
    def __init__(self):
        self.treat_steps = []
    
    def remove_offset(self, data, nb_points = 10):
        """Automatically identifies the offset of the signal and removes it by identifying the regions of points that are closer to zero and removing their average.
    
        Parameters
        ----------
        data : numpy array                           
            The data that is going to be treated

        Returns
        -------
        data_treat : numpy array
            The data where the offset has been removed
        """
        pos_min = np.argmin(data)
        window = [max(0, pos_min-nb_points), min(data.size, pos_min+nb_points)]
        offset = np.average(data[window[0]:window[1]])
        data_treat = data - offset
        return data_treat

    def normalize_data(self, data, window = 10, peak_pos = -1, remove_offset = True):
        """Normalizes a data array to an amplitude of 1 after removing the offset
    
        Parameters
        ----------
        data : numpy array                           
            The data that we want to normalize
        window : int, optional 
            The window width around the position of the peak to refine its position and use its amplitude to normalize the signal. Default is 10
        peak_pos : int, optional 
            The position of the peak in the data array. Defaults to the maximal value of the spectrum
        remove_offset : bool, optional 
            Wether to remove the offset of the data or not before normalizing. Defaults to True.

        Returns
        -------
        data_treat : numpy array
            The data where the offset has been removed
        """
        if remove_offset: data_treat = self.remove_offset(data)
        if peak_pos == -1: peak_pos = np.argmax(data)
        window = [max(0, peak_pos-window), min(data.size, peak_pos+window)]
        val = np.max(data[window[0]:window[1]])
        return data_treat/val
    
    def fit_model(self, frequency, data, center_frequency, linewidth, normalize = True, model = "Lorentz", fit_S_and_AS = True, window_peak_find = 1, window_peak_fit = 3, correct_elastic = False):
        r"""Fitting function that performs a fit on the selected spectrum and returns the fitted values and the standard deviations on the fitted parameters. When 2 peaks are fitted, the standard deviation returned by the function corresponds to the standard deviation of two independent events, that is 
        .. math:: std_{avg} = \\sqrt{std_S^2 + std_{AS}^2}

        Parameters
        ----------
        frequency : numpy array
            The freaquency axis corresponding to the data
        data : numpy array
            The data to fit
        center_frequency : float
            The estimate expected shift frequency
        linewidth : float
            The expected linewidth
        normalize : bool, optional
            Wether a normalization is to be made on the data before treatment or not , by default True
        model : str, optional
            The model with which to fit the data. Accepted models are "Lorentz" and "DHO", by default "Lorentz"
        fit_S_and_AS : bool, optional
            Wether to fit both the Stokes and Anti-Stokes peak during the fit (and return corresponding averaged values and propagated errors), by default True
        window_peak_find : float, optional
            The width in GHz where to find the peak, by default 1GHz
        window_peak_fit : float, optional
            The width in GHz of the windo used to fit the peak, by default 3 GHz
        correct_elastic : bool, optional
            Wether to correct for the presence of an elastic peak by setting adding a linear function to the model, by default False

        Returns
        -------
        optimal_parameters: tuple
            The returned optimal parameters for the fit (offset, amplitude, center_frequency, linewidth) averaged if both the Stokes and anti-Stokes peaks are used
        variance: tuple
            The returned variance on the fitted parameters (offset, amplitude, center_frequency, linewidth)
        """
        def lorentzian(nu, b, a, nu0, gamma):
            return b + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
        
        def lorentzian_elastic(nu, ae, be, a, nu0, gamma):
            return be + ae*nu + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
        
        def DHO(nu, b, a, nu0, gamma):
            return b + a*(gamma*nu0**2)/((nu**2-nu0**2)**2+gamma*nu0**2)
        
        def DHO_elastic(nu, ae, be, a, nu0, gamma):
            return be + ae*nu + a*(gamma*nu0**2)/((nu**2-nu0**2)**2+gamma*nu0**2)
        
        # Refine the position of the peak with a quadratic polynomial fit
        if fit_S_and_AS:
            center_frequency = abs(center_frequency)
            window_peak_find_S = np.where(np.abs(frequency+center_frequency)<window_peak_find/2)
            pol_temp_S = np.polyfit(frequency[window_peak_find_S], data[window_peak_find_S],2)
            center_frequency_S = -pol_temp_S[1]/(2*pol_temp_S[0])
            window_peak_find_AS = np.where(np.abs(frequency-center_frequency)<window_peak_find/2)
            pol_temp_AS = np.polyfit(frequency[window_peak_find_AS], data[window_peak_find_AS],2)
            center_frequency_AS = -pol_temp_AS[1]/(2*pol_temp_AS[0])

            center_frequency = center_frequency_S
        else:
            window_peak_find = np.where(np.abs(frequency-center_frequency)<window_peak_find/2)
            pol_temp = np.polyfit(frequency[window_peak_find], data[window_peak_find],2)
            center_frequency = -pol_temp[1]/(2*pol_temp[0])

        # Normalize the data is not already done
        if normalize: data = self.normalize_data(data, peak_pos=np.argmin(np.abs(frequency-center_frequency)))

        # Apply the fit
        if fit_S_and_AS:
            # Define the initial parameters of the fit
            if correct_elastic: 
                p0_S = [0, 0, 1, center_frequency_S, linewidth]
                p0_AS = [0, 0, 1, center_frequency_AS, linewidth]
                model = model+"_e"
            else: 
                p0_S = [0, 1, center_frequency_S, linewidth]
                p0_AS = [0, 1, center_frequency_AS, linewidth]

            # Define the fit function
            models = {"Lorentz": lorentzian, "DHO": DHO, "Lorentz_e": lorentzian_elastic, "DHO_e": DHO_elastic}
            f = models[model]

            # Define the windows of fit
            window_S = np.where(np.abs(frequency-center_frequency_S)<window_peak_fit/2)
            window_AS = np.where(np.abs(frequency-center_frequency_AS)<window_peak_fit/2)

            # Apply the fit on both peaks
            popt_S, pcov_S = optimize.curve_fit(f,
                                                frequency[window_S],
                                                data[window_S],
                                                p0_S)
        
            popt_AS, pcov_AS = optimize.curve_fit(f,
                                                  frequency[window_AS],
                                                  data[window_AS],
                                                  p0_AS)
            
            # Extract the errors in the form of standard deviations
            std_S = np.sqrt(np.diag(pcov_S))
            std_AS = np.sqrt(np.diag(pcov_AS))
            
            std = np.sqrt(std_AS**2+std_S**2)
            popt = 0.5*(np.array(popt_S)+np.array(popt_AS))
            popt[-2] = 0.5*(popt_AS[-2] - popt_S[-2])
        
        else:
            if correct_elastic: 
                p0 = [0, 0, 1, center_frequency, linewidth]
                model = model+"_e"
            else: 
                p0 = [0, 1, center_frequency, linewidth]
            
            # Define the fit function
            models = {"Lorentz": lorentzian, "DHO": DHO, "Lorentz_e": lorentzian_elastic, "DHO_e": DHO_elastic}
            f = models[model]

            window = np.where(np.abs(frequency-center_frequency)<window_peak_fit/2)

            popt, pcov = optimize.curve_fit(f,
                                            frequency[window],
                                            data[window],
                                            p0)
            
            std = np.sqrt(np.diag(pcov))

        return popt, std
