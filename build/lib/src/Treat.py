import numpy as np
from scipy import optimize

Treat_version = 0.1

class Treat():
    """This class is meant to offer a standard way of treating the data. Please refer to the dedicated notebook (found on GitHub) to find explicit descriptions of the algorithms.
    """
    def __init__(self):
        self.treat_steps = []
        self.version = Treat_version
    
    def reference_deconvolution(self, frequency, data, impulse_response, impulse_response_frequency = None, recenter_IR = True):
        """Deconvolution of the data with the given impulse response of the instrument. This impulse response should be in the form of the response of an instrument to a monochromatic source at a given order of interference. IMPORTANT: for interferometers returning different interference orders, do not use the full interference pattern but limit the data to one interference order. The deconvolution is performed using zero-padded signals so as to avoid circular convolution

        Parameters
        ----------
        frequency : numpy array
            The frequency array of the data
        data : numpy array
            The data array to be deconvolved
        impulse_response : numpy array
            The impulse response used for deconvolution
        impulse_response_frequency : numpy array, optional
            The frequency axis of the impulse response. Note that by default this frequency axis is not considered absolute and will be recentered on the peak maximum. To deactivate this recentering, you can set the next parameter recenter_IR to False. By default, the frequency axis of the data is used and its value is set by default to None
        recenter_IR : boolean, optional
            If the frequency axis used for the IR is not centered on the maximum of the IR, recenters it to the maximum of the IR (default mode), by default True
        
        Returns
        -------
        data_deconvolved: numpy array
            The data array after deconvolution
        """
        # Defines the length of the data after zero padding to avoid circular convolution and maximize FFT efficiency 
        M = data.size+impulse_response.size
        M = 2**(np.ceil(np.log(M)/np.log(2)))

        print(data.size+impulse_response.size, M)

        self.treat_steps.append("Reference Deconvolution")


    def fit_model(self, frequency, data, center_frequency, linewidth, normalize = True, model = "Lorentz", fit_S_and_AS = True, window_peak_find = 1, window_peak_fit = 3, correct_elastic = False):
        """Fitting function that performs a fit on the selected spectrum and returns the fitted values and the standard deviations on the fitted parameters. When 2 peaks are fitted, the standard deviation returned by the function corresponds to the standard deviation of two independent events, that is std_{avg} = sqrt{std_{S}^2 + std_{AS}^2}

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

            self.treat_steps.append(f"Windowing of Stokes and anti-Stokes peaks around {center_frequency_S:.2f}GHz and {center_frequency_AS:.2f}GHz respectively")

            center_frequency = center_frequency_S
        else:
            window_peak_find = np.where(np.abs(frequency-center_frequency)<window_peak_find/2)
            pol_temp = np.polyfit(frequency[window_peak_find], data[window_peak_find],2)
            center_frequency = -pol_temp[1]/(2*pol_temp[0])
            self.treat_steps.append(f"Windowing of a single peak around {center_frequency:.2f}GHz ")

        # Normalize the data is not already done
        if normalize: 
            data = self.normalize_data(data, peak_pos=np.argmin(np.abs(frequency-center_frequency)))

        # Apply the fit
        if fit_S_and_AS:
            # Define the initial parameters of the fit
            if correct_elastic: 
                p0_S = [0, 0, 1, center_frequency_S, linewidth]
                p0_AS = [0, 0, 1, center_frequency_AS, linewidth]
                treat_step = f"Fitting both Stokes and anti-Stokes peaks with a {model} model taking into account the effect of the elastic peak"
                model = model+"_e"
            else: 
                p0_S = [0, 1, center_frequency_S, linewidth]
                p0_AS = [0, 1, center_frequency_AS, linewidth]
                treat_step = f"Fitting both Stokes and anti-Stokes peaks with a {model} model without taking into account the effect of the elastic peak"

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
                treat_step = f"Fitting given peakwith a {model} model, taking into account the effect of the elastic peak"
                model = model+"_e"
            else: 
                p0 = [0, 1, center_frequency, linewidth]
                treat_step = f"Fitting given peak with a {model} model without taking into account the effect of the elastic peak"
            
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
        if remove_offset: 
            data_treat = self.remove_offset(data)
        if peak_pos == -1: 
            peak_pos = np.argmax(data)
        window = [max(0, peak_pos-window), min(data.size, peak_pos+window)]
        val = np.max(data[window[0]:window[1]])
        self.treat_steps.append(f"Normalizing the data based on the given peak's amplitude")
        return data_treat/val
    
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
        self.treat_steps.append(f"Removing data's offset by averaging the data value around the point of lowest intensity")
        return data_treat

    def resample(self, frequency, data):
        """Resamples the frequency and data arrays by creating a new frequency array where samples are equidistant

        Parameters
        ----------
        frequency : numpy array
            The frequency array used for resampling with samples of same widths
        data : numpy array
            The data array that will be resampled following the resampling of the frequency axis. The resampling on the data is done by locally fitting a quadratic polynomial.

        Returns
        -------
        new_frequency : numpy array
            The resampled frequency array
        new_data : numpy array
            The resampled data array
        """
        # Creates the new arrays
        new_frequency = np.linspace(frequency[0], frequency[-1], frequency.size)
        new_data = np.zeros(frequency.size)

        # Resampling by fitting a quadratic polynomial
        for i,f in enumerate(new_frequency):
            pos = np.argmin(np.abs(frequency-f))
            if pos<2:
                wndwf = frequency[:3]
                wndwd = data[:3]
            elif pos > data.size-3:
                wndwf = frequency[-3:]
                wndwd = data[-3:]
            else: 
                wndwf = frequency[pos-1:pos+2]
                wndwd = data[pos-1:pos+2]
            pol = np.polyfit(wndwf, wndwd,2)
            new_data[i] = np.poly1d(pol)(f)
        self.treat_steps.append("Resample the signal")
        return new_frequency, new_data
