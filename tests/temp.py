import numpy as np
import os
from scipy.signal import butter, filtfilt
from numpy.polynomial import Chebyshev
from matplotlib import pyplot as plt

def scrape_meta_file(filepath, process):
    attributes = {}
    # Read meta file
    with open(filepath, 'r') as file: content = file.read().splitlines()
    
    # Store informations in the attributes dictionnary
    for e in content:
        if e[0] == "%": continue 
        elif e[:4] == "scp.": 
            e = e[4:].split("=")
            for t in ("[","]",";","{","}","'"): e[1] = e[1].replace(t,"")
            attributes["TIMEDOMAIN."+e[0].strip()] = e[1].strip()
        else: 
            e = e.replace(" ","_")
            e = e.split("=")
            attributes["TIMEDOMAIN."+e[0].strip()] = e[1].strip()

    # Add bytes per point and format from extracted informations
    temp = [np.int8, np.int16, np.float32]
    attributes["TIMEDOMAIN.bytes_per_point"] =  2**(int(attributes["TIMEDOMAIN.format"])-1)
    attributes["TIMEDOMAIN.fmt"] = temp[int(attributes["TIMEDOMAIN.format"])-1]

    # Adds the process to the process list
    process.append(f"Opened meta file {filepath}, extracted parameters and created attributes dictionary.")

    return attributes, process

def scrape_con_file(filepath, attributes, process):
    n_traces = attributes["TIMEDOMAIN.n_traces"] 

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

    attributes["TIMEDOMAIN.Nx_steps"] = int(Nx_steps)
    attributes["TIMEDOMAIN.Ny_steps"] = int(Ny_steps)
    attributes["TIMEDOMAIN.dx_um"] = dx_um
    attributes["TIMEDOMAIN.dy_um"] = dy_um

    # Updated the process list
    process.append(f"Opened con file {filepath}, extracted scan parameters {temp_process} and updated attributes dictionary.")

    return process

def basic_process(filepath, attributes, process):
    n_traces = int(attributes["TIMEDOMAIN.n_traces"])
    points_per_trace = int(attributes["TIMEDOMAIN.points_per_trace"])
    bytes_per_point = int(attributes["TIMEDOMAIN.bytes_per_point"])
    fmt = attributes["TIMEDOMAIN.fmt"]
    Nx_steps = int(attributes["TIMEDOMAIN.Nx_steps"])
    Ny_steps = int(attributes["TIMEDOMAIN.Ny_steps"])
    vgain = float(attributes["TIMEDOMAIN.vgain"])
    voff = float(attributes["TIMEDOMAIN.voff"])
    ac_gain = float(attributes["TIMEDOMAIN.ac_gain"]) # PROBLEM HERE


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
    if attributes["TIMEDOMAIN.reverse_data"] == 'yes':
        data_ac = data_ac[:, :, ::-1]

    # Update the process list
    process.append(f"Opened data file {filepath}, extracted data based on attributes dictionary.")

    return data_ac, process

def load_dc(attributes, data_ac, filepath_dc, process):
    Nx_steps = int(attributes["TIMEDOMAIN.Nx_steps"])
    Ny_steps = int(attributes["TIMEDOMAIN.Ny_steps"])
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
    signal_length = attributes["TIMEDOMAIN.signal_length"] # PROBLEM HERE
    signal_window = np.arange(signal_length)
    if "TIMEDOMAIN.forced_copeak" in attributes and attributes["TIMEDOMAIN.forced_copeak"] == 'yes': # Forcing copeak location
        Nx_steps = int(attributes["TIMEDOMAIN.Nx_steps"])
        Ny_steps = int(attributes["TIMEDOMAIN.Ny_steps"])  
        copeak_val = attributes["TIMEDOMAIN.copeak_start"]
        copeak_idxs_shifted = copeak_val * np.ones((Nx_steps, Ny_steps))
        temp_process = "forcing copeak"
    else:# Finding copeak locations
        copeak_range = attributes["TIMEDOMAIN.copeak_start"] + np.arange(-attributes["TIMEDOMAIN.copeak_window"], attributes["TIMEDOMAIN.copeak_window"]+1, 1).astype(int) # PROBLEM HERE
        mod_copeak_windows = data_mod[:, :, copeak_range-1]
        first_vals = mod_copeak_windows[:, :, 0]
        tiled_mod = np.tile(first_vals[:, :, np.newaxis], (1, 1, len(copeak_range)))
        copeak_idxs = np.argmax(np.abs(mod_copeak_windows - tiled_mod), axis=2)
        # shift towards signal away from copeak
        copeak_idxs_shifted = copeak_idxs + copeak_range[0] - 1 + attributes["TIMEDOMAIN.start_offset"]
        temp_process = "without forcing copeak"
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
    points_per_trace = int(attributes["TIMEDOMAIN.points_per_trace"])
    hint = float(attributes["TIMEDOMAIN.hint"])
    hoff = float(attributes["TIMEDOMAIN.hoff"])
    rep_rate = attributes["TIMEDOMAIN.rep_rate"] # PROBLEM HERE
    delay_rate = attributes["TIMEDOMAIN.delay_rate"] # PROBLEM HERE
    signal_length = attributes["TIMEDOMAIN.signal_length"]
    t_tmp = np.arange(0, points_per_trace) * hint + hoff
    t_raw = t_tmp / (rep_rate/delay_rate)
    data_t = t_raw[0:signal_length] - t_raw[0]
    dt = data_t[1]

    process.append(f"Created time vector based on hint, hoff, rep_rate and delay_rate.")

    return data_t, dt, process


filepath = "/Users/pierrebouvet/Downloads/HDF5_BLS-time_domain_development/test/test_data/testdata_2D_tl_apt_stage0_tl_apt_stage0_scope0.dat"
filepath_con = "/Users/pierrebouvet/Downloads/HDF5_BLS-time_domain_development/test/test_data/testdata_2D.con"

file_base, ext = os.path.splitext(filepath)
process = []

# Initializes the attributes dictionary
attributes, process = scrape_meta_file(file_base + ".m", process)


attributes["TIMEDOMAIN.ac_gain"] = 0.5 # Added to avoid error
attributes["TIMEDOMAIN.reverse_data"] = 'yes' # Added to avoid error
attributes["TIMEDOMAIN.signal_length"] = 10 # Added to avoid error
attributes["TIMEDOMAIN.copeak_start"] = 1 # Added to avoid error
attributes["TIMEDOMAIN.copeak_window"] = 100 # Added to avoid error
attributes["TIMEDOMAIN.start_offset"] = 10 # Added to avoid error
attributes["TIMEDOMAIN.rep_rate"] = 1 # Added to avoid error
attributes["TIMEDOMAIN.delay_rate"] = 1 # Added to avoid error

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





def LPfilter(attributes, data_in, dt, process):
    # Low pass filter
    if "TIMEDOMAIN.LPfilter" in attributes: # Never in attributes
        # Get the cutoff frequency by Nyquist frequency (fs / 2) from the time vector
        nyquist_freq = 1 / (2 * dt)
        butter_order = attributes["TIMEDOMAIN.butter_order"] # Never in attributes
        # Cutoff frequency for lowpass filter
        LP = attributes["TIMEDOMAIN.LPfilter"] * 1e9 
        # Normalize the cutoff frequency by Nyquist frequency
        normalized_cutoff = LP / nyquist_freq  
        # Design a Butterworth lowpass filter
        b, a = butter(butter_order, normalized_cutoff, btype='low')
        for i in range(data_in.shape[0]):  
            for j in range(data_in.shape[1]):  
                # Apply the filter using filtfilt (zero-phase filtering)
                data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :])
        process.append(f"Low pass filter applied with cutoff frequency {LP} Hz")
    return data_in, process

def polyfit_removal(attributes, data_in, process):
    # polynomial fit and removal
    degree = attributes["TIMEDOMAIN.polyfit_order"] # PROBLEM HERE
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

    process.append(f"Subtracted the polynomial of degree {degree} from the data.")

    return data_pro, mod_poly, process

def HPfilter(attributes, data_in, dt, process):
    # Sampling frequency (Hz) from the time vector
    fs = 1 / dt
    # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
    nyquist_freq = fs / 2
    # Low pass filter        
    if "TIMEDOMAIN.HPfilter" in attributes:
        butter_order = attributes["TIMEDOMAIN.butter_order"] # PROBLEM HERE
        HP = attributes["TIMEDOMAIN.HPfilter"] * 1e9
        normalized_cutoff = HP / nyquist_freq  
        b, a = butter(butter_order, normalized_cutoff, btype='high')
        for i in range(data_in.shape[0]):  
            for j in range(data_in.shape[1]):  
                data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :]) 
        process.append(f"Applied a high pass Butterworth filter of order {butter_order} with cutoff frequency {HP} Hz.")

    return data_in, process

def take_FFT(attributes, data_in, dt):
    zp = attributes["TIMEDOMAIN.zp"] # PROBLEM HERE
    fmin_search = attributes["TIMEDOMAIN.fmin"] * 1e9 # PROBLEM HERE
    fmax_search = attributes["TIMEDOMAIN.fmax"] * 1e9 # PROBLEM HERE
    fmin_plot = attributes["TIMEDOMAIN.fmin_plot"] * 1e9 # PROBLEM HERE
    fmax_plot = attributes["TIMEDOMAIN.fmax_plot"] * 1e9 # PROBLEM HERE
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

def interactive_plot(self, wrp, ysignal0, sigcut_idxs, sig_poly, xsignal, ysignal, xfreq, yfreq, fmap):
    """
    Creates an interactive plot with a 3x2 layout:
    - Column 1: 2D array mapping (fmap) occupies all three rows.
    - Column 2:
        - Row 1: Current raw time-signal and polyfit (ysignal0, sig_poly).
        - Row 2: Current processed modulation depth (xsignal, ysignal).
        - Row 3: Current processed frequency spectrum (xfreq, yfreq).
    Updates plots in column 2 based on user clicks on the image in column 1.
    """
    # Function to set scientific notation for y-axis
    def set_scientific_yaxis(ax):
        from matplotlib.ticker import ScalarFormatter
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((-1, 1))  # Force scientific notation for all ranges
        ax.yaxis.set_major_formatter(formatter)
        ax.ticklabel_format(axis='y', style='scientific')

    x_inplot_cols = wrp.attributes["TIMEDOMAIN.y_um"] # x and y reversed between array and space
    y_inplot_rows = wrp.attributes["TIMEDOMAIN.x_um"] # x and y reversed between array and space

    # Create the figure and axes
    fig = plt.figure(figsize=(12, 6))
    gs = fig.add_gridspec(3, 2, width_ratios=[3, 3], height_ratios=[1, 1, 1])

    # Axes for fmap image spanning all rows in column 1
    ax_image = fig.add_subplot(gs[:, 0])

    # Axes for the plots in column 2
    ax_raw = fig.add_subplot(gs[0, 1])
    ax_time = fig.add_subplot(gs[1, 1])
    ax_freq = fig.add_subplot(gs[2, 1])

    set_scientific_yaxis(ax_raw)
    set_scientific_yaxis(ax_time)
    set_scientific_yaxis(ax_freq)

    # Determine x/y extents/limits for imshow
    if np.all(x_inplot_cols == x_inplot_cols[0]):  # Check if all values in xmap are the same
        x_extent = [0, len(x_inplot_cols) * 5]  # Use the index range for x-axis
        ax_image.set_ylabel("Count")  # Update label to reflect index-based axis
        ax_image.tick_params(axis='x', which='both', left=False, right=False, labelleft=False)
    else:
        x_extent = [x_inplot_cols.min(), x_inplot_cols.max()]

    if np.all(y_inplot_rows == y_inplot_rows[0]):  # Check if all values in ymap are the same
        y_extent = [0, len(y_inplot_rows) * 5]  # Use the index range for y-axis
        ax_image.set_xlabel("Count")  # Update label to reflect index-based axis
        ax_image.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
    else:
        y_extent = [y_inplot_rows.min(), y_inplot_rows.max()]

    # Plot the 2D array with updated extent
    im = ax_image.imshow(fmap, cmap='jet', aspect='equal', origin='lower',
                        extent=[x_extent[0], x_extent[1], y_extent[0], y_extent[1]])

    # Update axis labels for special cases
    if np.all(x_inplot_cols[0] != x_inplot_cols[-1]) and np.all(y_inplot_rows[0] != y_inplot_rows[-1]):
        ax_image.set_xlabel("Axis 0 ($\mu$m)")
        ax_image.set_ylabel("Axis 1 ($\mu$m)")

    # Plot the 2D array (entire first column)
    im = ax_image.imshow(fmap, cmap='jet', aspect='equal', origin='lower',
                        extent=[x_extent[0], x_extent[1], y_extent[0], y_extent[1]])
    ax_image.set_title("Brillouin Frequency Map (GHz) (click me!)")
    fig.colorbar(im, ax=ax_image, orientation='vertical', shrink=0.85)

    # Initial plot for the raw time signal (row 1, column 2)
    raw_line1, = ax_raw.plot(ysignal0[0, 0, :], label="Extra Signal")
    raw_line2, = ax_raw.plot(sigcut_idxs[0, 0, :], sig_poly[0, 0, :])
    ax_raw.set_title(f"Raw data and poly fit (i=0, j=0)")
    ax_raw.set_xlabel("index value")
    ax_raw.set_ylabel("Amplitude")

    # Initial plot for time signal (row 2, column 2)
    time_line, = ax_time.plot(xsignal, ysignal[0, 0, :], label="Time Signal")
    ax_time.set_title("Time signal")
    ax_time.set_xlabel("Time (ns)")
    ax_time.set_ylabel("Amplitude")

    # Initial plot for frequency signal (row 3, column 2)
    freq_line, = ax_freq.plot(xfreq, yfreq[0, 0, :], label="Frequency Spectrum")
    ax_freq.set_title(f"Frequency Spectrum | fB = {fmap[0, 0]:.2f} GHz")
    ax_freq.set_xlabel("Frequency (GHz)")
    ax_freq.set_ylabel("Amplitude")

    # Add a cross marker for the clicked pixel
    cross_marker, = ax_image.plot([], [], 'k+', markersize=10, label='Selected Pixel')

    # Click event handler
    def onclick(event):
        if event.inaxes == ax_image:  # Check if click is in the image axis
            j = np.abs(x_inplot_cols - event.xdata).argmin()  # Find index in xmap closest to clicked x
            i = np.abs(y_inplot_rows - event.ydata).argmin()  # Find index in ymap closest to clicked y            
            print(f"Clicked on pixel: (i={i}, j={j})")

            # Update cross marker position
            cross_marker.set_data([x_inplot_cols[j]], [y_inplot_rows[i]])            
            
            # Update mod-depth signal
            time_line.set_ydata(ysignal[i, j, :])
            ax_time.set_ylim(ysignal[i, j, :].min(), ysignal[i, j, :].max())

            # Update frequency spectrum
            freq_line.set_ydata(yfreq[i, j, :])
            ax_freq.set_ylim(yfreq[i, j, :].min(), yfreq[i, j, :].max())
            ax_freq.set_title(f"Frequency Spectrum | fB = {fmap[i, j]:.2f} GHz")

            # Update the ac signal
            raw_line1.set_ydata(ysignal0[i, j, :])
            raw_line2.set_xdata(sigcut_idxs[i, j, :])
            raw_line2.set_ydata(sig_poly[i, j, :])
            ax_raw.set_ylim(ysignal0[i, j, :].min(), ysignal0[i, j, :].max())
            ax_raw.set_title(f"Raw data and poly fit (i={i}, j={j})")

            # Redraw the figure
            fig.canvas.draw()

    # Connect the click event to the handler
    fig.canvas.mpl_connect('button_press_event', onclick)

    # Adjust layout and show the plot
    plt.tight_layout()
    plt.show()


attributes["TIMEDOMAIN.polyfit_order"] = 3 # Added to avoid error
attributes["TIMEDOMAIN.butter_order"] = 3 # Added to avoid error
attributes["TIMEDOMAIN.zp"] = 100 # Added to avoid error
attributes["TIMEDOMAIN.fmin"] = 0# Added to avoid error
attributes["TIMEDOMAIN.fmax"] = 10e9 # Added to avoid error
attributes["TIMEDOMAIN.fmin_plot"] = 0 # Added to avoid error
attributes["TIMEDOMAIN.fmax_plot"] = 10e9 # Added to avoid error

# Low pass filter the signal
# mod_shifted, process = LPfilter(attributes, mod_shifted, dt, process)

# # Polynomial fit and removal
# data_pro, polyfit, process = polyfit_removal(attributes, mod_shifted, process)

# # High pass filter the signal
# data_pro, process = HPfilter(attributes, data_pro, dt, process)

# # # Take FFT of the time signal
# fft_out, freqs_out_GHz, fB_GHz = take_FFT(attributes, data_pro, dt)

# plt.imshow(fB_GHz)
# plt.show()


