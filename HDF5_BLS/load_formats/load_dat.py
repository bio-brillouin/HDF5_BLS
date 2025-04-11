import os
import numpy as np
from scipy.signal import butter, filtfilt
from numpy.polynomial import Chebyshev

from HDF5_BLS.load_formats.errors import LoadError_parameters


def load_dat_GHOST(filepath):
    """Loads DAT files obtained with the GHOST software

    Parameters
    ----------
    filepath : stt
        The filepath to the GHOST file

    Returns
    -------
    dict
        The dictionnary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
    """
    metadata = {}
    data = []
    name, _ = os.path.splitext(filepath)
    attributes = {}

    with open(filepath, 'r') as file:
        lines = file.readlines()
        # Extract metadata
        for line in lines:
            if line.strip() == '':
                continue  # Skip empty lines
            if any(char.isdigit() for char in line.split()[0]):
                break  # Stop at the first number
            else:
                # Split metadata into key-value pairs
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        # Extract numerical data
        for line in lines:
            if line.strip().isdigit():
                data.append(int(line.strip()))

    data = np.array(data)
    attributes['MEASURE.Sample'] = metadata["Sample"]
    attributes['SPECTROMETER.Scanning_Strategy'] = "point_scanning"
    attributes['SPECTROMETER.Type'] = "TFP"
    attributes['SPECTROMETER.Illumination_Type'] = "CW Laser"
    attributes['SPECTROMETER.Detector_Type'] = "Photon Counter"
    attributes['SPECTROMETER.Filtering_Module'] = "None"
    attributes['SPECTROMETER.Wavelength_(nm)'] = metadata["Wavelength"]
    attributes['SPECTROMETER.Scan_Amplitude_(GHz)'] = metadata["Scan amplitude"]
    spectral_resolution = float(float(metadata["Scan amplitude"])/data.shape[-1])
    attributes['SPECTROMETER.Spectral_Resolution_(GHz)'] = str(spectral_resolution)

    frequency = np.linspace(-float(metadata["Scan amplitude"])/2, float(metadata["Scan amplitude"])/2, data.shape[-1])

    dic = {"PSD": {"Name": "PSD","Data": data},
           "Frequency": {"Name": "Frequency", "Data": frequency}, 
           "Attributes": attributes}
    return dic

def load_dat_TimeDomain(filepath, parameters = None):
    """Loads DAT files obtained with the TimeDomain software

    Parameters
    ----------
    filepath : stt
        The filepath to the TimeDomain file
    parameters : dict, optional
        A dictionnary with the parameters to load the data, by default None. In the case where no parameters are provided, the function will return a list of the names of the parameters as string that have to be provided to load the data.

    Returns
    -------
    dict
        The dictionnary with the time vector, the time resolved data and the attributes of the file stored respectively in the keys "Data", "Abscissa_dt" and "Attributes"
    """

    def scrape_meta_file(filepath, attributes, process):
        # Read meta file
        with open(filepath, 'r') as file: content = file.read().splitlines()
        
        # Store informations in the attributes dictionnary
        for e in content:
            if e[0] == "%": continue 
            elif e[:4] == "scp.": 
                e = e[4:].split("=")
                for t in ("[","]",";","{","}","'"): e[1] = e[1].replace(t,"")
                attributes["MEASURE."+e[0].strip()] = e[1].strip()
            else: 
                e = e.replace(" ","_")
                e = e.split("=")
                attributes["MEASURE."+e[0].strip()] = e[1].strip()

        # Add bytes per point and format from extracted informations
        temp = [np.int8, np.int16, np.float32]
        attributes["MEASURE.bytes_per_point"] =  2**(int(attributes["MEASURE.format"])-1)
        attributes["MEASURE.fmt"] = temp[int(attributes["MEASURE.format"])-1]

        # Adds the process to the process list
        process.append(f"Opened meta file {filepath}, extracted parameters and created attributes dictionary.")

        return attributes, process

    def scrape_con_file(filepath, attributes, process):
        n_traces = attributes["MEASURE.n_traces"] 

        # Open the con file and read its content
        with open(filepath, 'r') as file:  content = file.read().split()

        # Search for scan parameters and extract values
        scan_parameters = []
        for i, line in enumerate(content):
            if line == "scan" and i + 3 < len(content):
                    scan_parameters.append([float(content[i + 1]), float(content[i + 2]), float(content[i + 3])])

        # Get the scan parameters
        if scan_parameters:
            Nx_steps = (scan_parameters[0][1] - scan_parameters[0][0])//scan_parameters[0][2] + 1
            dx_um = scan_parameters[0][2] * 1e3
            if len(scan_parameters) > 1:
                temp_process = "on x and y"
                Ny_steps = (scan_parameters[1][1] - scan_parameters[1][0]) // scan_parameters[1][2] + 1
                dy_um = scan_parameters[1][2] * 1e3
            else:
                temp_process = "on x"
                Ny_steps = 1
                dy_um = 0
        else:    
            temp_process = "on y"
            Nx_steps, Ny_steps, dx_um, dy_um = 1, n_traces, 0, 1

        # Adjust to get the right number of traces
        if Nx_steps * Ny_steps != n_traces:
            Ny_steps = Ny_steps - 1

        # NOTE: 
        #     x_um = np.arange(attribute["MEASURE.Nx_steps"]) * attribute["MEASURE.dx_um"]
        #     y_um = np.arange(attribute["MEASURE.Ny_steps"]) * attribute["MEASURE.dy_um"]

        attributes["MEASURE.Nx_steps"] = int(Nx_steps)
        attributes["MEASURE.Ny_steps"] = int(Ny_steps)
        attributes["MEASURE.dx_um"] = dx_um
        attributes["MEASURE.dy_um"] = dy_um

        # Updated the process list
        process.append(f"Opened con file {filepath}, extracted scan parameters {temp_process} and updated attributes dictionary.")

        return process

    def basic_process(filepath, attributes, process):
        n_traces = int(attributes["MEASURE.n_traces"])
        points_per_trace = int(attributes["MEASURE.points_per_trace"])
        bytes_per_point = int(attributes["MEASURE.bytes_per_point"])
        fmt = attributes["MEASURE.fmt"]
        Nx_steps = int(attributes["MEASURE.Nx_steps"])
        Ny_steps = int(attributes["MEASURE.Ny_steps"])
        vgain = float(attributes["MEASURE.vgain"])
        voff = float(attributes["MEASURE.voff"])
        ac_gain = float(attributes["MEASURE.ac_gain"]) # PROBLEM HERE


        # Initialize the data array
        data_tmp = np.zeros((n_traces, points_per_trace))
        # load and basic process for .dat file
        with open(filepath, 'r') as fi:
            # Loop through each trace and read data
            for i in range(n_traces):
                # Move the file pointer to the correct position
                fi.seek(i * points_per_trace * bytes_per_point)
                # Read the data for the current trace
                data_tmp[i, :] = np.fromfile(fi, dtype=fmt, count=points_per_trace)

            data_tmp2 = data_tmp.reshape(Nx_steps, Ny_steps, points_per_trace, order='F')
            # apply appropriate voltage gain and voltage offset from meta file
            data_ac = (data_tmp2 * vgain + voff)/ac_gain

        # reverse left-right time trace if needed
        if attributes["MEASURE.bool_reverse_data"]:
            data_ac = data_ac[:, :, ::-1]

        # Update the process list
        process.append(f"Opened data file {filepath}, extracted data based on attributes dictionary.")

        return data_ac, process

    def load_dc(attributes, data_ac, filepath_dc, process):
        Nx_steps = int(attributes["MEASURE.Nx_steps"])
        Ny_steps = int(attributes["MEASURE.Ny_steps"])
        if os.path.isfile(filepath_dc):
            with open(filepath_dc, 'rb') as fi:
                # Read all data as float32
                tmp_dc = np.fromfile(fi, dtype=np.float32)        
            dc_samples = int(len(tmp_dc) / (Nx_steps * Ny_steps))
            data_dc = np.mean(tmp_dc.reshape(Nx_steps, Ny_steps, dc_samples, order='F'), 2)
            data_mod = data_ac / data_dc.reshape(Nx_steps, Ny_steps, 1, order='F')
            process.append(f"Opened DC file {filepath_dc} and used it to make modulation depth.")
        else:
            data_mod = data_ac
            process.append(f"The filepath {filepath_dc} is incorrect, using AC data only.")
        return data_mod, process

    def find_copeaks(attributes, data_mod, process):   
        # Find copeak and create signal of ROI
        signal_length = int(attributes["MEASURE.signal_length"])
        signal_window = np.arange(signal_length)
        if "MEASURE.forced_copeak" in attributes and attributes["MEASURE.forced_copeak"] == 'yes': # Forcing copeak location
            Nx_steps = int(attributes["MEASURE.Nx_steps"])
            Ny_steps = int(attributes["MEASURE.Ny_steps"])  
            copeak_val = attributes["MEASURE.copeak_start"]
            copeak_idxs_shifted = copeak_val * np.ones((Nx_steps, Ny_steps))
            temp_process = f"forcing copeak based on a copeak start value of {attributes["MEASURE.copeak_start"]}"
        else:# Finding copeak locations
            copeak_range = int(attributes["MEASURE.copeak_start"]) + np.arange(-int(attributes["MEASURE.copeak_window"]), int(attributes["MEASURE.copeak_window"])+1, 1).astype(int)
            mod_copeak_windows = data_mod[:, :, copeak_range-1]
            first_vals = mod_copeak_windows[:, :, 0]
            tiled_mod = np.tile(first_vals[:, :, np.newaxis], (1, 1, len(copeak_range)))
            copeak_idxs = np.argmax(np.abs(mod_copeak_windows - tiled_mod), axis=2)
            # shift towards signal away from copeak
            copeak_idxs_shifted = copeak_idxs + copeak_range[0] - 1 + float(attributes["MEASURE.start_offset"])
            temp_process = f"without forcing copeak, based on a copeak start value of {attributes["MEASURE.copeak_start"]}, a copeak window of {attributes["MEASURE.copeak_window"]}, and a start offset of {attributes["MEASURE.start_offset"]}"
        copeak_idxs_shifted = copeak_idxs_shifted.astype(int)

        # Add offsets to the start indices (broadcasting)
        signal_idxs = copeak_idxs_shifted[..., np.newaxis] + signal_window

        # Use advanced indexing to extract the windows
        mod_shifted = data_mod[np.arange(data_mod.shape[0])[:, np.newaxis, np.newaxis],  # Batch indices
                    np.arange(data_mod.shape[1])[np.newaxis, :, np.newaxis],  # Row indices
                    signal_idxs]  # Column indices (from expanded_idxs)
        
        process.append(f"Finding copeak location {temp_process} and creating signal of ROI.")

        return mod_shifted, signal_idxs, process

    def make_time(attributes, process):
        points_per_trace = int(attributes["MEASURE.points_per_trace"])
        hint = float(attributes["MEASURE.hint"])
        hoff = float(attributes["MEASURE.hoff"])
        rep_rate = float(attributes["MEASURE.rep_rate"])
        delay_rate = float(attributes["MEASURE.delay_rate"])
        signal_length = int(attributes["MEASURE.signal_length"])
        t_tmp = np.arange(0, points_per_trace) * hint + hoff
        t_raw = t_tmp / (rep_rate/delay_rate)
        data_t = t_raw[0:signal_length] - t_raw[0]
        dt = data_t[1]

        process.append(f"Created time vector based on hint = {hint}, hoff = {hoff}, rep_rate = {rep_rate}, delay_rate = {delay_rate}, and signal_length = {signal_length}.")

        return data_t, dt, process

    def LPfilter(attributes, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter
        if "MEASURE.LPfilter" in attributes:
            butter_order = attributes["MEASURE.butter_order"]
            # Cutoff frequency for lowpass filter
            LP = attributes["MEASURE.LPfilter"] * 1e9
            # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
            normalized_cutoff = LP / nyquist_freq  
            # Design a Butterworth lowpass filter
            b, a = butter(butter_order, normalized_cutoff, btype='low')
            for i in range(data_in.shape[0]):  
                for j in range(data_in.shape[1]):  
                    # Apply the filter using filtfilt (zero-phase filtering)
                    data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :])
            return data_in   

    # Butterworth-based high pass filter
    def HPfilter(attributes, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter        
        if "MEASURE.HPfilter" in attributes:
            butter_order = attributes["MEASURE.butter_order"]
            HP = attributes["MEASURE.HPfilter"] * 1e9
            normalized_cutoff = HP / nyquist_freq  
            b, a = butter(butter_order, normalized_cutoff, btype='high')
            for i in range(data_in.shape[0]):  
                for j in range(data_in.shape[1]):  
                    data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :]) 
        return data_in 

    # To remove the thermal background envelope, fit and subtract a polynomial (Chebyshev model currently)
    def polyfit_removal(attributes, data_in):
        # polynomial fit and removal
        degree = attributes["polyfit_order"] 
        # Create x values for fitting (scaled to the range [-1, 1])
        xfit = np.linspace(-1, 1, data_in.shape[2])  
        # Create a placeholder for fitted coefficients (for each fit along the third dimension)
        coeffs = np.zeros((data_in.shape[0], data_in.shape[1], degree + 1))  
        mod_poly = np.zeros((data_in.shape[0], data_in.shape[1], len(xfit)))  
        # Fit a Chebyshev polynomial to each slice along the third dimension
        for i in range(data_in.shape[0]):
            for j in range(data_in.shape[1]):
                # Fit a Chebyshev polynomial of degree `degree` to the data in the third dimension
                cheb_fit = Chebyshev.fit(xfit, data_in[i, j, :], degree)
                coeffs[i, j, :] = cheb_fit.coef  # Store the coefficients
                # Create the Chebyshev object for the current coefficients
                cheb_poly = Chebyshev(coeffs[i, j, :])        
                # Evaluate the polynomial at the new points
                mod_poly[i, j, :] = cheb_poly(xfit)# Initialize an array to store the evaluated values
        # Subtract polynomial fit from signal          
        data_pro = data_in - mod_poly
        return data_pro, mod_poly      

    # Use a Fast Fourier Transform to convert the time signal into the frequency domain.
    # Zero padding is used to increase the sampling rate in the freq domain
    def take_FFT(attributes, data_in, dt):
        zp = attributes["MEASURE.zp"] # zero padding coefficient
        fmin_search = attributes["MEASURE.fmin"] * 1e9
        fmax_search = attributes["MEASURE.fmax"] * 1e9
        fmin_plot = attributes["MEASURE.fmin_plot"] * 1e9
        fmax_plot = attributes["MEASURE.fmax_plot"] * 1e9
        Nx_steps = attributes["MEASURE.Nx_steps"]
        Ny_steps = attributes["MEASURE.Ny_steps"]
        fB_GHz = np.zeros((Nx_steps, Ny_steps))
        for i in range(data_in.shape[0]):  
            for j in range(data_in.shape[1]): 
                signal_now = data_in[i, j, :]
                fft_out = (2/len(signal_now))*abs(np.fft.fft(signal_now, zp)) # calculate zero-padded and amplitude normalised fft
                fft_shifted= np.fft.fftshift(fft_out)
                if i == 0 and j == 0:
                    freqs = np.fft.fftfreq(len(fft_shifted), d=dt) # calculate the frequency axis information based on the time-step
                    freqs_shifted = np.fft.fftshift(freqs)
                    # Below separates frequency spectrum into two arrays:
                    # - *roi* one with a narrow band where the fB will be searched
                    # - *plot* one with a wider band that will be used for plotting and main output
                    roi_idx = np.where((freqs_shifted >= fmin_search) & (freqs_shifted <= fmax_search)) # original spectrum spans +/- 1/dt centred on the rayleigh peak (f=0)
                    plot_idx = np.where((freqs_shifted >= fmin_plot) & (freqs_shifted <= fmax_plot)) # original spectrum spans +/- 1/dt centred on the rayleigh peak (f=0)
                    plot_fft = np.zeros((Nx_steps, Ny_steps, np.size(plot_idx)))
                    freqs_plot_GHz = freqs_shifted[plot_idx] * 1e-9
                    freqs_roi_GHz = freqs_shifted[roi_idx] * 1e-9
                data_fft = fft_shifted[roi_idx]
                plot_fft[i, j, :] = fft_shifted[plot_idx]
                # below not strictly needed b/c they're calculated in treat() I think
                max_idx = np.argmax(data_fft) # find frequency of peak with max amplitude
                # store found Brillouin frequency measurements
                fB_GHz[i, j] = freqs_roi_GHz[max_idx]

                ## Sal, add timedomain specific fwhm measurements here?
                #fft_norm = fft_pos/max(fft_pos) # normalise peak amplitude to one
                #ifwhm = np.where(fft_norm >= 0.5) # rough definition for fwhm
                #fpeak = freqs_GHz[ifwhm]
                #fwhm = fpeak[-1] - fpeak[0]  

        return plot_fft, freqs_plot_GHz, fB_GHz    

    if parameters is None:
        parameters_list = ["ac_gain", "bool_reverse_data", "signal_length", "copeak_start", "copeak_window", "start_offset", "rep_rate", "delay_rate", "file_con"]
        raise LoadError_parameters(f"The following parameters have to be provided: {"; ".join(parameters_list)}", parameters_list)
    else:
        attributes = {}
        for k, v in parameters.items():
            if k == "file_con": 
                filepath_con = parameters["file_con"]
            else:
                attributes["MEASURE."+k] = v

    file_base, _ = os.path.splitext(filepath)
    process = []

    # Initializes the attributes dictionary
    attributes, process = scrape_meta_file(file_base + ".m", attributes, process)

    # Read the confile and update attributes
    process = scrape_con_file(filepath_con, attributes, process)

    # Load and basic processing of .dat file
    data_ac, process = basic_process(file_base + ".dat", attributes, process)

    # Extract DC measurements and make units modulation depth
    filepath_dc = file_base[:-6] + "a2d1_1f.d"
    data_mod, process = load_dc(attributes, data_ac, filepath_dc, process)

    # Find and crop to signal ROI
    mod_shifted, signal_idxs, process = find_copeaks(attributes, data_mod, process)

    # Build time vector
    data_t, dt, process = make_time(attributes, process)

    # Low pass filter the signal
    mod_shifted = LPfilter(attributes, mod_shifted, dt)

    # Polynomial fit and removal
    data_pro, polyfit = polyfit_removal(parameters, mod_shifted)

    # High pass filter the signal
    data_pro = HPfilter(attributes, data_pro, dt)

    # Take FFT of the time signal
    fft_out, freqs_out_GHz, fB_GHz = take_FFT(attributes, data_pro, dt)

    attributes["MEASURE.Process"] = ";".join(process)
    attributes['SPECTROMETER.Type'] = "TimeDomain"
    attributes['SPECTROMETER.Filtering_Module'] = "None"

    return {"Raw_Data": {"Name": "Time measures", "Data": data_t}, 
            "Abscissa_Time": {"Name": "Time axis", "Data": dt},
            "Attributes": attributes}

