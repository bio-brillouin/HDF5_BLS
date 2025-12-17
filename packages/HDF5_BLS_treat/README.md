# The HDF5_BLS_treat package

This package is a part of the [HDF5_BLS](https://github.com/bio-brillouin/HDF5_BLS) project. It's purpose is to unify the extraction of relevant information from power spectra data.

## Installation

To install the package, you can use pip:

```bash
pip install HDF5_BLS_treat
```

To install the package from source for local development, please refer to the [documentation](https://hdf5-bls.readthedocs.io/en/latest/).

## Documentation

You can access the documentation of the project at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) or on the dedicated ReadTheDocs page at [this link](https://hdf5-bls.readthedocs.io/en/latest/).

## Example of usage

```python
from HDF5_BLS_treat import Treat, Models
import numpy as np
import sys

def progress(current, total):
    """
    Function to display the progress of the treatment.
    """
    percent = (current / total) * 100
    sys.stdout.write(f"\rProgress: sample {current} of {total} - {percent:.2f}% treated")
    sys.stdout.flush()

# We first recover the model we are going to use to simulate the data
models = Models()
models = models.models
lorentzian = models["DHO"]

# We then create a frequency axis and a PSD based on the model
frequency = np.linspace(-10,10,512)
psd = lorentzian(frequency, 0, 1, -5, 1) + lorentzian(frequency, 0, 1, 5, 1) + 0.1 * np.random.normal(size = frequency.shape)

# We set the list parameters for the analysis
points = [-5, 5] # An initial guess for the center of the peak
windows_find = [3, 3] # The size of the windows around the peaks given to refine their position
windows_fit = [[3, 1.5], [1.5, 3]] # The windows around the peaks to fit them
point_type = ["Anti-Stokes", "Stokes"] # The nature of the peaks to fit
max_width_guess = 2 # The maximal estimation allowed for the linewidth before the fitting
bound_shift = [[-7, -3], [3, 7]] # The bounds for the fitting of the shift
bound_linewidth = [[0, 5], [0, 5]] # The bounds for the fitting of the linewidth

# Initialising the Treat object on the a doublet of frequency and PSD
treat = Treat(frequency = frequency, PSD = psd)

# Setting the progress callback (optional, this allows us to display the progress of the treatment on large datasets)
treat._progress_callback = progress

# Adding the points to normalize the data
for point, window in zip(points, windows_find):
    treat.add_point(position_center_window = point, type_pnt = "Other", window_width = window)
treat.normalize_data(threshold_noise = 0.05)

# Adding the peaks to fit
for point, window, tpe in zip(points, windows_fit, point_type):
    treat.add_point(position_center_window = point, type_pnt = tpe, window_width = window)

# Defining the model for fitting the peaks - you can choose between the models defined in the Models class
treat.define_model(model = "Lorentzian", elastic_correction = True)

# Estimating the linewidth from selected peaks
treat.estimate_width_inelastic_peaks(max_width_guess = max_width_guess)

# Fitting all the selected inelastic peaks with multiple peaks fitting
treat.single_fit_all_inelastic(guess_offset = True, 
                                update_point_position = True, 
                                bound_shift = bound_shift, 
                                bound_linewidth = bound_linewidth)

# Applying the algorithm to all the spectra (in the case where PSD is a 2D array)
treat.apply_algorithm_on_all()

# Combining the two fitted peaks together here weighing the result on the standard deviation of the shift
treat.combine_results_FSR(FSR = 60, keep_max_amplitude = False, amplitude_weight = False, shift_err_weight= True)

# Printing the results
print("\nFinal results:")
print(f"Shfit: {treat.shift}")
print(f"Linewidth: {treat.linewidth}")
print(f"Amplitude: {treat.amplitude}")
```
