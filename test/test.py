import sys
sys.path.insert(0, '/Users/pierrebouvet/Documents/Code/HDF5_BLS/HDF5_BLS')
from load_data import load_general, load_dat_file, load_hdf5_file, load_tiff_file
from wraper import Wraper
from treat import Treat

import numpy as np

# Test creating a new wraper from a GHOST file 
filepath = '/Users/pierrebouvet/Documents/Code/HDF5_BLS/test/test_data/GHOST_example.DAT'
wrp = Wraper()
wrp.open_data(filepath)

# Extracting the scna amplitude parameter and creating a frequency axis for the data
scan_amplitude = float(wrp.attributes["SPECTROMETER.Scan_Amplitude"])
wrp.create_abscissa_1D_min_max(0,-scan_amplitude/2, scan_amplitude/2,"Frequency (GHz)")

# Saving the wraper as a H5 file
wrp.save_as_hdf5("/Users/pierrebouvet/Documents/Code/HDF5_BLS/test/test.h5")

treat = Treat()

for i in range(100):
    opt, std = treat.fit_model(wrp.data["Abscissa_0"],
                    wrp.data["Raw_data"],
                    7.43,
                    1,
                    normalize = True, 
                    model = "Lorentz", 
                    fit_S_and_AS = True, 
                    window_peak_find = 1, 
                    window_peak_fit = 3, 
                    correct_elastic = True,
                    IR_wndw = [-0.5,0.5])

print(opt, std)

# import matplotlib.pyplot as plt

# plt.figure()
# plt.plot(wrp.data["Abscissa_0"], wrp.data["Raw_data"])
# plt.show()

# for e in treat.treat_steps: print(e)

