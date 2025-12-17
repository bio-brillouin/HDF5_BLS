# The HDF5_BLS_treat package

This package is a part of the [HDF5_BLS](https://github.com/bio-brillouin/HDF5_BLS) project. It's purpose is to unify the conversion of arbitrary Brillouin spectrometers data into a power spectrum.

## Installation

To install the package, you can use pip:

```bash
pip install HDF5_BLS_analyse
```

To install the package from source for local development, please refer to the [documentation](https://hdf5-bls.readthedocs.io/en/latest/).

## Documentation

You can access the documentation of the project at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) or on the dedicated ReadTheDocs page at [this link](https://hdf5-bls.readthedocs.io/en/latest/).

## Example of usage

```python
from HDF5_BLS_analyse import Analyse_VIPA
import numpy as np
import matplotlib.pyplot as plt

# Creating a mock spectrum and a mock pixel axis
def DHO(nu, nu0, gamma, a, b):
    return b + a * (gamma*nu0)**2/((nu**2-nu0**2)**2+(gamma*nu)**2)

nu = (np.linspace(-1,1,1024) + 2)**2 * 90/8 - 50 # The frequency axis is a simple quadratic polynomial here
pixel = np.arange(len(nu))
mock_spectrum = DHO(nu, nu0=-35, gamma=0.5, a=1, b=0) + DHO(nu, nu0=-25, gamma=0.5, a=1, b=0) + DHO(nu, nu0=-5, gamma=0.5, a=1, b=0) + DHO(nu, nu0=5, gamma=0.5, a=1, b=0) + DHO(nu, nu0=25, gamma=0.5, a=1, b=0) + DHO(nu, nu0=35, gamma=0.5, a=1, b=0) + np.random.normal(0, 0.05, size=1024)

# Initialising the Analyse_VIPA object on the mock spectrum
analyser = Analyse_VIPA(x = np.arange(mock_spectrum.size), y = mock_spectrum)

# Creating a blank algorithm to perform the analysis
analyser.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
                            version="v0", 
                            author="Pierre Bouvet", 
                            description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")

# Adding points corresponding to peaks to the algorithm
analyser.add_point(position_center_window=79, type_pnt="Anti-Stokes", window_width=5)
analyser.add_point(position_center_window=252, type_pnt="Stokes", window_width=5)
analyser.add_point(position_center_window=513, type_pnt="Anti-Stokes", window_width=5)
analyser.add_point(position_center_window=619, type_pnt="Stokes", window_width=5)
analyser.add_point(position_center_window=810, type_pnt="Anti-Stokes", window_width=5)
analyser.add_point(position_center_window=895, type_pnt="Stokes", window_width=5)

# Defining the FSR of the VIPA used
analyser.interpolate_elastic_inelastic(FSR = 30)

# Identifying the central peaks and recentering the spectrum to have them be symetric
analyser.add_point(position_center_window=33.7, type_pnt="Stokes", window_width=1)
analyser.add_point(position_center_window=43.8, type_pnt="Anti-Stokes", window_width=1)
analyser.center_x_axis(center_type = "Inelastic")

# # Plotting the results
plt.plot(analyser.x, analyser.y)
plt.xlabel("Frequency (GHz)")
plt.ylabel("PSD (a.u.)")
plt.show()
```
