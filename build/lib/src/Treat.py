import numpy as np
from scipy import optimize

Treat_version = 0.1


class TreatmentError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Treat():
    """This class is meant to offer a standard way of treating the data. Please refer to the dedicated notebook (found on GitHub) to find explicit descriptions of the algorithms.
    """
    def __init__(self):
        self.treat_steps = []
        self.version = Treat_version
    
    def fit_model(self, frequency, data, center_frequency, linewidth, normalize = True, model = "Lorentz", fit_S_and_AS = True, window_peak_find = 1, window_peak_fit = 3, correct_elastic = False, IR_wndw = None, freq_IR = None, data_IR = None):
        """Fitting function that performs a fit on the selected spectrum and returns the fitted values and the standard deviations on the fitted parameters. When 2 peaks are fitted, the standard deviation returned by the function corresponds to the standard deviation of two independent events, that is std_{avg} = sqrt{std_{S}^2 + std_{AS}^2}. This function also takes into account the impulse response of the spectrometer when applying the fit, which therefore returns a 

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
        wndw_IR : 2-tuple, optional
            If the impulse response can be recovered from the spectrum, the corresponding window on the frequency axis where to recover the response
        freq_IR : numpy array, optional
            The frequency of the impulse response
        data_IR : numpy array, optional
            The data of the impulse response

        Returns
        -------
        optimal_parameters: tuple
            The returned optimal parameters for the fit (offset, amplitude, center_frequency, linewidth) averaged if both the Stokes and anti-Stokes peaks are used
        variance: tuple
            The returned variance on the fitted parameters (offset, amplitude, center_frequency, linewidth)
        """
        frequency, data = self.resample(frequency, data)
        
        # Extract the impulse response
        convolution = False
        if not IR_wndw is None: 
            _, IR = self.wndw_data_from_freq(data, frequency,IR_wndw[0],IR_wndw[1])
            IR = IR - min(IR) # Rough removal of any offset
            IR = IR/max(IR) # Rough normalization of the peak
            convolution = True
            self.treat_steps.append(f"Add convolution by the impulse response in the fitting function")
        elif not freq_IR is None:
            assert freq_IR.size == data_IR.size, "the drequency array and data array fro the impulse response are not of same size"
            wndw = np.where((frequency>=min(freq_IR))&(frequency<=max(freq_IR)))
            _, IR = self.resample(freq_IR, data_IR, frequency[wndw])
            IR = IR - min(IR) # Rough removal of any offset
            IR = IR/max(IR) # Rough normalization of the peak
            convolution = True
            self.treat_steps.append(f"Add convolution by the impulse response in the fitting function")
        else:
            self.treat_steps.append(f"No convolution by the impulse response in the fitting function were added")

        # Define the fitting functions taking into account the convolutions.
        def lorentzian(nu, b, a, nu0, gamma):
            func = b + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
            if convolution: return np.convolve(func, IR, "same")
            return func
        
        def lorentzian_elastic(nu, ae, be, a, nu0, gamma):
            func =  be + ae*nu + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
            if convolution: return np.convolve(func, IR, "same")
            return func
        
        def DHO(nu, b, a, nu0, gamma):
            func = b + a*(gamma*nu0**2)/((nu**2-nu0**2)**2+gamma*nu0**2)
            if convolution: return np.convolve(func, IR, "same")
            return func
        
        def DHO_elastic(nu, ae, be, a, nu0, gamma):
            func = be + ae*nu + a*(gamma*nu0**2)/((nu**2-nu0**2)**2+gamma*nu0**2)
            if convolution: return np.convolve(func, IR, "same")
            return func
        
        # Refine the position of the peak with a quadratic polynomial fit
        try:
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
        except:
            raise TreatmentError("The windowing of the peaks before treatment failed.")

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
        self.treat_steps.append(treat_step)

        return popt, std

    def wndw_data_from_freq(self, data, freq, fmin, fmax = None):
        """Returns a window of the data and the frequency arrays corresponding to a given region of the frequency array.

        Parameters
        ----------
        data : numpy array
            The raw data array
        freq : numpy array
            The frequency array
        fmin : float
            The left side of the window. Note that if the window is symetric, fmax is not needed and -fmin will be taken as the right side of the window
        fmax : _type_, optional
            The right side of the window. Optional when the window is symetric, hence fmax = -fmin, by default None

        Returns
        -------
        numpy array
            The windowed frequency
        numpy array
            The windowed data
        """
        if type(fmax) is None: fmax = -fmin
        if fmin>fmax: fmin, fmax = fmax, fmin
        wndw = np.where((freq>fmin)&(freq<fmax))
        return freq[wndw], data[wndw]

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

    def resample(self, frequency, data, new_frequency = None):
        """Resamples the frequency and data arrays by creating a new frequency array where samples are equidistant

        Parameters
        ----------
        frequency : numpy array
            The frequency array used for resampling with samples of same widths
        data : numpy array
            The data array that will be resampled following the resampling of the frequency axis. The resampling on the data is done by locally fitting a quadratic polynomial.
        new_frequency : numpy array, optional
            A new frequency array to resample the data on.

        Returns
        -------
        new_frequency : numpy array
            The resampled frequency array
        new_data : numpy array
            The resampled data array
        """
        # Creates the new arrays
        if new_frequency is None: 
            new_frequency = np.linspace(frequency[0], frequency[-1], frequency.size)
        new_data = np.zeros(new_frequency.size)

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
