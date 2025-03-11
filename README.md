# HDF5_BLS

**HDF5_BLS** is a Python library for handling Brillouin Light Scattering (BLS) data and converting it into a standardized HDF5 format. The library provides functions to open raw data files, define and import abscissa, add metadata, and save the organized data in HDF5 files.
The library is currently compatible with the following file formats:
- "*.dat" files: spectra returned by the GHOST software or obtained using Time Domain measurements
- "*.tif" files: an image format that can be used to export 2D detector images.
- "*.npy" files: an arbitrary numpy array
- "*.sif" files: image files obtained with Andor cameras

## GUI

The package comes with a graphical user interface (GUI) that allows users to easily open, edit, and save data. Please refer to the [tutorial](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/Tutorial/Tutorial.pdf) for more information.

## Library 

### Library installation

You can install **HDF5_BLS** directly from PyPI:

```bash
pip install HDF5_BLS
```

### Documentation

A full documentation for the library is accessible at [this link](https://hdf5-bls.readthedocs.io/en/latest/).

## Contributing

A Developper Guide is accessible at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/main/guides/DeveloperGuide/ModuleDevelopperGuide.pdf). This guide is meant to be used by researchers who want to expand the project to their own devices while keeping the compatibility with all the existing functionalities. 

For changes that might affect the compatibility of the project with existing devices, please open an issue first to discuss what you would like to change. For more information, please refer to [CONTRIBUTING.md](https://github.com/bio-brillouin/HDF5_BLS/blob/main/CONTRIBUTING.md).

## License

[GNU-GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)