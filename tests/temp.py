# import h5py as h5

# with h5.File('/Users/pierrebouvet/Desktop/file.h5', 'r') as f:
# 	data = f['Data/Data_6/Power Spectral Density'][:]
# 	frequency = f['Data/Data_6/Frequency'][:]


# import os
# import sys

# current_dir = os.path.abspath(os.path.dirname(__file__))
# relative_path_libs = os.path.join(current_dir, "..", "..", "HDF5_BLS")
# absolute_path_libs = os.path.abspath(relative_path_libs)
# sys.path.append(absolute_path_libs)

# from HDF5_BLS.treat import fit_model_v0

# popt, std, steps = fit_model_v0(n_frequency = frequency, 
# 								n_data = data, 
# 								center_frequency = 7.5, 
# 								linewidth = 0.8, 
# 								normalize = True, 
# 								c_model = "DHO", 
# 								fit_S_and_AS = True, 
# 								window_peak_find = 1, 
# 								window_peak_fit = 3, 
# 								correct_elastic = False, 
# 								IR_wndw = None, 
# 								n_freq_IR = None, 
# 								n_data_IR = None)
   
# print(popt)


import sys
import os

directory = os.path.dirname(os.path.realpath(__file__)).split("/")
sys.path.insert(0, "/".join(directory[:-1]))
directory = "/".join(directory)

from HDF5_BLS.wrapper import Wrapper
import matplotlib.pyplot as plt
import numpy as np

wrp = Wrapper(filepath=f"{directory}/test.h5")

test_dir = f"{directory}/test_data"
filepath = f"{test_dir}/TR_test_count1_scope0.dat"

attributes = {}

attributes["SPECTROMETER.type"] = 'time_domain' # required to trigger time_domain cascade in load_data.py

attributes["file_con"] = f"{test_dir}/TR_test.con"
attributes["rep_rate"] = 80e6
attributes["delay_rate"] = 10e3
attributes["ac_gain"] = 12.5 # spectra rig
attributes["copeak_start"] = 2036
attributes["MEASURE.forced_copeak"] = 'no'
attributes["start_offset"] = 55
attributes["signal_length"] = 2400
attributes["copeak_window"] = 100
attributes["bool_reverse_data"] = True
attributes["polyfit_order"] = 8
attributes["MEASURE.fmin"] = 0 # GHz
attributes["MEASURE.fmax"] = 25 # GHz
attributes["MEASURE.fmin_plot"] = 0 # GHz
attributes["MEASURE.fmax_plot"] = 20 # GHz
attributes["MEASURE.LPfilter"] = 8
attributes["MEASURE.HPfilter"] = 4.5
attributes["MEASURE.butter_order"] = 8 # butterworth filter order, higher = steeper
attributes["MEASURE.zp"] = 2**(16) # zero padding for FFT"""

wrp.import_file(filepath = filepath, 
                parent_group="TimeDomain Test", 
                creator = "TimeDomain", 
                parameters = attributes)



# wrp.open_data(filepath)

# ## Extracting the scna amplitude parameter and creating a frequency axis for the data
# #scan_amplitude = float(wrp.attributes["SPECTROMETER.Scan_Amplitude"])
# #wrp.create_abscissa_1D_min_max(0,-scan_amplitude/2, scan_amplitude/2,"Frequency (GHz)")

# # Saving the wrapper as a H5 file
# # wrp.save_as_hdf5("/Users/pierrebouvet/Documents/Code/HDF5_BLS/test/test.h5")

# treat = Treat()

# """opt, std = treat.fit_model(wrp.data["Abscissa_0"],
#                             wrp.data["Raw_data"],
#                             7.43,
#                             1,
#                             normalize = True, 
#                             model = "Lorentz", 
#                             fit_S_and_AS = True, 
#                             window_peak_find = 1, 
#                             window_peak_fit = 3, 
#                             correct_elastic = True,
#                             IR_wndw = [-0.5,0.5])"""
