import h5py as h5

with h5.File('/Users/pierrebouvet/Desktop/file.h5', 'r') as f:
	data = f['Data/Data_6/Power Spectral Density'][:]
	frequency = f['Data/Data_6/Frequency'][:]


import os
import sys

current_dir = os.path.abspath(os.path.dirname(__file__))
relative_path_libs = os.path.join(current_dir, "..", "..", "HDF5_BLS")
absolute_path_libs = os.path.abspath(relative_path_libs)
sys.path.append(absolute_path_libs)

from HDF5_BLS.treat import fit_model_v0

popt, std, steps = fit_model_v0(n_frequency = frequency, 
								n_data = data, 
								center_frequency = 7.5, 
								linewidth = 0.8, 
								normalize = True, 
								c_model = "DHO", 
								fit_S_and_AS = True, 
								window_peak_find = 1, 
								window_peak_fit = 3, 
								correct_elastic = False, 
								IR_wndw = None, 
								n_freq_IR = None, 
								n_data_IR = None)
   
print(popt)

