# HDF5_BLS

**HDF5_BLS** is a Python library for handling Brillouin Light Scattering (BLS) data and converting it into a standardized HDF5 format. The library provides functions to open raw data files, define and import abscissa, add metadata, and save the organized data in HDF5 files.
The library is currently compatible with the following file formats:
- "*.DAT" files: spectra returned by the GHOST software
- "*.TIFF" files: an image format that can be used to export 2D detector images.

## Features

- Load raw BLS data from `.DAT` and `.TIFF` files
- Define or import abscissa values
- Add calibration and impulse response curves to the HDF5 file
- Attach metadata attributes for experimental setup and measurement details
- Save data and metadata to an HDF5 file for standardized storage

## Installation

You can install **HDF5_BLS** directly from PyPI:

```bash
pip install HDF5_BLS