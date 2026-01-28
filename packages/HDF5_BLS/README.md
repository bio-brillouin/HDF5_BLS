# The HDF5_BLS package

This package is a part of the [HDF5_BLS](https://github.com/bio-brillouin/HDF5_BLS) project. It's purpose is to unify the storage of BLS-related data to a HDF5 file.

## Installation

To install the package, you can use pip:

```bash
pip install HDF5_BLS
```

To install the package from source for local development, please refer to the [documentation](https://hdf5-bls.readthedocs.io/en/latest/).

## Documentation

You can access the documentation of the project at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) or on the dedicated ReadTheDocs page at [this link](https://hdf5-bls.readthedocs.io/en/latest/).

## Example of usage

```python
from HDF5_BLS import Wrapper, NormalizedAttributes

# Create a HDF5 file
wrp = Wrapper(filepath = "path/to/file.h5")

# Use normalized attributes
NormalizedAttributes.to_excel("my_attributes.xlsx") # Export standardized list
attrs = NormalizedAttributes.get_attributes_by_group("MEASURE")

# Add a normalized attribute to the file
wrp.add_attributes({"MEASURE.Sample": "Water"}, parent_group="Brillouin/Measure")
```

###############################################################################
# Existing code to extract data from a file
###############################################################################
# ...
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
