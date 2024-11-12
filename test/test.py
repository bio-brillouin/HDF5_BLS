import sys

# setting path
sys.path.append('../src')
sys.path.append("/Users/pierrebouvet/Documents/Code/HDF5_BLS/src")

from Wraper import Wraper
from Treat import Treat
import matplotlib.pyplot as plt
from scipy import optimize, stats
import numpy as np
import os

def lorentzian(nu,A,B,nu0,Gamma):
    return B + A*(Gamma/2)**2/((nu-nu0)**2+(Gamma/2)**2)

filepath = '/Users/pierrebouvet/Documents/Code/HDF5_BLS/test/test_data/GHOST_example.DAT'

hdf5 = Wraper()
hdf5.open_data(filepath)

scan_amplitude = float(hdf5.attributes["SPECTROMETER.Scan_Amplitude"])
hdf5.define_abscissa(-scan_amplitude/2, scan_amplitude/2, hdf5.data.shape[-1])

treat = Treat()

opt, std = treat.fit_model(hdf5.abscissa,
                hdf5.data,
                7.43,
                1,
                normalize = True, 
                model = "Lorentz", 
                fit_S_and_AS = True, 
                window_peak_find = 1, 
                window_peak_fit = 3, 
                correct_elastic = False)


print(opt, std)
