import sys
import os
current_dir = os.getcwd()
relative_path_libs = os.path.join(current_dir, "..", "HDF5_BLS")
absolute_path_libs = os.path.abspath(relative_path_libs)
sys.path.insert(0, absolute_path_libs)
from load_data import load_general, load_dat_file, load_tiff_file
from wrapper import Wrapper
from treat import Treat
import matplotlib.pyplot as plt
import numpy as np

test_dir = os.path.join(current_dir, "test_data")
wrp = Wrapper()
wrp.attributes["SPECTROMETER.type"] = 'time_domain' # required to trigger time_domain cascade in load_data.py

filepath = os.path.join(test_dir, "testdata_2D_tl_apt_stage0_tl_apt_stage0_scope0.dat")
wrp.attributes["TIMEDOMAIN.confile"] = os.path.join(test_dir, "testdata_2D.con")
wrp.attributes["TIMEDOMAIN.rep_rate"] = 80e6
wrp.attributes["TIMEDOMAIN.delay_rate"] = 5e3
wrp.attributes["TIMEDOMAIN.ac_gain"] = 12.5 # spectra
wrp.attributes["TIMEDOMAIN.copeak_start"] = 950
wrp.attributes["TIMEDOMAIN.forced_copeak"] = 'no'
wrp.attributes["TIMEDOMAIN.start_offset"] = 200
wrp.attributes["TIMEDOMAIN.signal_length"] = 3000
wrp.attributes["TIMEDOMAIN.copeak_window"] = 500
wrp.attributes["TIMEDOMAIN.reverse_data"] = 'no'
wrp.attributes["TIMEDOMAIN.polyfit_order"] = 10#15
wrp.attributes["TIMEDOMAIN.fmin"] = 9 # GHz
wrp.attributes["TIMEDOMAIN.fmax"] = 11 # GHz
wrp.attributes["TIMEDOMAIN.fmin_plot"] = 0 # GHz
wrp.attributes["TIMEDOMAIN.fmax_plot"] = 20 # GHz
wrp.attributes["TIMEDOMAIN.LPfilter"] = 20
wrp.attributes["TIMEDOMAIN.HPfilter"] = 7
wrp.attributes["TIMEDOMAIN.butter_order"] = 8 # butterworth filter order, higher = steeper
wrp.attributes["TIMEDOMAIN.zp"] = 2**(18) # zero padding for FFT"""

wrp.open_data(filepath)

## Extracting the scna amplitude parameter and creating a frequency axis for the data
#scan_amplitude = float(wrp.attributes["SPECTROMETER.Scan_Amplitude"])
#wrp.create_abscissa_1D_min_max(0,-scan_amplitude/2, scan_amplitude/2,"Frequency (GHz)")

# Saving the wrapper as a H5 file
# wrp.save_as_hdf5("/Users/pierrebouvet/Documents/Code/HDF5_BLS/test/test.h5")

treat = Treat()

"""opt, std = treat.fit_model(wrp.data["Abscissa_0"],
                            wrp.data["Raw_data"],
                            7.43,
                            1,
                            normalize = True, 
                            model = "Lorentz", 
                            fit_S_and_AS = True, 
                            window_peak_find = 1, 
                            window_peak_fit = 3, 
                            correct_elastic = True,
                            IR_wndw = [-0.5,0.5])"""