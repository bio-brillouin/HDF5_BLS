import numpy as np
import os
import re
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import ScalarFormatter
from scipy.signal import butter, filtfilt
from numpy.polynomial import Chebyshev

class TimeDomainError(Exception):
    def __init__(self, msg) -> None:
        self.message = msg
        super().__init__(self.message)

class TimeDomain:
    """
    This object is used to process time domain data and extract/store relevant attributes 
    to the outer Wrapper object.
    """    
    # As new timedomain experimental parameters are scraped add them to wrp.attributes
    def update_wrapper(self, wrp, results):
        # Update the wrp.attributes dictionary with multiple values
        wrp.attributes.update(results)

    # Scrape the .m file which stores relevant oscilloscope data
    def scrape_m_file(self, filepath):
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
            else:
                print("scp.format not found in the file.")
            n_traces = int(re.search(r'scp\.n_traces\s*=\s*([\d\.]+);', content).group(1))
            points_per_trace = int(re.search(r'scp\.points_per_trace\s*=\s*([\d\.]+);', content).group(1))
            vgain = float(re.search(r'scp\.vgain\s*=\s*\[\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)]\s*;', content).group(1))
            voff = float(re.search(r'scp\.voff\s*=\s*\[\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)]\s*;', content).group(1))
            hint = float(re.search(r'scp\.hint\s*=\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)\s*;', content).group(1))
            hoff = float(re.search(r'scp\.hoff\s*=\s*([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)\s*;', content).group(1))
        return {
            "TIMEDOMAIN.bytes_per_point": bytes_per_point,
            "TIMEDOMAIN.fmt": fmt,
            "TIMEDOMAIN.n_traces": n_traces,
            "TIMEDOMAIN.points_per_trace": points_per_trace,
            "TIMEDOMAIN.vgain": vgain,
            "TIMEDOMAIN.voff": voff,
            "TIMEDOMAIN.hint": hint,
            "TIMEDOMAIN.hoff": hoff
        }

    # Scrape the .con file which contains the relevant x/y scan parameters
    def scrape_con_file(self, wrp):
        n_traces = wrp.attributes["TIMEDOMAIN.n_traces"]
        # Open the file and read its contents as a single string
        with open(wrp.attributes["TIMEDOMAIN.confile"], 'r') as file:
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

    # Loads .dat binary file and applies oscilloscope parameters to create raw AC signal
    def basic_process(self, wrp, filepath):
        n_traces = wrp.attributes["TIMEDOMAIN.n_traces"]
        points_per_trace = wrp.attributes["TIMEDOMAIN.points_per_trace"]
        bytes_per_point = wrp.attributes["TIMEDOMAIN.bytes_per_point"]
        fmt = wrp.attributes["TIMEDOMAIN.fmt"]
        Nx_steps = wrp.attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = wrp.attributes["TIMEDOMAIN.Ny_steps"]
        vgain = wrp.attributes["TIMEDOMAIN.vgain"]
        voff = wrp.attributes["TIMEDOMAIN.voff"]
        ac_gain = wrp.attributes["TIMEDOMAIN.ac_gain"]
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
        if wrp.attributes["TIMEDOMAIN.reverse_data"] == 'yes':
            data_ac = data_ac[:, :, ::-1]

        return data_ac
    
    # Load DC data from .d and reshape according to x/y/count sizes
    def load_dc(self, wrp, data_ac, filepath_dc):
        Nx_steps = wrp.attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = wrp.attributes["TIMEDOMAIN.Ny_steps"]
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
    
    # Locate the coincidence peaks from the raw time signal, cut AC signal to start from here
    def find_copeaks(self, wrp, data_mod):
        Nx_steps = wrp.attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = wrp.attributes["TIMEDOMAIN.Ny_steps"]
        print('Beginning signal processing...')     
        # find copeak and create signal of ROI
        signal_length = wrp.attributes["TIMEDOMAIN.signal_length"]
        signal_window = np.arange(signal_length)
        if "TIMEDOMAIN.forced_copeak" in wrp.attributes and wrp.attributes["TIMEDOMAIN.forced_copeak"] == 'yes':
            print('Forcing copeak location...')
            copeak_val = wrp.attributes["TIMEDOMAIN.copeak_start"]
            copeak_idxs_shifted = copeak_val * np.ones((Nx_steps, Ny_steps))
        else:
            print('Finding copeak locations...')
            copeak_range = wrp.attributes["TIMEDOMAIN.copeak_start"] + np.arange(-wrp.attributes["TIMEDOMAIN.copeak_window"], wrp.attributes["TIMEDOMAIN.copeak_window"]+1, 1)
            copeak_range = copeak_range.astype(int)
            mod_copeak_windows = data_mod[:, :, copeak_range-1]
            first_vals = mod_copeak_windows[:, :, 0]
            tiled_mod = np.tile(first_vals[:, :, np.newaxis], (1, 1, len(copeak_range)))
            tmp_mod = np.abs(mod_copeak_windows - tiled_mod)
            copeak_idxs = np.argmax(tmp_mod, axis=2)
            # shift towards signal away from copeak
            copeak_idxs_shifted = copeak_idxs + copeak_range[0] - 1 + wrp.attributes["TIMEDOMAIN.start_offset"]
        copeak_idxs_shifted = copeak_idxs_shifted.astype(int)
        # Add offsets to the start indices (broadcasting)
        signal_idxs = copeak_idxs_shifted[..., np.newaxis] + signal_window
        # Use advanced indexing to extract the windows
        mod_shifted = data_mod[np.arange(data_mod.shape[0])[:, np.newaxis, np.newaxis],  # Batch indices
                    np.arange(data_mod.shape[1])[np.newaxis, :, np.newaxis],  # Row indices
                    signal_idxs]  # Column indices (from expanded_idxs)
        return mod_shifted, signal_idxs
    
    # Use oscilloscope parameters and cropped signal window to create the time vector
    def make_time(self, wrp):
        points_per_trace = wrp.attributes["TIMEDOMAIN.points_per_trace"]
        hint = wrp.attributes["TIMEDOMAIN.hint"]
        hoff = wrp.attributes["TIMEDOMAIN.hoff"]
        rep_rate = wrp.attributes["TIMEDOMAIN.rep_rate"]
        delay_rate = wrp.attributes["TIMEDOMAIN.delay_rate"]
        signal_length = wrp.attributes["TIMEDOMAIN.signal_length"]
        t_tmp = np.arange(0, points_per_trace) * hint + hoff
        t_raw = t_tmp / (rep_rate/delay_rate)
        data_t = t_raw[0:signal_length] - t_raw[0]
        dt = data_t[1]
        return data_t, dt
    
    # Butterworth-based low pass filter
    def LPfilter(self, wrp, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter
        if "TIMEDOMAIN.LPfilter" in wrp.attributes:
            butter_order = wrp.attributes["TIMEDOMAIN.butter_order"]
            # Cutoff frequency for lowpass filter
            LP = wrp.attributes["TIMEDOMAIN.LPfilter"] * 1e9
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
    def HPfilter(self, wrp, data_in, dt):
        # Sampling frequency (Hz) from the time vector
        fs = 1 / dt
        # Normalize the cutoff frequency by Nyquist frequency (fs / 2)
        nyquist_freq = fs / 2
        # Low pass filter        
        if "TIMEDOMAIN.HPfilter" in wrp.attributes:
            butter_order = wrp.attributes["TIMEDOMAIN.butter_order"]
            HP = wrp.attributes["TIMEDOMAIN.HPfilter"] * 1e9
            normalized_cutoff = HP / nyquist_freq  
            b, a = butter(butter_order, normalized_cutoff, btype='high')
            for i in range(data_in.shape[0]):  
                for j in range(data_in.shape[1]):  
                    data_in[i, j, :] = filtfilt(b, a, data_in[i, j, :]) 
        return data_in        
    
    # To remove the thermal background envelope, fit and subtract a polynomial (Chebyshev model currently)
    def polyfit_removal(self, wrp, data_in):
        print('Beginning polynomial fit removal...')
        # polynomial fit and removal
        degree = wrp.attributes["TIMEDOMAIN.polyfit_order"] 
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
    def take_FFT(self, wrp, data_in, dt):
        print('Taking the FFT...')
        zp = wrp.attributes["TIMEDOMAIN.zp"] # zero padding coefficient
        fmin_search = wrp.attributes["TIMEDOMAIN.fmin"] * 1e9
        fmax_search = wrp.attributes["TIMEDOMAIN.fmax"] * 1e9
        fmin_plot = wrp.attributes["TIMEDOMAIN.fmin_plot"] * 1e9
        fmax_plot = wrp.attributes["TIMEDOMAIN.fmax_plot"] * 1e9
        Nx_steps = wrp.attributes["TIMEDOMAIN.Nx_steps"]
        Ny_steps = wrp.attributes["TIMEDOMAIN.Ny_steps"]
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

    # Interactive plot showing the raw time signal, processed time signal, freq signal, and clickable Brill map
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