# HDF5_BLS

**HDF5_BLS** is a Python library for handling Brillouin Light Scattering (BLS) data and converting it into a standardized HDF5 format. The library provides functions to open raw data files, define and import abscissa, add metadata, and save the organized data in HDF5 files.
The library is currently compatible with the following file formats:
- "*.DAT" files: spectra returned by the GHOST software
- "*.TIF" files: an image format that can be used to export 2D detector images.

## Features

- Load raw BLS data from `.DAT` and `.TIF` files
- Define or import abscissa values
- Add calibration and impulse response curves to the HDF5 file
- Attach metadata attributes for experimental setup and measurement details
- Save data and metadata to an HDF5 file for standardized storage

## Installation

You can install **HDF5_BLS** directly from PyPI:

```bash
pip install HDF5_BLS
```

## Example

This example demonstrates a full workflow with HDF5_BLS, including loading data from a .DAT file, defining the abscissa, adding metadata, and saving it to an HDF5 file.

```python
from HDF5_BLS import HDF5_BLS

# Initialize the HDF5_BLS object
bls = HDF5_BLS()

# Open raw data from a .DAT file and store it in the object
bls.open_data("example.DAT")

# Define an abscissa for the data
bls.define_abscissa(min_val=0, max_val=100, nb_samples=1000)

# Add metadata attributes describing the measurement and spectrometer settings
bls.properties_data(
    MEASURE_Sample="Water",
    MEASURE_Date="2024-11-06",
    MEASURE_Exposure=10,                  # in seconds
    MEASURE_Dimension=3,
    SPECTROMETER_Type="TFP",
    SPECTROMETER_Model="JRS-TFP2",
    SPECTROMETER_Wavelength=532.0,          # in nm
    SPECTROMETER_Illumination_Type="CW",
    SPECTROMETER_Spectral_Resolution=15.0,  # in MHz
)

# Load and add a calibration curve from a .DAT file (optional)
bls.open_calibration("calibration_curve.dat")

# Load and add an impulse response curve (optional)
bls.open_IR("impulse_response.dat")

# Save the data, abscissa, and metadata attributes to an HDF5 file
bls.save_hdf5_as("output_data.h5")
```

A full example where a treatment is implemented on a water spectrum is presented in the test directory.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)