import sys

# setting path
sys.path.append('../HDF5_BLS')

from HDF5_BLS import HDF5_BLS
pip
import matplotlib.pyplot as plt
from scipy import optimize, stats
import numpy as np
import os

def lorentzian(nu,A,B,nu0,Gamma):
    return B + A*(Gamma/2)**2/((nu-nu0)**2+(Gamma/2)**2)

directory = '/Users/pierrebouvet/Documents/Databases/241105 - Water SNR TFP2 Felix/'
filepaths = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
filepaths.remove('.DS_Store')
counts = [int(filepath.split(" ")[1][:-4]) for filepath in filepaths]

sorted_pairs = sorted(zip(counts, filepaths))
counts, filepaths = zip(*sorted_pairs)

filepath = "/Users/pierrebouvet/Documents/Databases/241105 - Water SNR TFP2 Felix/count 3015.DAT"

# filepaths = filepaths[-2:]
# counts = counts[-2:]

posS = -7.43
posAS = 7.43
width_find_max = 1

A_S, B_S, nu0_S, Gamma_S = [],[],[],[]
A_AS, B_AS, nu0_AS, Gamma_AS = [],[],[],[]

for count, filepath in zip(counts, filepaths):
    filepath = directory+filepath
    hdf5 = HDF5_BLS.HDF5_BLS()
    hdf5.open_data(filepath)
    scan_amplitude = float(hdf5.attributes["SPECTROMETER.Scan_Amplitude"])
    hdf5.define_abscissa(-scan_amplitude/2, scan_amplitude/2, hdf5.raw_data.shape[-1])

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

    A_AS.append([poptAS[0],vAS[0]])
    A_S.append([poptS[0],vS[0]])
    B_AS.append([poptAS[1],vAS[1]])
    B_S.append([poptS[1],vS[1]])
    nu0_AS.append([poptAS[2],vAS[2]])
    nu0_S.append([poptS[2],vS[2]])
    Gamma_AS.append([poptAS[3],vAS[3]])
    Gamma_S.append([poptS[3],vS[3]])

A_AS = np.array(A_AS)
A_S = np.array(A_S)
B_AS = np.array(B_AS)
B_S = np.array(B_S)
nu0_AS = np.array(nu0_AS)
nu0_S = np.array(nu0_S)
Gamma_AS = np.array(Gamma_AS)
Gamma_S = np.array(Gamma_S)

plt.figure()
plt.subplot(221)
plt.title("Amplitude")
plt.errorbar(counts,A_AS[:,0],A_AS[:,1], label = "Anti-Stokes")
plt.errorbar(counts,A_S[:,0],A_S[:,1], label = "Stokes")
plt.xlabel("Counts")
plt.ylabel("Amplitude")
plt.subplot(222)
plt.title("Offset")
plt.errorbar(counts,B_AS[:,0],B_AS[:,1], label = "Anti-Stokes")
plt.errorbar(counts,B_S[:,0],B_S[:,1], label = "Stokes")
plt.xlabel("Counts")
plt.ylabel("Offset")
plt.subplot(223)
plt.title("Shift")
# plt.errorbar(counts,nu0_AS[:,0],nu0_AS[:,1], label = "Anti-Stokes")
# plt.errorbar(counts,-nu0_S[:,0],nu0_S[:,1], label = "Stokes")
plt.errorbar(counts,(nu0_AS[:,0]-nu0_S[:,0])/2,(nu0_AS[:,1]+nu0_S[:,1])/2, label = "Average")
plt.xlabel("Counts")
plt.ylabel("Shift (GHz)")
plt.subplot(224)
plt.title("Linewidth")
# plt.errorbar(counts,Gamma_AS[:,0],Gamma_AS[:,1], label = "Anti-Stokes")
# plt.errorbar(counts,Gamma_S[:,0],Gamma_S[:,1], label = "Stokes")
plt.errorbar(counts,(Gamma_AS[:,0]+Gamma_S[:,0])/2,(Gamma_AS[:,1]+Gamma_S[:,1])/2, label = "Average")
plt.xlabel("Counts")
plt.ylabel("Linewidth (GHz)")
plt.tight_layout()
plt.legend()

log_counts = np.log10(counts)
log_shift_error = np.log10((nu0_AS[:,1] + nu0_S[:,1])/2)
log_linewidth_error = np.log10((Gamma_AS[:,1] + Gamma_S[:,1])/2)

plt.figure()
slope, intercept, r, p, std_err = stats.linregress(log_counts, log_shift_error)
plt.subplot(121)
plt.title("Shift")
plt.plot(counts,(nu0_AS[:,1] + nu0_S[:,1])/2, label = f"Error")
plt.plot(counts,10**(intercept+slope*np.log10(counts)), label = f"$R^2 = {-r:.2f}")
plt.xscale('log')
plt.yscale('log')
plt.xlabel("Counts")
plt.ylabel("Error on Shift (GHz)")
plt.legend()

slope, intercept, r, p, std_err = stats.linregress(log_counts, log_linewidth_error)
plt.subplot(122)
plt.title("Linewidth")
plt.plot(counts,1000*(Gamma_AS[:,1] + Gamma_S[:,1])/2, label = f"Error")
plt.plot(counts,1000*10**(intercept+slope*np.log10(counts)), label = f"$R^2 = {-r:.2f}")
plt.xscale('log')
plt.yscale('log')
plt.xlabel("Counts")
plt.ylabel("Error on Linewidth (MHz)")
plt.legend()
plt.tight_layout()

plt.show()
