import os
import numpy as np

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
    attributes['FILEPROP.Name'] = name.split("/")[-1]
    attributes['MEASURE.Sample'] = metadata["Sample"]
    attributes['MEASURE.Date'] = ""
    attributes['SPECTROMETER.Scanning_Strategy'] = "point_scanning"
    attributes['SPECTROMETER.Type'] = "TFP"
    attributes['SPECTROMETER.Illumination_Type'] = "CW"
    attributes['SPECTROMETER.Detector_Type'] = "Photon Counter"
    attributes['SPECTROMETER.Filtering_Module'] = "None"
    attributes['SPECTROMETER.Wavelength_(nm)'] = metadata["Wavelength"]
    attributes['SPECTROMETER.Scan_Amplitude_(GHz)'] = metadata["Scan amplitude"]
    spectral_resolution = float(float(metadata["Scan amplitude"])/data.shape[-1])
    attributes['SPECTROMETER.Spectral_Resolution_(GHz)'] = str(spectral_resolution)

    dic = {"Data": data, "Attributes": attributes}
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
        #     x_um = np.arange(attribute["TIMEDOMAIN.Nx_steps"]) * attribute["TIMEDOMAIN.dx_um"]
        #     y_um = np.arange(attribute["TIMEDOMAIN.Ny_steps"]) * attribute["TIMEDOMAIN.dy_um"]

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
        if "TIMEDOMAIN.forced_copeak" in attributes and attributes["MEASURE.forced_copeak"] == 'yes': # Forcing copeak location
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

    attributes["MEASURE.Process"] = ";".join(process)

    return {"Data": data_t, "Abscissa_Time": dt, "Attributes": attributes}

