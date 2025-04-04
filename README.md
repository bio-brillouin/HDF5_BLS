# HDF5_BLS

**HDF5_BLS** is a Python library for handling Brillouin Light Scattering (BLS) data and converting it into a standardized HDF5 format. The library provides functions to open raw data files, define and import abscissa, add metadata, and save the organized data in HDF5 files.
The library is currently compatible with the following file formats:
- "*.dat" files: dat spectra obtained with:
    - [GHOST](https://tablestable.com/en/downloads/) software 
    - Time Domain measures (format defined by Sal La Cavera)
- "*.npy" files: a numpy file
- "*.sif" files: image files obtained with [Andor](https://andor.oxinst.com) cameras
- All image files supported by the Pillow library (see [this link](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#write-only-formats))

## GUI

The GUI is not yet compatible with v1.0.0.

## Library 

### Library installation

You can install **HDF5_BLS** directly from PyPI:

```bash
pip install HDF5_BLS
```
Please refer to [the tutorial](https://github.com/bio-brillouin/HDF5_BLS/blob/v-1.0.0/guides/Tutorial/Tutorial.pdf) for more information.

### Documentation

You can access the documentation of the project at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/v-1.0.0/guides/Tutorial/Tutorial.pdf).
Additionnally, a ReadTheDocs documentation for the library is accessible at [this link](https://hdf5-bls.readthedocs.io/en/latest/).

## Contributing

A Developper Guide is accessible at [this link](https://github.com/bio-brillouin/HDF5_BLS/blob/v-1.0.0/guides/Tutorial/Tutorial.pdf). This guide is meant to be used by researchers who want to expand the project to their own devices while keeping the compatibility with all the existing functionalities. 

For changes that might affect the compatibility of the project with existing devices, please open an issue first to discuss what you would like to change. For more information, please refer to [CONTRIBUTING.md](https://github.com/bio-brillouin/HDF5_BLS/blob/main/CONTRIBUTING.md).

## License

[GNU-GPL v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)