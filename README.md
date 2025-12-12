# HDF5_BLS

**HDF5_BLS** is a project to unify and standardize the storage of Brillouin Light Scattering (BLS) data in a HDF5 files, and to develop unified tools to process these data. The projects consists of three packages:

- **HDF5_BLS**: A package to store BLS data in a single HDF5 file.
- **HDF5_BLS_analyse**: A package to analyse BLS data (extract power spectra) from raw data.
- **HDF5_BLS_treat**: A package to treat BLS data (process power spectra to obtain relevant quantities).

The library is thought to seemlessly integrate in existing Python workflows, to be minimally constrained, and to be as easy to use as possible. Additionally, the library is aimed at speeding up all the steps involved in BLS data processing, starting with the extraction of raw data from arbitrary sources.

## File format quickstart

### Library installation

To directly use the library, you can install the three packages: **HDF5_BLS**, **HDF5_BLS_analyse** and **HDF5_BLS_treat** directly from PyPI:

```bash
pip install HDF5_BLS
pip install HDF5_BLS_analyse
pip install HDF5_BLS_treat
```

To help in the development of the library, we recommend setting up a custom development environment, and installing the three packages in editable mode from your local repository. Please refer to [the tutorial](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) or [the documentation](https://hdf5-bls.readthedocs.io/en/latest/) for more information.

### Integration to workflow

Once the package is installed, you can use it in your Python scripts to store your data:

```python
import HDF5_BLS as bls

# Create a HDF5 file
wrp = bls.Wrapper(filepath = "path/to/file.h5")

###############################################################################
# Existing code to extract data from a file
###############################################################################
# Storing the data in the HDF5 file (for this example we use a random array)
data = np.random.random((50, 50, 512))
wrp.add_raw_data(data = data, parent_group = "Brillouin", name = "Raw data")

###############################################################################
# Existing code to convert the data to a PSD
###############################################################################
# Storing the Power Spectral Density in the HDF5 file together with the associated frequency array (for this example we use random arrays)
PSD = np.random.random((50, 50, 512))
frequency = np.arange(512)
wrp.add_PSD(data = PSD, parent_group = "Brillouin", name = "Power Spectral Density")
wrp.add_frequency(data = frequency, parent_group = "Brillouin", name = "Frequency")

###############################################################################
# Existing code to fit the PSD to extract shift and linewidth arrays
###############################################################################
# Storing the Power Spectral Density in the HDF5 file together with the associated frequency array (for this example we use random arrays)
shift = np.random.random((50, 50))
linewidth = np.random.random((50, 50))
wrp.add_treated_data(parent_group = "Brillouin", name_group = "Treat_0", shift = shift, linewidth = linewidth)
```

### Normalization

The file format does not impose any restriction on the way the data is stored. However, if you plan on sharing your data with other researchers, we recommend using the normalization guidelines set in [the tutorial](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) or on [the documentation](https://hdf5-bls.readthedocs.io/en/latest/). 

The guidelines for normlization affect:
- The way dataset are shaped
- The nomenclature of attributes

### Extracting the data from the HDF5 file

Independently of the way the data is stored, extracting data from the HDF5 file is done using the path of the dataset in the file in brackets:

```python
import HDF5_BLS as bls

# Open the file
wrp = bls.Wrapper(filepath = "path/to/file.h5")

# Extract the data
data = wrp["Brillouin/path/in/file/Raw data"]
```

## Analysis and treatment quickstart

To use the analysis and treatment tools, you need to install the two packages **HDF5_BLS_analyse** and **HDF5_BLS_treat**. Once installed, you can use them in your Python scripts to extract and treat your data. Both packages are based on a modular design, where the user can define new algorithms to be used in the analysis and treatment of the data. Using these packages gives a few benefits over codes written by the user:
- The algorithm is defined with unified functions
- The algorithms are automatically stored when run and can be either exported as standalone files or as a set of commands stored in the HDF5 file
- These algorithms can be used in the GUI

Additionally, the format supports the storage of custom scripts which are used to process the data, perform statistical analysis, generate figures etc. To know more about how to use this feature, please refer to [the tutorial](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) or [the documentation](https://hdf5-bls.readthedocs.io/en/latest/).

### Analysis example code

Here is an example of how to use the analysis package to extract a power spectrum from a raw data array:

```python
from HDF5_BLS_analyse import Analyse_VIPA
import numpy as np

# Initialising the Analyse_VIPA object on the mock spectrum
analyser = Analyse_VIPA(x = np.arange(mock_spectrum.size), y = mock_spectrum)

# Creating a blank algorithm to perform the analysis
analyser.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
                            version="v0", 
                            author="Pierre Bouvet", 
                            description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")

# Adding points corresponding to peaks to the algorithm
analyser.add_point(position_center_window=12, type_pnt="Elastic", window_width=5)
analyser.add_point(position_center_window=37, type_pnt="Anti-Stokes", window_width=5)
analyser.add_point(position_center_window=236, type_pnt="Stokes", window_width=5)
analyser.add_point(position_center_window=259, type_pnt="Elastic", window_width=5)
analyser.add_point(position_center_window=282, type_pnt="Anti-Stokes", window_width=5)
analyser.add_point(position_center_window=466, type_pnt="Stokes", window_width=5)
analyser.add_point(position_center_window=488, type_pnt="Elastic", window_width=5)
analyser.add_point(position_center_window=509, type_pnt="Anti-Stokes", window_width=5)

# Defining the FSR of the VIPA used
analyser.interpolate_elastic_inelastic(FSR = 60)

# Identifying the central peaks and recentering the spectrum to have them be symetric
analyser.add_point(position_center_window=57, type_pnt="Stokes", window_width=1)
analyser.add_point(position_center_window=68.5, type_pnt="Anti-Stokes", window_width=1)
analyser.center_x_axis(center_type = "Inelastic")

# Saving the algorithm to a standalone JSON file
analyser.silent_save_algorithm(filepath = "algorithms/Analysis/VIPA spectrometer/Test.json", save_parameters=True)

# Extracting the PSD and frequency axis from the analyser object
frequency = analyser.x
PSD = analyser.y
```

### Treatment example code

Here is an example of how to use the analysis package to extract a power spectrum from a raw data array:

```python
from HDF5_BLS_treat import Treat
import numpy as np

# Initialising the Treat object on the a doublet of frequency and PSD
treat = Treat(frequency = frequency, PSD = data)

# Creating a blank algorithm to perform the analysis
treat.silent_create_algorithm(algorithm_name="VIPA spectrum analyser", 
                        version="v0", 
                        author="Pierre Bouvet", 
                        description="This algorithm allows the user to recover a frequency axis basing ourselves on a single Brillouin spectrum obtained with a VIPA spectrometer. Considering that only one Brillouin Stokes and anti-Stokes doublet is visible on the spectrum, the user can select the peaks he sees, and then perform a quadratic interpolation to obtain the frequency axis. This interpolation is obtained either by entering a value for the Brillouin shift of the material or by entering the value of the Free Spectral Range (FSR) of the spectrometer. The user can finally recenter the spectrum either using the average between a Stokes and an anti-Stokes peak or by choosing an elastic peak as zero frequency.")

# Adding points corresponding to the central peaks to the algorithm so as to normalize the PSD
treat.add_point(position_center_window=-6, type_pnt="Anti-Stokes", window_width=5)
treat.add_point(position_center_window=6, type_pnt="Stokes", window_width=5)
treat.normalize_data(threshold_noise = 0.05)

# Adding the peaks to fit
treat.add_point(position_center_window=-6, type_pnt="Anti-Stokes", window_width=5)
treat.add_point(position_center_window=6, type_pnt="Stokes", window_width=5)

# Defining the model for fitting the peaks
treat.define_model(model="DHO", elastic_correction=False) 

# Estimating the linewidth from selected peaks
treat.estimate_width_inelastic_peaks(max_width_guess=5)

# Fitting all the selected inelastic peaks with multiple peaks fitting
treat.single_fit_all_inelastic(guess_offset=True, 
                                update_point_position=True, 
                                bound_shift=[[-7, -5], [5, 7]], 
                                bound_linewidth=[[0, 5], [0, 5]])

# Applying the algorithm to all the spectra (in the case where PSD is a 2D array)
treat.apply_algorithm_on_all()

# Combining the two fitted peaks together here weighing the result on the standard deviation of the shift
treat.combine_results_FSR(FSR = 60, keep_max_amplitude = False, amplitude_weight = False, shift_err_weight= True)

# Extracting the results
shift = treat.shift
linewidth = treat.linewidth
amplitude = treat.amplitude
BLT = treat.BLT
shift_var = treat.shift_var
linewidth_var = treat.linewidth_var
amplitude_var = treat.amplitude_var 
BLT_var = treat.BLT_var
```

## GUI

To faciliate the use of the package, we have interfaced it with a GUI also accessible in this repository. The GUI is now capable of:
- Creating HDF5 files following the structure of v1.0:
    - Structure the file in a hierarchical way
    - Import measure data (drag and drop functionality implemented)
    - Import attributes from a CSV or Excel spreadsheet file (drag and drop functionality implemented)
    - Modify parameters of data both by group and individually from the GUI
- Inspect existing HDF5 files and in particular, ones made with the HDF5_BLS package
- Export sub-HDF5 files from meta files
- Export Python or Matlab code to access individual datasets
- Analyse raw spectra obtained with a VIPA spectrometer

## Library 

### Documentation

You can access the documentation of the project at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) or on the dedicated ReadTheDocs page at [this link](https://hdf5-bls.readthedocs.io/en/latest/). Both documentations are identical (the tutorial PDF is generated from the ReadTheDocs documentation).

## Contributing

We are more than happy to receive contributions from the community! Please refer to [CONTRIBUTING.md](https://github.com/bio-brillouin/HDF5_BLS/blob/main/CONTRIBUTING.md) for more information.

To help you in creating your development environment, a dedicated section for developpers has been added both to [the tutorial](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) and [the documentation](https://hdf5-bls.readthedocs.io/en/latest/).

Contributions from industry are also welcome! The goal of this project being to create a unified and standardized way to store and process Brillouin light scattering (BLS) data, we recommend you to contact the main developer of the project: [Pierre Bouvet](pierre.bouvet@meduniwien.ac.at) for any specific features you would want to add to the project in order to protect your proprietary data or treatment, so we can work together in making something that works for you while keeping the compatibility with the existing tools and the possibility for researchers to apply the advances to your instruments as we develp them.

## License

The project is licensed under the [GNU-GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

## What's new with respect to previous versions?

### v1.0.3
- Restructuring of the documentation and GitHub repository

### v1.0.2
- Bug fix in the export of groups as independent HDF5 files
- Ability to export to Brim files

### v1.0.1
- New "add_other" method to add datasets from non-specified type to the wrapper
- Working with temporary files: Instead of creating a temporary H5 file in the directory of the library, the file is now created in a temporary directory of the OS. 
