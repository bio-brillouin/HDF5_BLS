import os
import numpy as np
from scipy.signal import butter, filtfilt
from numpy.polynomial import Chebyshev
import re
import logging

from HDF5_BLS.load_formats.errors import LoadError_parameters

class PipelineLogger(logging.Handler):
    def __init__(self):
        super().__init__()
        self.pipeline = []

    def emit(self, record):
        message = record.getMessage()
        if message.startswith("Call:"):
            _, func_name, args, kwargs = message.split(":", 3)
            self.pipeline.append({
                "function": func_name.strip(),
                "args": eval(args.strip()),
                "kwargs": eval(kwargs.strip())
            })

class TimeDomain():
    def __init__(self, filepath, attributes = None):
        self.filepath = filepath
        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = attributes
        self.data = None

    def scrape_m_file(self):
        meta_filebase = self.filepath[0:len(self.filepath)-4]
        meta_file = meta_filebase + ".m"
        # extract useful information from the relevant meta-file
        with open(meta_file, 'r') as file:
            content = file.read()
            meta_format = int(re.search(r'scp\.format\s*=\s*([\d\.]+);', content).group(1))
            if meta_format == 1:
                bytes_per_point, fmt = 1, np.int8
            elif meta_format == 2:
                bytes_per_point, fmt = 2, np.int16
            elif meta_format == 3:
                bytes_per_point, fmt = 4, np.float32
            n_traces = int(re.search(r'scp\.n_traces\s*=\s*([\d\.]+);', content).group(1))
            points_per_trace = int(re.search(r'scp\.points_per_trace\s*=\s*([\d\.]+);', content).group(1))
            vgain = float(re.search(r'scp\.vgain\s*=\s*\[\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)]\s*;', content).group(1))
            voff = float(re.search(r'scp\.voff\s*=\s*\[\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)]\s*;', content).group(1))
            hint = float(re.search(r'scp\.hint\s*=\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)\s*;', content).group(1))
            hoff = float(re.search(r'scp\.hoff\s*=\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)\s*;', content).group(1))
        dic = {"TIMEDOMAIN.bytes_per_point": bytes_per_point,
               "TIMEDOMAIN.fmt": fmt,
               "TIMEDOMAIN.n_traces": n_traces,
               "TIMEDOMAIN.points_per_trace": points_per_trace,
               "TIMEDOMAIN.vgain": vgain,
               "TIMEDOMAIN.voff": voff,
               "TIMEDOMAIN.hint": hint,
               "TIMEDOMAIN.hoff": hoff}
        self.attributes.update(dic)

    def scrape_con_file(self):
        n_traces = self.attributes["TIMEDOMAIN.n_traces"]
        # Open the file and read its contents as a single string
        with open(self.attributes["TIMEDOMAIN.file_con"], 'r') as file:
            content = file.read()  # Get the entire content as a string
        # Normalize content to ensure all words are separated by newlines
        lines = '\n'.join(content.split())
        # Split lines into a list for easier processing
        lines_list = lines.splitlines()
        # Search for 'scan' and extract the next line's value
        start_val, end_val, step_val = {}, {}, {}
        scan_count = -1
        # Extract start/stop/step values for x and y scan parameters
        for i, line in enumerate(lines_list):
            if line == "scan":
                scan_count = scan_count + 1
                if i + 1 < len(lines_list):  # Ensure there's a subsequent line
                    start_val[scan_count] = float(lines_list[i + 1])
                    end_val[scan_count] = float(lines_list[i + 2])
                    step_val[scan_count] = float(lines_list[i + 3])

        # Sal, the above doesn't account for axis 1 existing, but axis 0 not. Just takes first 'scan' instance and assigns it to local var x, and if sencond to y
        # Organise start/stop/step values into variables and create x/y vectors (in microns)
        if start_val:
            tmp_x = np.arange(start_val[0], end_val[0], step_val[0])
            Nx_steps = len(tmp_x)
            x_um = np.linspace(0, Nx_steps-1, Nx_steps) * step_val[0] * 1e3 # mm to microns
            if len(start_val) > 1:
                tmp_y = np.arange(start_val[1], end_val[1], step_val[1])
                Ny_steps = len(tmp_y)
                y_um = np.linspace(0, Ny_steps-1, Ny_steps) * step_val[1] * 1e3 # mm to microns
            else:
                Ny_steps, y_um = 1, np.zeros((1, n_traces))
        else:
            Nx_steps, Ny_steps, x_um, y_um = 1, n_traces, np.zeros((1, n_traces)), np.linspace(0, n_traces-1, n_traces)

        if Nx_steps * Ny_steps == n_traces:
            print('Size of X and Y data matches number of traces, continuing...')
        else:
            print('Size of X and Y data do not match number of traces, reducing Y by 1 and trying again...')
            Ny_steps = Ny_steps - 1
            y_um = y_um[0:-1]
        return {
            "TIMEDOMAIN.Nx_steps": Nx_steps,
            "TIMEDOMAIN.Ny_steps": Ny_steps,
            "TIMEDOMAIN.x_um": x_um,
            "TIMEDOMAIN.y_um": y_um
        }

    def basic_process(attributes, filepath):
        n_traces = attributes["TIMEDOMAIN.n_traces"]
        points_per_trace = attributes["TIMEDOMAIN.points_per_trace"]
        bytes_per_point = attributes["TIMEDOMAIN.bytes_per_point"]
        fmt = attributes["TIMEDOMAIN.fmt"]
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
        vgain = attributes["TIMEDOMAIN.vgain"]
        voff = attributes["TIMEDOMAIN.voff"]
        ac_gain = attributes["TIMEDOMAIN.ac_gain"]
        # load and basic process for .dat file
        with open(filepath, 'r') as fi:
            # Create an array of traces
            traces = np.arange(1, n_traces + 1)
            # Initialize the data array
            data_tmp = np.zeros((len(traces), points_per_trace))
            # Loop through each trace and read data
            print('Loading time domain data...')
            for i, trace in enumerate(traces):
                # Move the file pointer to the correct position
                fi.seek((trace - 1) * points_per_trace * bytes_per_point)
                # Read the data for the current trace
                data_tmp[i, :] = np.fromfile(fi, dtype=fmt, count=points_per_trace)

            data_tmp2 = data_tmp.reshape(Nx_steps, Ny_steps, points_per_trace, order='F')
            # apply appropriate voltage gain and voltage offset from meta file
            data_ac = (data_tmp2 * vgain + voff)/ac_gain

        # reverse left-right time trace if needed
        if attributes["TIMEDOMAIN.bool_reverse_data"]:
            data_ac = data_ac[:, :, ::-1]

        return data_ac

    def load_dc(attributes, data_ac, filepath_dc):
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
        if os.path.isfile(filepath_dc):
            print('DC data found: ', filepath_dc)
            with open(filepath_dc, 'rb') as fi:
                # Read all data as float32
                tmp_dc = np.fromfile(fi, dtype=np.float32)        
            dc_samples = int(len(tmp_dc) / (Nx_steps * Ny_steps))
            data_dc = np.mean(tmp_dc.reshape(Nx_steps, Ny_steps, dc_samples, order='F'), 2)
            data_mod = data_ac / data_dc.reshape(Nx_steps, Ny_steps, 1, order='F')
        else:
            print('Could not find a valid DC data file, using AC data only')
            data_mod = data_ac
        return data_mod

    def find_copeaks(attributes, data_mod):
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
        print('Beginning signal processing...')     
        # find copeak and create signal of ROI
        signal_length = attributes["TIMEDOMAIN.signal_length"]
        signal_window = np.arange(signal_length)
        if attributes["TIMEDOMAIN.bool_forced_copeaks"]:
            print('Forcing copeak location...')
            copeak_val = attributes["TIMEDOMAIN.copeak_start"]
            copeak_idxs_shifted = copeak_val * np.ones((Nx_steps, Ny_steps))
        else:
            print('Finding copeak locations...')
            copeak_range = attributes["TIMEDOMAIN.copeak_start"] + np.arange(-attributes["TIMEDOMAIN.copeak_window"], attributes["TIMEDOMAIN.copeak_window"]+1, 1)
            copeak_range = copeak_range.astype(int)
            mod_copeak_windows = data_mod[:, :, copeak_range-1]
            first_vals = mod_copeak_windows[:, :, 0]
            tiled_mod = np.tile(first_vals[:, :, np.newaxis], (1, 1, len(copeak_range)))
            tmp_mod = np.abs(mod_copeak_windows - tiled_mod)
            copeak_idxs = np.argmax(tmp_mod, axis=2)
            # shift towards signal away from copeak
            copeak_idxs_shifted = copeak_idxs + copeak_range[0] - 1 + attributes["TIMEDOMAIN.start_offset"]
        copeak_idxs_shifted = copeak_idxs_shifted.astype(int)
        # Add offsets to the start indices (broadcasting)
        signal_idxs = copeak_idxs_shifted[..., np.newaxis] + signal_window
        # Use advanced indexing to extract the windows
        mod_shifted = data_mod[np.arange(data_mod.shape[0])[:, np.newaxis, np.newaxis],  # Batch indices
                    np.arange(data_mod.shape[1])[np.newaxis, :, np.newaxis],  # Row indices
                    signal_idxs.astype(int)]  # Column indices (from expanded_idxs)
        return mod_shifted, signal_idxs

    def make_time(attributes):
        points_per_trace = attributes["TIMEDOMAIN.points_per_trace"]
        hint = attributes["TIMEDOMAIN.hint"]
        hoff = attributes["TIMEDOMAIN.hoff"]
        rep_rate = attributes["TIMEDOMAIN.rep_rate"]
        delay_rate = attributes["TIMEDOMAIN.delay_rate"]
        signal_length = int(attributes["TIMEDOMAIN.signal_length"])
        t_tmp = np.arange(0, points_per_trace) * hint + hoff
        t_raw = t_tmp / (rep_rate/delay_rate)
        data_t = t_raw[0:signal_length] - t_raw[0]
        dt = data_t[1]
        return data_t, dt

    def LPfilter(attributes, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter
        if "TIMEDOMAIN.LPfilter" in attributes:
            butter_order = attributes["TIMEDOMAIN.butter_order"]
            # Cutoff frequency for lowpass filter
            LP = attributes["TIMEDOMAIN.LPfilter"] * 1e9
            # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
            normalized_cutoff = LP / nyquist_freq  
            # Design a Butterworth lowpass filter
            b, a = butter(butter_order, normalized_cutoff, btype='low')
            for i in range(data_in.shape[0]):  
                for j in range(data_in.shape[1]):  
                    # Apply the filter using filtfilt (zero-phase filtering)
                    data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :])
        return data_in   

    def polyfit_removal(atttributes, data_in):
        print('Beginning polynomial fit removal...')
        # polynomial fit and removal
        degree = int(attributes["TIMEDOMAIN.polyfit_order"])
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

    def HPfilter(attributes, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter        
        if "TIMEDOMAIN.HPfilter" in attributes:
            butter_order = attributes["TIMEDOMAIN.butter_order"]
            HP = attributes["TIMEDOMAIN.HPfilter"] * 1e9
            normalized_cutoff = HP / nyquist_freq  
            b, a = butter(butter_order, normalized_cutoff, btype='high')
            for i in range(data_in.shape[0]):  
                for j in range(data_in.shape[1]):  
                    data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :]) 
        return data_in 

    def take_FFT(wrp, data_in, dt):
        print('Taking the FFT...')
        zp = int(attributes["TIMEDOMAIN.zp"]) # zero padding coefficient
        fmin_search = attributes["TIMEDOMAIN.fmin"] * 1e9
        fmax_search = attributes["TIMEDOMAIN.fmax"] * 1e9
        fmin_plot = attributes["TIMEDOMAIN.fmin_plot"] * 1e9
        fmax_plot = attributes["TIMEDOMAIN.fmax_plot"] * 1e9
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
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


def load_dat_GHOST(filepath):
    """Loads DAT files obtained with the GHOST software

    Parameters
    ----------
    filepath : stt
        The filepath to the GHOST file

    Returns
    -------
    dict
        The dictionary with the data and the attributes of the file stored respectively in the keys "Data" and "Attributes"
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
        A dictionary with the parameters to load the data, by default None. In the case where no parameters are provided, the function will return a list of the names of the parameters as string that have to be provided to load the data.

    Returns
    -------
    dict
        The dictionary with the time vector, the time resolved data and the attributes of the file stored respectively in the keys "Data", "Abscissa_dt" and "Attributes"
    """
    def scrape_m_file(filepath):
        meta_filebase = filepath[0:len(filepath)-4]
        meta_file = meta_filebase + ".m"
        # extract useful information from the relevant meta-file
        with open(meta_file, 'r') as file:
            content = file.read()
            meta_format = int(re.search(r'scp\.format\s*=\s*([\d\.]+);', content).group(1))
            if meta_format == 1:
                bytes_per_point, fmt = 1, np.int8
            elif meta_format == 2:
                bytes_per_point, fmt = 2, np.int16
            elif meta_format == 3:
                bytes_per_point, fmt = 4, np.float32
            n_traces = int(re.search(r'scp\.n_traces\s*=\s*([\d\.]+);', content).group(1))
            points_per_trace = int(re.search(r'scp\.points_per_trace\s*=\s*([\d\.]+);', content).group(1))
            vgain = float(re.search(r'scp\.vgain\s*=\s*\[\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)]\s*;', content).group(1))
            voff = float(re.search(r'scp\.voff\s*=\s*\[\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)]\s*;', content).group(1))
            hint = float(re.search(r'scp\.hint\s*=\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)\s*;', content).group(1))
            hoff = float(re.search(r'scp\.hoff\s*=\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)\s*;', content).group(1))
        return {"TIMEDOMAIN.bytes_per_point": bytes_per_point,
                "TIMEDOMAIN.fmt": fmt,
                "TIMEDOMAIN.n_traces": n_traces,
                "TIMEDOMAIN.points_per_trace": points_per_trace,
                "TIMEDOMAIN.vgain": vgain,
                "TIMEDOMAIN.voff": voff,
                "TIMEDOMAIN.hint": hint,
                "TIMEDOMAIN.hoff": hoff}

    def scrape_con_file(attributes):
        n_traces = attributes["TIMEDOMAIN.n_traces"]
        # Open the file and read its contents as a single string
        with open(attributes["TIMEDOMAIN.file_con"], 'r') as file:
            content = file.read()  # Get the entire content as a string
        # Normalize content to ensure all words are separated by newlines
        lines = '\n'.join(content.split())
        # Split lines into a list for easier processing
        lines_list = lines.splitlines()
        # Search for 'scan' and extract the next line's value
        start_val, end_val, step_val = {}, {}, {}
        scan_count = -1
        # Extract start/stop/step values for x and y scan parameters
        for i, line in enumerate(lines_list):
            if line == "scan":
                scan_count = scan_count + 1
                if i + 1 < len(lines_list):  # Ensure there's a subsequent line
                    start_val[scan_count] = float(lines_list[i + 1])
                    end_val[scan_count] = float(lines_list[i + 2])
                    step_val[scan_count] = float(lines_list[i + 3])

        # Sal, the above doesn't account for axis 1 existing, but axis 0 not. Just takes first 'scan' instance and assigns it to local var x, and if sencond to y
        # Organise start/stop/step values into variables and create x/y vectors (in microns)
        if start_val:
            tmp_x = np.arange(start_val[0], end_val[0], step_val[0])
            Nx_steps = len(tmp_x)
            x_um = np.linspace(0, Nx_steps-1, Nx_steps) * step_val[0] * 1e3 # mm to microns
            if len(start_val) > 1:
                tmp_y = np.arange(start_val[1], end_val[1], step_val[1])
                Ny_steps = len(tmp_y)
                y_um = np.linspace(0, Ny_steps-1, Ny_steps) * step_val[1] * 1e3 # mm to microns
            else:
                Ny_steps, y_um = 1, np.zeros((1, n_traces))
        else:
            Nx_steps, Ny_steps, x_um, y_um = 1, n_traces, np.zeros((1, n_traces)), np.linspace(0, n_traces-1, n_traces)

        if Nx_steps * Ny_steps == n_traces:
            print('Size of X and Y data matches number of traces, continuing...')
        else:
            print('Size of X and Y data do not match number of traces, reducing Y by 1 and trying again...')
            Ny_steps = Ny_steps - 1
            y_um = y_um[0:-1]
        return {
            "TIMEDOMAIN.Nx_steps": Nx_steps,
            "TIMEDOMAIN.Ny_steps": Ny_steps,
            "TIMEDOMAIN.x_um": x_um,
            "TIMEDOMAIN.y_um": y_um
        }

    def basic_process(attributes, filepath):
        n_traces = attributes["TIMEDOMAIN.n_traces"]
        points_per_trace = attributes["TIMEDOMAIN.points_per_trace"]
        bytes_per_point = attributes["TIMEDOMAIN.bytes_per_point"]
        fmt = attributes["TIMEDOMAIN.fmt"]
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
        vgain = attributes["TIMEDOMAIN.vgain"]
        voff = attributes["TIMEDOMAIN.voff"]
        ac_gain = attributes["TIMEDOMAIN.ac_gain"]
        # load and basic process for .dat file
        with open(filepath, 'r') as fi:
            # Create an array of traces
            traces = np.arange(1, n_traces + 1)
            # Initialize the data array
            data_tmp = np.zeros((len(traces), points_per_trace))
            # Loop through each trace and read data
            print('Loading time domain data...')
            for i, trace in enumerate(traces):
                # Move the file pointer to the correct position
                fi.seek((trace - 1) * points_per_trace * bytes_per_point)
                # Read the data for the current trace
                data_tmp[i, :] = np.fromfile(fi, dtype=fmt, count=points_per_trace)

            data_tmp2 = data_tmp.reshape(Nx_steps, Ny_steps, points_per_trace, order='F')
            # apply appropriate voltage gain and voltage offset from meta file
            data_ac = (data_tmp2 * vgain + voff)/ac_gain

        # reverse left-right time trace if needed
        if attributes["TIMEDOMAIN.bool_reverse_data"]:
            data_ac = data_ac[:, :, ::-1]

        return data_ac

    def load_dc(attributes, data_ac, filepath_dc):
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
        if os.path.isfile(filepath_dc):
            print('DC data found: ', filepath_dc)
            with open(filepath_dc, 'rb') as fi:
                # Read all data as float32
                tmp_dc = np.fromfile(fi, dtype=np.float32)        
            dc_samples = int(len(tmp_dc) / (Nx_steps * Ny_steps))
            data_dc = np.mean(tmp_dc.reshape(Nx_steps, Ny_steps, dc_samples, order='F'), 2)
            data_mod = data_ac / data_dc.reshape(Nx_steps, Ny_steps, 1, order='F')
        else:
            print('Could not find a valid DC data file, using AC data only')
            data_mod = data_ac
        return data_mod

    def find_copeaks(attributes, data_mod):
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
        print('Beginning signal processing...')     
        # find copeak and create signal of ROI
        signal_length = attributes["TIMEDOMAIN.signal_length"]
        signal_window = np.arange(signal_length)
        if attributes["TIMEDOMAIN.bool_forced_copeaks"]:
            print('Forcing copeak location...')
            copeak_val = attributes["TIMEDOMAIN.copeak_start"]
            copeak_idxs_shifted = copeak_val * np.ones((Nx_steps, Ny_steps))
        else:
            print('Finding copeak locations...')
            copeak_range = attributes["TIMEDOMAIN.copeak_start"] + np.arange(-attributes["TIMEDOMAIN.copeak_window"], attributes["TIMEDOMAIN.copeak_window"]+1, 1)
            copeak_range = copeak_range.astype(int)
            mod_copeak_windows = data_mod[:, :, copeak_range-1]
            first_vals = mod_copeak_windows[:, :, 0]
            tiled_mod = np.tile(first_vals[:, :, np.newaxis], (1, 1, len(copeak_range)))
            tmp_mod = np.abs(mod_copeak_windows - tiled_mod)
            copeak_idxs = np.argmax(tmp_mod, axis=2)
            # shift towards signal away from copeak
            copeak_idxs_shifted = copeak_idxs + copeak_range[0] - 1 + attributes["TIMEDOMAIN.start_offset"]
        copeak_idxs_shifted = copeak_idxs_shifted.astype(int)
        # Add offsets to the start indices (broadcasting)
        signal_idxs = copeak_idxs_shifted[..., np.newaxis] + signal_window
        # Use advanced indexing to extract the windows
        mod_shifted = data_mod[np.arange(data_mod.shape[0])[:, np.newaxis, np.newaxis],  # Batch indices
                    np.arange(data_mod.shape[1])[np.newaxis, :, np.newaxis],  # Row indices
                    signal_idxs.astype(int)]  # Column indices (from expanded_idxs)
        return mod_shifted, signal_idxs

    def make_time(attributes):
        points_per_trace = attributes["TIMEDOMAIN.points_per_trace"]
        hint = attributes["TIMEDOMAIN.hint"]
        hoff = attributes["TIMEDOMAIN.hoff"]
        rep_rate = attributes["TIMEDOMAIN.rep_rate"]
        delay_rate = attributes["TIMEDOMAIN.delay_rate"]
        signal_length = int(attributes["TIMEDOMAIN.signal_length"])
        t_tmp = np.arange(0, points_per_trace) * hint + hoff
        t_raw = t_tmp / (rep_rate/delay_rate)
        data_t = t_raw[0:signal_length] - t_raw[0]
        dt = data_t[1]
        return data_t, dt

    def LPfilter(attributes, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter
        if "TIMEDOMAIN.LPfilter" in attributes:
            butter_order = attributes["TIMEDOMAIN.butter_order"]
            # Cutoff frequency for lowpass filter
            LP = attributes["TIMEDOMAIN.LPfilter"] * 1e9
            # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
            normalized_cutoff = LP / nyquist_freq  
            # Design a Butterworth lowpass filter
            b, a = butter(butter_order, normalized_cutoff, btype='low')
            for i in range(data_in.shape[0]):  
                for j in range(data_in.shape[1]):  
                    # Apply the filter using filtfilt (zero-phase filtering)
                    data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :])
        return data_in   

    def polyfit_removal(atttributes, data_in):
        print('Beginning polynomial fit removal...')
        # polynomial fit and removal
        degree = int(attributes["TIMEDOMAIN.polyfit_order"])
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

    def HPfilter(attributes, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter        
        if "TIMEDOMAIN.HPfilter" in attributes:
            butter_order = attributes["TIMEDOMAIN.butter_order"]
            HP = attributes["TIMEDOMAIN.HPfilter"] * 1e9
            normalized_cutoff = HP / nyquist_freq  
            b, a = butter(butter_order, normalized_cutoff, btype='high')
            for i in range(data_in.shape[0]):  
                for j in range(data_in.shape[1]):  
                    data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :]) 
        return data_in 

    def take_FFT(attributes, data_in, dt):
        print('Taking the FFT...')
        zp = int(attributes["TIMEDOMAIN.zp"]) # zero padding coefficient
        fmin_search = attributes["TIMEDOMAIN.fmin"] * 1e9
        fmax_search = attributes["TIMEDOMAIN.fmax"] * 1e9
        fmin_plot = attributes["TIMEDOMAIN.fmin_plot"] * 1e9
        fmax_plot = attributes["TIMEDOMAIN.fmax_plot"] * 1e9
        Nx_steps = attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = attributes["TIMEDOMAIN.Ny_steps"]
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
        parameters_list = ["ac_gain", 
                           "bool_reverse_data", 
                           "bool_forced_copeaks", 
                           "butter_order",
                           "copeak_start", 
                           "copeak_window",
                           "delay_rate",
                           "file_con",  
                           "fmin",
                           "fmax", 
                           "fmin_plot",
                           "fmax_plot",
                           "LPfilter",
                           "HPfilter",
                           "polyfit_order",
                           "rep_rate",
                           "signal_length", 
                           "start_offset",
                           "zp"]
        
        raise LoadError_parameters(f"The following parameters have to be provided: {"; ".join(parameters_list)}", parameters_list)
    else:
        attributes = {}
        for k, v in parameters.items():
            if "bool_" in k or "file_" in k:
                attributes[f"TIMEDOMAIN.{k}"] = v
            else:
                attributes[f"TIMEDOMAIN.{k}"] = float(v)
    
    TD = TimeDomain(filepath = filepath, attributes = attributes)

    attributes['SPECTROMETER.Type'] = "TimeDomain"

    TD.scrape_m_file()

    attributes.update(TD.scrape_con_file())
    
    print("scrape_con_file")
    attributes.update(scrape_con_file(attributes))
    print("basic_process")
    data_ac = basic_process(attributes, filepath)  
    print("load_dc")
    filepath_dc = filepath[0:len(filepath)-10] + "a2d1_1f.d"
    data_mod = load_dc(attributes, data_ac, filepath_dc)
    print("find_copeaks")
    mod_shifted, signal_idxs = find_copeaks(attributes, data_mod)
    print("make_time")
    data_t, dt = make_time(attributes)
    print("LPfilter")
    mod_shifted = LPfilter(attributes, mod_shifted, dt)
    print("polyfit_removal")
    data_pro, polyfit = polyfit_removal(attributes, mod_shifted)
    print("HPfilter")
    data_pro = HPfilter(attributes, data_pro, dt)
    print("take_FFT")
    fft_out, freqs_out_GHz, fB_GHz = take_FFT(attributes, data_pro, dt)

    attributes['SPECTROMETER.Filtering_Module'] = "None"
    # attributes['Process_PSD': process]

    return {"Raw_data": {"Name": "Time measures", "Data": data_pro}, 
            "Abscissa_Time": {"Name": "Time axis", 
                              "Data": data_t,
                              "Unit": "s",
                              "Dim_start": -len(data_t.shape),
                              "Dim_end": 0},
            "PSD": {"Name": "PSD", "Data": fft_out},
            "Frequency": {"Name": "Frequency", "Data": freqs_out_GHz},
            "Attributes": attributes}

