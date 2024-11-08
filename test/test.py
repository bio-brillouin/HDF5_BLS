import sys

# setting path
sys.path.append('../HDF5_BLS')

from HDF5_BLS import HDF5_BLS
import matplotlib.pyplot as plt
from scipy import optimize, stats
import numpy as np
import os

def lorentzian(nu,A,B,nu0,Gamma):
    return B + A*(Gamma/2)**2/((nu-nu0)**2+(Gamma/2)**2)

filepath = 'test/test_data/GHOST_example.DAT'

hdf5 = HDF5_BLS.HDF5_BLS()
hdf5.open_data(filepath)

scan_amplitude = float(hdf5.attributes["SPECTROMETER.Scan_Amplitude"])
hdf5.define_abscissa(-scan_amplitude/2, scan_amplitude/2, hdf5.raw_data.shape[-1])

posS = -7.43
posAS = 7.43
width_find_max = 1

wndw_S = np.where((hdf5.abscissa>posS-width_find_max/2)&(hdf5.abscissa<posS+width_find_max/2))
pol = np.polyfit(hdf5.abscissa[wndw_S], hdf5.raw_data[wndw_S],2)
v_S = -pol[1]/(2*pol[0])
wndw_AS = np.where((hdf5.abscissa>posAS-width_find_max/2)&(hdf5.abscissa<posAS+width_find_max/2))
pol = np.polyfit(hdf5.abscissa[wndw_AS], hdf5.raw_data[wndw_AS],2)
v_AS = -pol[1]/(2*pol[0])

poptS,pcovS = optimize.curve_fit(lorentzian,hdf5.abscissa[wndw_S], hdf5.raw_data[wndw_S],[max(hdf5.raw_data[wndw_S]),0,v_S,0.8])
poptAS,pcovAS = optimize.curve_fit(lorentzian,hdf5.abscissa[wndw_AS], hdf5.raw_data[wndw_AS],[max(hdf5.raw_data[wndw_AS]),0,v_AS,0.8])

vS = np.sqrt(np.diag(pcovS))
vAS = np.sqrt(np.diag(pcovAS))

print("The fitted parameters for the Stokes peak are:")
print(f"    - Amplitude: {poptS[0]:.1f} ± {vS[0]:.3f}")
print(f"    - Offset: {poptS[1]:.1f} ± {vS[1]:.3f}")
print(f"    - Shift: {poptS[2]:.2f} ± {vS[2]:.3f} GHz")
print(f"    - Linewidth: {poptS[3]:.2f} ± {vS[3]:.3f} GHz")

print("The fitted parameters for the anti-Stokes peak are:")
print(f"    - Amplitude: {poptAS[0]:.1f} ± {vAS[0]:.3f}")
print(f"    - Offset: {poptAS[1]:.1f} ± {vAS[1]:.3f}")
print(f"    - Shift: {poptAS[2]:.2f} ± {vAS[2]:.3f} GHz")
print(f"    - Linewidth: {poptAS[3]:.2f} ± {vAS[3]:.3f} GHz")

hdf5.save_hdf5_as("test/test.hdf5")
