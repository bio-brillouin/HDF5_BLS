# HDF5_BLS

**HDF5_BLS** is a Python library for handling Brillouin Light Scattering (BLS) data and converting it into a standardized HDF5 format. The library provides functions to open raw data files, define and import abscissa, add metadata, and save the organized data in HDF5 files.
The library is currently compatible with the following file formats:
- "*.dat" files: spectra returned by the GHOST software
- "*.tif" files: an image format that can be used to export 2D detector images.
- "*.npy" files: an arbitrary numpy array
- "*.sif" files: image files obtained with Andor cameras

## Installation

You can install **HDF5_BLS** directly from PyPI:

```bash
pip install HDF5_BLS
```

## Documentation

A full documentation is accessible at [this link](https://hdf5-bls.readthedocs.io/en/latest/).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. For more information, please refer to [CONTRIBUTING.md](https://github.com/PierreBouvet/HDF5_BLS_v1/blob/main/CONTRIBUTING.md).

## License

[GNU-GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)