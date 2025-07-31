# HDF5_BLS

**HDF5_BLS** is a Python library for storing Brillouin Light Scattering (BLS) data into a standardized HDF5 file format. The library provides functions to open raw data files, define and import abscissa, add metadata, and save the organized data in HDF5 files.
The library is currently compatible with the following file formats:
- "*.dat" files: dat spectra obtained with:
    - [GHOST](https://tablestable.com/en/downloads/) software 
    - Time Domain measures (format defined by Sal La Cavera)
- "*.npy" files: a numpy file
- "*.sif" files: image files obtained with [Andor](https://andor.oxinst.com) cameras
- All image files supported by the Pillow library (see [this link](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#write-only-formats))

## Quickstart

### Library installation

You can install **HDF5_BLS** directly from PyPI:

```bash
pip install HDF5_BLS
```
Please refer to [the tutorial](https://github.com/bio-brillouin/HDF5_BLS/blob/v-1.0.0/guides/Tutorial/Tutorial.pdf) for more information.


### Integration to workflow

Once the package is installed, you can use it in your Python scripts as follows:

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

### Extracting the data from the HDF5 file

Once the data is stored in the HDF5 file, you can extract it as follows:

```python
import HDF5_BLS as bls

# Open the file
wrp = bls.Wrapper(filepath = "path/to/file.h5")

# Extract the data
data = wrp["Brillouin/path/in/file/Raw data"]
```

## GUI

To faciliate the use of the package, we have interfaced it with a GUI also accessible in this repository. The GUI is now capable of:
- Creating HDF5 files following the structure of v1.0.0:
    - Structure the file in a hierarchical way
    - Import measure data (drag and drop functionality implemented)
    - Import attributes from a CSV or Excel spreadsheet file (drag and drop functionality implemented)
    - Modify parameters of data both by group and individually from the GUI
- Inspect existing HDF5 files and in particular, ones made with the HDF5_BLS package
- Export sub-HDF5 files from meta files
- Export Python or Matlab code to access individual datasets
- Visualize 2D arrays as images
- Analyze raw spectra obtained with a VIPA spectrometer
- Develop new algorithms for the analysis of raw spectra

## Library 

### Documentation

You can access the documentation of the project at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/v-1.0.0/guides/Tutorial/Tutorial.pdf).
Additionnally, a ReadTheDocs documentation for the library is accessible at [this link](https://hdf5-bls.readthedocs.io/en/latest/).

## Contributing

A Developper Guide is accessible at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/v-1.0.0/guides/Tutorial/Tutorial.pdf). This guide is meant to be used by researchers who want to expand the project to their own devices while keeping the compatibility with all the existing functionalities. 

For changes that might affect the compatibility of the project with existing devices, please open an issue first to discuss what you would like to change. For more information, please refer to [CONTRIBUTING.md](https://github.com/bio-brillouin/HDF5_BLS/blob/main/CONTRIBUTING.md).

## License

[GNU-GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)